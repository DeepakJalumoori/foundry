from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
import re
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.candidate_profile import (
    AdditionalInfo,
    BasicInfo,
    DataOrigin,
    EvidenceItem,
    SkillCategory,
    SkillItem,
    StructuredCandidateProfile,
)

logger = logging.getLogger(__name__)

_EXTRACTION_SYSTEM_PROMPT = """You are a strict, evidence-first resume parser for Foundry.
Extract structured candidate information ONLY from the provided resume text.

Rules:
1. Do NOT invent or guess missing values. Use null or empty lists if not present.
2. Do NOT infer skill proficiency unless explicitly stated (e.g. "Expert in Python").
3. Do NOT fabricate employment dates, CGPA, years of experience, or project outcomes.
4. Preserve page numbers from the [Page N] markers and include verbatim evidence snippets from the resume text.
5. Distinguish explicitly stated facts ("explicitly_stated") from derived fields ("inferred").
"""

_KNOWN_DEMO_SKILLS: tuple[tuple[str, SkillCategory], ...] = (
    ("Python", "programming_languages"),
    ("TypeScript", "programming_languages"),
    ("JavaScript", "programming_languages"),
    ("Go", "programming_languages"),
    ("SQL", "databases"),
    ("PostgreSQL", "databases"),
    ("SQLite", "databases"),
    ("FastAPI", "frameworks"),
    ("React", "frameworks"),
    ("Next.js", "frameworks"),
    ("PyTorch", "ai_ml"),
    ("LangGraph", "ai_ml"),
    ("Docker", "cloud_infrastructure"),
    ("AWS", "cloud_infrastructure"),
    ("Git", "tools_platforms"),
)


class LLMProviderError(Exception):
    """Safe domain error raised when an LLM provider fails."""

    def __init__(self, code: str, detail: str, status_code: int = 502) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class LLMProfileExtractionResult:
    """Result returned by an LLMProvider after structured profile extraction."""

    profile: StructuredCandidateProfile
    provider_name: str
    model_name: str | None
    data_origin: DataOrigin
    warnings: list[str] = field(default_factory=list)


class LLMProvider(ABC):
    """Abstract interface for candidate profile extraction providers."""

    @abstractmethod
    def extract_candidate_profile(
        self,
        resume_text: str,
        schema: type[StructuredCandidateProfile] = StructuredCandidateProfile,
    ) -> LLMProfileExtractionResult:
        """Extract a structured candidate profile from normalized resume text."""


class DemoLLMProvider(LLMProvider):
    """Deterministic provider for tests and local development without an API key."""

    provider_name = "demo"
    model_name = "demo-deterministic-v1"

    def extract_candidate_profile(
        self,
        resume_text: str,
        schema: type[StructuredCandidateProfile] = StructuredCandidateProfile,
    ) -> LLMProfileExtractionResult:
        if not resume_text or not resume_text.strip():
            raise LLMProviderError(
                "EMPTY_RESUME_TEXT",
                "Cannot extract a candidate profile from empty resume text.",
                status_code=422,
            )

        page_1_lines = self._extract_page_lines(resume_text, page_number=1)
        full_name = page_1_lines[0] if page_1_lines else "Demo Candidate"
        headline = page_1_lines[1] if len(page_1_lines) > 1 else "Software Engineer (Demo)"

        skills: list[SkillItem] = []
        for skill_name, category in _KNOWN_DEMO_SKILLS:
            pattern = re.compile(rf"\b{re.escape(skill_name)}\b", re.IGNORECASE)
            match = pattern.search(resume_text)
            if match:
                page_num = self._find_page_for_offset(resume_text, match.start())
                snippet = self._extract_line_at_offset(resume_text, match.start())
                skills.append(
                    SkillItem(
                        name=skill_name,
                        category=category,
                        proficiency=None,
                        evidence_snippet=snippet,
                        page_number=page_num,
                        evidence_status="explicitly_stated",
                    )
                )

        evidence: list[EvidenceItem] = []
        if page_1_lines:
            evidence.append(
                EvidenceItem(
                    claim=f"Candidate name: {full_name}",
                    snippet=page_1_lines[0],
                    page_number=1,
                    status="explicitly_stated",
                )
            )

        profile = schema.model_validate(
            {
                "basic_info": BasicInfo(
                    full_name=full_name,
                    headline=headline,
                    evidence=evidence,
                ),
                "skills": skills,
                "work_experience": [],
                "education": [],
                "projects": [],
                "certifications_and_achievements": [],
                "additional_info": AdditionalInfo(
                    summary="Simulated demo extraction generated without a live LLM.",
                ),
                "evidence": evidence,
            }
        )

        return LLMProfileExtractionResult(
            profile=profile,
            provider_name=self.provider_name,
            model_name=self.model_name,
            data_origin="demo",
            warnings=[
                "Profile generated by DemoLLMProvider (simulated demo mode); "
                "not extracted by a live LLM."
            ],
        )

    @staticmethod
    def _extract_page_lines(resume_text: str, page_number: int) -> list[str]:
        marker = f"[Page {page_number}]"
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        filtered = [line for line in lines if not re.fullmatch(r"\[Page \d+\]", line)]
        if marker in resume_text:
            return filtered
        return filtered

    @staticmethod
    def _find_page_for_offset(text: str, offset: int) -> int:
        markers = list(re.finditer(r"\[Page (\d+)\]", text[: offset + 1]))
        if not markers:
            return 1
        return int(markers[-1].group(1))

    @staticmethod
    def _extract_line_at_offset(text: str, offset: int) -> str:
        start = text.rfind("\n", 0, offset) + 1
        end = text.find("\n", offset)
        if end == -1:
            end = len(text)
        return text[start:end].strip()[:240]


class GeminiLLMProvider(LLMProvider):
    """Gemini-backed structured candidate profile extraction provider."""

    provider_name = "gemini"

    def __init__(
        self,
        *,
        api_key: str | None,
        model_name: str = "gemini-2.5-flash",
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        client: Any | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise LLMProviderError(
                "GEMINI_API_KEY_MISSING",
                "Gemini API key is not configured.",
                status_code=503,
            )
        self._api_key = api_key.strip()
        self.model_name = model_name
        self.timeout_seconds = max(1.0, timeout_seconds)
        self.max_retries = max(0, min(max_retries, 2))
        self._client = client

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        return genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
        )

    def extract_candidate_profile(
        self,
        resume_text: str,
        schema: type[StructuredCandidateProfile] = StructuredCandidateProfile,
    ) -> LLMProfileExtractionResult:
        if not resume_text or not resume_text.strip():
            raise LLMProviderError(
                "EMPTY_RESUME_TEXT",
                "Cannot extract a candidate profile from empty resume text.",
                status_code=422,
            )

        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=_EXTRACTION_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.1,
        )

        logger.info(
            "Requesting Gemini structured profile extraction (model=%s, text_length=%d)",
            self.model_name,
            len(resume_text),
        )

        last_error: LLMProviderError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=resume_text,
                    config=config,
                )
                raw_text = getattr(response, "text", None)
                if not raw_text or not isinstance(raw_text, str):
                    raise LLMProviderError(
                        "LLM_INVALID_OUTPUT",
                        "LLM provider returned an empty or non-text response.",
                    )

                try:
                    profile = schema.model_validate_json(raw_text)
                except ValidationError as exc:
                    raise LLMProviderError(
                        "LLM_INVALID_OUTPUT",
                        "LLM output failed structured candidate profile validation.",
                    ) from exc

                return LLMProfileExtractionResult(
                    profile=profile,
                    provider_name=self.provider_name,
                    model_name=self.model_name,
                    data_origin="real",
                    warnings=[],
                )
            except LLMProviderError as exc:
                if exc.code == "LLM_INVALID_OUTPUT":
                    raise
                last_error = exc
            except TimeoutError as exc:
                last_error = LLMProviderError(
                    "LLM_TIMEOUT",
                    "LLM provider request timed out.",
                    status_code=504,
                )
                logger.warning("Gemini extraction timed out on attempt %d", attempt + 1)
                if attempt >= self.max_retries:
                    raise last_error from exc
            except genai_errors.APIError as exc:
                status = getattr(exc, "code", None)
                if status == 429:
                    last_error = LLMProviderError(
                        "LLM_RATE_LIMITED",
                        "LLM provider rate limit exceeded. Please try again later.",
                        status_code=429,
                    )
                    logger.warning("Gemini rate limit hit on attempt %d", attempt + 1)
                    if attempt >= self.max_retries:
                        raise last_error from exc
                else:
                    logger.warning("Gemini API error (status=%s)", status)
                    raise LLMProviderError(
                        "LLM_PROVIDER_ERROR",
                        "LLM provider returned an upstream API error.",
                        status_code=502,
                    ) from exc
            except Exception as exc:
                logger.warning("Unexpected Gemini provider failure (%s)", type(exc).__name__)
                raise LLMProviderError(
                    "LLM_PROVIDER_ERROR",
                    "LLM provider request failed due to a network or client error.",
                    status_code=502,
                ) from exc

        assert last_error is not None
        raise last_error


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Resolve the configured LLMProvider from application settings."""
    if settings.demo_mode or settings.ai_provider == "demo":
        return DemoLLMProvider()

    if settings.ai_provider == "gemini":
        return GeminiLLMProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    raise LLMProviderError(
        "UNSUPPORTED_LLM_PROVIDER",
        "Configured AI provider is not supported.",
        status_code=500,
    )
