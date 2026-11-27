from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.candidate_profile import CandidateProfile


class ProfileRepository:
    """Persistence operations for CandidateProfile entities."""

    @staticmethod
    def get_candidate_by_id(db: Session, candidate_id: str) -> Candidate | None:
        return db.get(Candidate, candidate_id)

    @staticmethod
    def get_by_candidate_id(db: Session, candidate_id: str) -> CandidateProfile | None:
        stmt = select(CandidateProfile).where(CandidateProfile.candidate_id == candidate_id)
        return db.scalar(stmt)

    @staticmethod
    def upsert_profile(
        db: Session,
        *,
        candidate_id: str,
        research_run_id: str | None,
        extraction_status: str,
        source_type: str,
        data_origin: str,
        provider_name: str,
        model_name: str | None,
        page_count: int | None,
        warnings: list[str],
        profile_data: dict[str, Any] | None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> CandidateProfile:
        existing = ProfileRepository.get_by_candidate_id(db, candidate_id)
        if existing is not None:
            existing.research_run_id = research_run_id
            existing.extraction_status = extraction_status
            existing.source_type = source_type
            existing.data_origin = data_origin
            existing.provider_name = provider_name
            existing.model_name = model_name
            existing.page_count = page_count
            existing.warnings = warnings
            existing.profile_data = profile_data
            existing.error_code = error_code
            existing.error_message = error_message
            db.flush()
            return existing

        profile = CandidateProfile(
            candidate_id=candidate_id,
            research_run_id=research_run_id,
            extraction_status=extraction_status,
            source_type=source_type,
            data_origin=data_origin,
            provider_name=provider_name,
            model_name=model_name,
            page_count=page_count,
            warnings=warnings,
            profile_data=profile_data,
            error_code=error_code,
            error_message=error_message,
        )
        db.add(profile)
        db.flush()
        return profile
