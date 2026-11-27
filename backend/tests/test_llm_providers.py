import logging
from types import SimpleNamespace

from google.genai import errors as genai_errors
import pytest

from app.core.config import Settings
from app.providers.llm import (
    DemoLLMProvider,
    GeminiLLMProvider,
    LLMProviderError,
    get_llm_provider,
)
from app.schemas.candidate_profile import StructuredCandidateProfile


def test_demo_provider_returns_deterministic_demo_labelled_output() -> None:
    provider = DemoLLMProvider()
    resume_text = "[Page 1]\nPriya Nair\nML Systems Engineer\nBuilt Python, FastAPI, and PyTorch pipelines."

    result1 = provider.extract_candidate_profile(resume_text)
    result2 = provider.extract_candidate_profile(resume_text)

    assert result1.provider_name == "demo"
    assert result1.data_origin == "demo"
    assert result1.profile.basic_info.full_name == "Priya Nair"
    assert result1.profile == result2.profile
    assert any("demo" in w.lower() for w in result1.warnings)
    skill_names = {s.name for s in result1.profile.skills}
    assert {"Python", "FastAPI", "PyTorch"}.issubset(skill_names)


def test_provider_selection_from_settings() -> None:
    demo_settings = Settings(ai_provider="demo", gemini_api_key=None)
    assert isinstance(get_llm_provider(demo_settings), DemoLLMProvider)

    forced_demo = Settings(ai_provider="gemini", demo_mode=True, gemini_api_key=None)
    assert isinstance(get_llm_provider(forced_demo), DemoLLMProvider)

    gemini_settings = Settings(ai_provider="gemini", demo_mode=False, gemini_api_key="test-secret-key")
    provider = get_llm_provider(gemini_settings)
    assert isinstance(provider, GeminiLLMProvider)
    assert "test-secret-key" not in repr(gemini_settings)


def test_gemini_provider_missing_api_key_handled() -> None:
    with pytest.raises(LLMProviderError) as exc_info:
        GeminiLLMProvider(api_key=None)
    assert exc_info.value.code == "GEMINI_API_KEY_MISSING"
    assert exc_info.value.status_code == 503


def test_gemini_provider_timeout_handled_without_leaking_key(caplog: pytest.LogCaptureFixture) -> None:
    secret_key = "AIzaSy-SUPER-SECRET-KEY-12345"

    class TimeoutModels:
        def generate_content(self, **_kwargs):
            raise TimeoutError(f"request timed out for key={secret_key}")

    fake_client = SimpleNamespace(models=TimeoutModels())
    provider = GeminiLLMProvider(api_key=secret_key, max_retries=1, client=fake_client)

    with caplog.at_level(logging.INFO):
        with pytest.raises(LLMProviderError) as exc_info:
            provider.extract_candidate_profile("[Page 1]\nAlex Mercer\nPython Engineer")

    assert exc_info.value.code == "LLM_TIMEOUT"
    assert exc_info.value.status_code == 504
    assert secret_key not in exc_info.value.detail
    assert secret_key not in caplog.text


def test_gemini_provider_rate_limit_handled() -> None:
    class RateLimitModels:
        def generate_content(self, **_kwargs):
            raise genai_errors.APIError(code=429, response_json={"error": {"message": "Quota exceeded"}})

    fake_client = SimpleNamespace(models=RateLimitModels())
    provider = GeminiLLMProvider(api_key="fake-key", max_retries=1, client=fake_client)

    with pytest.raises(LLMProviderError) as exc_info:
        provider.extract_candidate_profile("[Page 1]\nAlex Mercer\nPython Engineer")

    assert exc_info.value.code == "LLM_RATE_LIMITED"
    assert exc_info.value.status_code == 429


def test_gemini_provider_invalid_json_output_handled() -> None:
    class BadOutputModels:
        def generate_content(self, **_kwargs):
            return SimpleNamespace(text="{malformed-json")

    fake_client = SimpleNamespace(models=BadOutputModels())
    provider = GeminiLLMProvider(api_key="fake-key", client=fake_client)

    with pytest.raises(LLMProviderError) as exc_info:
        provider.extract_candidate_profile("[Page 1]\nAlex Mercer\nPython Engineer", StructuredCandidateProfile)

    assert exc_info.value.code == "LLM_INVALID_OUTPUT"
