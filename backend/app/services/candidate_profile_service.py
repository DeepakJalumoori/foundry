import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate_profile import CandidateProfile
from app.providers.llm import LLMProvider, LLMProviderError, get_llm_provider
from app.repositories.profile_repository import ProfileRepository
from app.repositories.run_repository import RunRepository
from app.schemas.candidate_profile import (
    CandidateProfileResponse,
    ProcessRunResponse,
    StructuredCandidateProfile,
)
from app.schemas.run import RunErrorResponse
from app.services.profile_validator import validate_and_ground_profile
from app.services.resume_extractor import ResumeExtractionError, extract_resume_text
from app.services.run_service import RunNotFoundError

logger = logging.getLogger(__name__)


class CandidateNotFoundError(Exception):
    """Raised when a candidate record cannot be found."""

    status_code: int = 404
    code: str = "CANDIDATE_NOT_FOUND"
    detail: str = "Candidate not found."


class ProfileNotFoundError(Exception):
    """Raised when a candidate profile has not been generated yet."""

    status_code: int = 404
    code: str = "PROFILE_NOT_FOUND"
    detail: str = "Candidate profile has not been generated yet."


class UnsupportedInputSourceError(Exception):
    """Raised when a candidate input source cannot be extracted automatically in M3."""

    status_code: int = 422

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class DuplicateProcessingError(Exception):
    """Raised when a research run is already actively processing."""

    status_code: int = 409
    code: str = "RUN_ALREADY_PROCESSING"
    detail: str = "Research run is already processing."


def to_profile_response(profile: CandidateProfile) -> CandidateProfileResponse:
    """Map ORM CandidateProfile to the public CandidateProfileResponse schema."""
    structured: StructuredCandidateProfile | None = None
    if profile.profile_data is not None:
        structured = StructuredCandidateProfile.model_validate(profile.profile_data)

    return CandidateProfileResponse(
        profile_id=profile.id,
        candidate_id=profile.candidate_id,
        research_run_id=profile.research_run_id,
        extraction_status=profile.extraction_status,  # type: ignore[arg-type]
        source_type=profile.source_type,  # type: ignore[arg-type]
        data_origin=profile.data_origin,  # type: ignore[arg-type]
        provider_name=profile.provider_name,
        model_name=profile.model_name,
        page_count=profile.page_count,
        warnings=list(profile.warnings or []),
        profile=structured,
        error_code=profile.error_code,
        error_message=profile.error_message,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def get_candidate_profile(db: Session, candidate_id: str) -> CandidateProfileResponse:
    """Retrieve a candidate's structured profile or raise a domain 404 error."""
    candidate = ProfileRepository.get_candidate_by_id(db, candidate_id)
    if candidate is None:
        raise CandidateNotFoundError()

    profile = ProfileRepository.get_by_candidate_id(db, candidate_id)
    if profile is None:
        raise ProfileNotFoundError()

    return to_profile_response(profile)


def process_candidate_profile_for_run(
    db: Session,
    settings: Settings,
    run_id: str,
    *,
    llm_provider: LLMProvider | None = None,
) -> ProcessRunResponse:
    """Execute the end-to-end M3 candidate profile extraction pipeline for a run."""
    run = RunRepository.get_run_by_id(db, run_id)
    if run is None:
        raise RunNotFoundError()

    if run.status == "processing":
        raise DuplicateProcessingError()

    candidate = run.candidate

    if candidate.input_source == "linkedin_url":
        message = (
            "LinkedIn profile scraping is not permitted. "
            "Upload a PDF resume or wait for an authorized LinkedIn integration."
        )
        RunRepository.mark_failed(
            db,
            run,
            error_code="LINKEDIN_EXTRACTION_UNSUPPORTED",
            error_message=message,
        )
        raise UnsupportedInputSourceError("LINKEDIN_EXTRACTION_UNSUPPORTED", message)

    if run.status == "completed" and candidate.profile is not None:
        existing_profile = candidate.profile
        return ProcessRunResponse(
            run_id=run.id,
            candidate_id=candidate.id,
            status=run.status,  # type: ignore[arg-type]
            extraction_status=existing_profile.extraction_status,  # type: ignore[arg-type]
            profile_id=existing_profile.id,
            warnings=list(existing_profile.warnings or []),
            started_at=run.started_at,
            completed_at=run.completed_at,
            error=None,
        )

    if not candidate.resume_storage_key:
        message = "Candidate has no stored PDF resume to process."
        RunRepository.mark_failed(
            db,
            run,
            error_code="MISSING_RESUME_SOURCE",
            error_message=message,
        )
        raise ResumeExtractionError("MISSING_RESUME_SOURCE", message)

    RunRepository.mark_processing(db, run)

    try:
        extraction = extract_resume_text(settings.upload_dir, candidate.resume_storage_key)

        if extraction.status == "requires_manual_review":
            profile = ProfileRepository.upsert_profile(
                db,
                candidate_id=candidate.id,
                research_run_id=run.id,
                extraction_status="requires_manual_review",
                source_type="resume_pdf",
                data_origin="real",
                provider_name="pymupdf",
                model_name=None,
                page_count=extraction.page_count,
                warnings=extraction.warnings,
                profile_data=None,
                error_code="RESUME_REQUIRES_OCR_OR_REVIEW",
                error_message=extraction.warnings[0] if extraction.warnings else "Resume requires manual review.",
            )
            RunRepository.mark_failed(
                db,
                run,
                error_code="RESUME_REQUIRES_OCR_OR_REVIEW",
                error_message=profile.error_message or "Resume requires manual review.",
            )
            return ProcessRunResponse(
                run_id=run.id,
                candidate_id=candidate.id,
                status=run.status,  # type: ignore[arg-type]
                extraction_status="requires_manual_review",
                profile_id=profile.id,
                warnings=list(profile.warnings or []),
                started_at=run.started_at,
                completed_at=run.completed_at,
                error=RunErrorResponse(code=run.error_code, message=run.error_message),
            )

        provider = llm_provider or get_llm_provider(settings)
        llm_result = provider.extract_candidate_profile(
            extraction.extracted_text,
            StructuredCandidateProfile,
        )

        validated = validate_and_ground_profile(
            llm_result.profile,
            extraction,
            initial_warnings=llm_result.warnings,
        )

        profile = ProfileRepository.upsert_profile(
            db,
            candidate_id=candidate.id,
            research_run_id=run.id,
            extraction_status=validated.extraction_status,
            source_type="resume_pdf",
            data_origin=llm_result.data_origin,
            provider_name=llm_result.provider_name,
            model_name=llm_result.model_name,
            page_count=extraction.page_count,
            warnings=validated.warnings,
            profile_data=validated.profile.model_dump(mode="json"),
            error_code=None,
            error_message=None,
        )
        RunRepository.mark_completed(db, run)

        return ProcessRunResponse(
            run_id=run.id,
            candidate_id=candidate.id,
            status=run.status,  # type: ignore[arg-type]
            extraction_status=profile.extraction_status,  # type: ignore[arg-type]
            profile_id=profile.id,
            warnings=list(profile.warnings or []),
            started_at=run.started_at,
            completed_at=run.completed_at,
            error=None,
        )
    except (ResumeExtractionError, LLMProviderError) as exc:
        db.rollback()
        RunRepository.mark_failed(
            db,
            run,
            error_code=exc.code,
            error_message=exc.detail,
        )
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        logger.warning("Database error during candidate profile persistence (%s)", type(exc).__name__)
        RunRepository.mark_failed(
            db,
            run,
            error_code="PROFILE_PERSISTENCE_ERROR",
            error_message="Failed to persist the extracted candidate profile.",
        )
        raise
    except Exception as exc:
        db.rollback()
        logger.warning("Unexpected error during candidate profile extraction (%s)", type(exc).__name__)
        RunRepository.mark_failed(
            db,
            run,
            error_code="PROFILE_EXTRACTION_ERROR",
            error_message="Candidate profile extraction failed unexpectedly.",
        )
        raise
