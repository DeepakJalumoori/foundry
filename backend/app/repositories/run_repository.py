from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import Candidate
from app.models.research_run import ResearchRun


def _utc_now() -> datetime:
    return datetime.now(UTC)


class RunRepository:
    """Persistence operations for Candidate and ResearchRun entities."""

    @staticmethod
    def create_linkedin_candidate_and_run(db: Session, linkedin_url: str) -> ResearchRun:
        candidate = Candidate(
            input_source="linkedin_url",
            linkedin_url=linkedin_url,
        )
        db.add(candidate)
        db.flush()

        run = ResearchRun(
            candidate_id=candidate.id,
            status="pending",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        db.refresh(candidate)
        return run

    @staticmethod
    def create_resume_candidate_and_run(
        db: Session,
        *,
        resume_filename: str,
        resume_content_type: str | None,
        resume_size_bytes: int,
        resume_storage_key: str,
    ) -> ResearchRun:
        candidate = Candidate(
            input_source="resume_pdf",
            resume_filename=resume_filename,
            resume_content_type=resume_content_type,
            resume_size_bytes=resume_size_bytes,
            resume_storage_key=resume_storage_key,
        )
        db.add(candidate)
        db.flush()

        run = ResearchRun(
            candidate_id=candidate.id,
            status="pending",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        db.refresh(candidate)
        return run

    @staticmethod
    def get_run_by_id(db: Session, run_id: str) -> ResearchRun | None:
        stmt = (
            select(ResearchRun)
            .options(
                selectinload(ResearchRun.candidate).selectinload(Candidate.profile),
            )
            .where(ResearchRun.id == run_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def mark_processing(db: Session, run: ResearchRun) -> ResearchRun:
        run.status = "processing"
        run.started_at = _utc_now()
        run.completed_at = None
        run.error_code = None
        run.error_message = None
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def mark_completed(db: Session, run: ResearchRun) -> ResearchRun:
        run.status = "completed"
        run.completed_at = _utc_now()
        run.error_code = None
        run.error_message = None
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def mark_failed(
        db: Session,
        run: ResearchRun,
        *,
        error_code: str,
        error_message: str,
    ) -> ResearchRun:
        if run.started_at is None:
            run.started_at = _utc_now()
        run.status = "failed"
        run.completed_at = _utc_now()
        run.error_code = error_code[:64]
        run.error_message = error_message
        db.commit()
        db.refresh(run)
        return run
