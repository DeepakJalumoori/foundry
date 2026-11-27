from pathlib import Path

import pymupdf
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate_profile import CandidateProfile
from app.providers.llm import (
    DemoLLMProvider,
    LLMProfileExtractionResult,
    LLMProvider,
    LLMProviderError,
)
from app.repositories.profile_repository import ProfileRepository
from app.repositories.run_repository import RunRepository
from app.schemas.candidate_profile import SkillItem, StructuredCandidateProfile
from app.services.candidate_profile_service import process_candidate_profile_for_run
from app.services.resume_extractor import ResumeExtractionError


def _write_pdf(path: Path, text: str | None) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_service_successful_pdf_extraction_and_profile_persistence(
    db_session: Session,
    test_settings: Settings,
) -> None:
    storage_key = "resume_success.pdf"
    _write_pdf(
        test_settings.upload_dir / storage_key,
        "Samira Patel\nBackend Engineer\nExperienced in Python, FastAPI, and SQLite.",
    )
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="samira.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=512,
        resume_storage_key=storage_key,
    )

    result = process_candidate_profile_for_run(
        db_session,
        test_settings,
        run.id,
        llm_provider=DemoLLMProvider(),
    )

    assert result.status == "completed"
    assert result.profile_id is not None
    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.started_at <= result.completed_at

    db_session.refresh(run)
    assert run.status == "completed"
    assert run.error_code is None

    profile = ProfileRepository.get_by_candidate_id(db_session, run.candidate_id)
    assert profile is not None
    assert profile.data_origin == "demo"
    assert profile.provider_name == "demo"
    assert profile.profile_data is not None
    assert profile.profile_data["basic_info"]["full_name"] == "Samira Patel"


def test_service_image_only_pdf_marks_manual_review_and_failed_run(
    db_session: Session,
    test_settings: Settings,
) -> None:
    storage_key = "scanned_resume.pdf"
    _write_pdf(test_settings.upload_dir / storage_key, None)
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="scanned.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key=storage_key,
    )

    result = process_candidate_profile_for_run(
        db_session,
        test_settings,
        run.id,
        llm_provider=DemoLLMProvider(),
    )

    assert result.status == "failed"
    assert result.extraction_status == "requires_manual_review"
    assert result.error is not None
    assert result.error.code == "RESUME_REQUIRES_OCR_OR_REVIEW"

    profile = ProfileRepository.get_by_candidate_id(db_session, run.candidate_id)
    assert profile is not None
    assert profile.profile_data is None
    assert profile.extraction_status == "requires_manual_review"


def test_service_provider_failure_updates_run_failed_without_partial_profile(
    db_session: Session,
    test_settings: Settings,
) -> None:
    storage_key = "provider_fail.pdf"
    _write_pdf(test_settings.upload_dir / storage_key, "Alex Rivera\nSoftware Engineer\nPython")
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="alex.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key=storage_key,
    )

    class FailingProvider(LLMProvider):
        def extract_candidate_profile(self, resume_text, schema=StructuredCandidateProfile):
            raise LLMProviderError("LLM_TIMEOUT", "Provider timed out.", status_code=504)

    with pytest.raises(LLMProviderError):
        process_candidate_profile_for_run(db_session, test_settings, run.id, llm_provider=FailingProvider())

    db_session.refresh(run)
    assert run.status == "failed"
    assert run.error_code == "LLM_TIMEOUT"
    assert run.started_at is not None
    assert run.completed_at is not None
    assert db_session.query(CandidateProfile).count() == 0


def test_service_evidence_validation_flags_unsupported_claims(
    db_session: Session,
    test_settings: Settings,
) -> None:
    storage_key = "ungrounded.pdf"
    _write_pdf(test_settings.upload_dir / storage_key, "Maya Lin\nFull Stack Developer\nTypeScript and React")
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="maya.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key=storage_key,
    )

    class HallucinatingProvider(LLMProvider):
        def extract_candidate_profile(self, resume_text, schema=StructuredCandidateProfile):
            return LLMProfileExtractionResult(
                profile=StructuredCandidateProfile(
                    skills=[
                        SkillItem(
                            name="Kubernetes",
                            category="cloud_infrastructure",
                            evidence_snippet="Led Kubernetes platform migration",
                            page_number=1,
                        )
                    ]
                ),
                provider_name="fake",
                model_name="fake-v1",
                data_origin="real",
            )

    result = process_candidate_profile_for_run(
        db_session,
        test_settings,
        run.id,
        llm_provider=HallucinatingProvider(),
    )
    assert result.extraction_status == "requires_manual_review"
    assert any("requires review" in w for w in result.warnings)


def test_service_repeat_processing_is_idempotent(
    db_session: Session,
    test_settings: Settings,
) -> None:
    storage_key = "idempotent.pdf"
    _write_pdf(test_settings.upload_dir / storage_key, "Devon Brooks\nAI Engineer\nPython and PyTorch")
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="devon.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key=storage_key,
    )

    call_count = 0

    class CountingProvider(LLMProvider):
        def extract_candidate_profile(self, resume_text, schema=StructuredCandidateProfile):
            nonlocal call_count
            call_count += 1
            return DemoLLMProvider().extract_candidate_profile(resume_text, schema)

    first = process_candidate_profile_for_run(db_session, test_settings, run.id, llm_provider=CountingProvider())
    second = process_candidate_profile_for_run(db_session, test_settings, run.id, llm_provider=CountingProvider())

    assert call_count == 1
    assert first.profile_id == second.profile_id
    assert db_session.query(CandidateProfile).count() == 1


def test_service_db_persistence_failure_rolls_back_and_marks_run_failed(
    db_session: Session,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_key = "db_fail.pdf"
    _write_pdf(test_settings.upload_dir / storage_key, "Chris Cole\nEngineer\nPython")
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="chris.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key=storage_key,
    )

    def _boom(*_args, **_kwargs):
        raise SQLAlchemyError("simulated db write error")

    monkeypatch.setattr(ProfileRepository, "upsert_profile", _boom)

    with pytest.raises(SQLAlchemyError):
        process_candidate_profile_for_run(db_session, test_settings, run.id, llm_provider=DemoLLMProvider())

    db_session.refresh(run)
    assert run.status == "failed"
    assert run.error_code == "PROFILE_PERSISTENCE_ERROR"
    assert db_session.query(CandidateProfile).count() == 0


def test_service_missing_file_marks_run_failed(
    db_session: Session,
    test_settings: Settings,
) -> None:
    run = RunRepository.create_resume_candidate_and_run(
        db_session,
        resume_filename="missing.pdf",
        resume_content_type="application/pdf",
        resume_size_bytes=256,
        resume_storage_key="missing.pdf",
    )

    with pytest.raises(ResumeExtractionError) as exc_info:
        process_candidate_profile_for_run(db_session, test_settings, run.id, llm_provider=DemoLLMProvider())

    assert exc_info.value.code == "RESUME_FILE_MISSING"
    db_session.refresh(run)
    assert run.status == "failed"
    assert run.error_code == "RESUME_FILE_MISSING"
