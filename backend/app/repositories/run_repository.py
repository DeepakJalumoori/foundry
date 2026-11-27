from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import Candidate
from app.models.research_run import ResearchRun


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
            .options(selectinload(ResearchRun.candidate))
            .where(ResearchRun.id == run_id)
        )
        return db.scalar(stmt)
