from datetime import UTC, datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.research_run import ResearchRun


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Candidate(Base):
    """Represents a candidate submission via LinkedIn URL or resume PDF."""

    __tablename__ = "candidates"
    __table_args__ = (
        CheckConstraint(
            "input_source IN ('linkedin_url', 'resume_pdf')",
            name="ck_candidates_input_source",
        ),
        CheckConstraint(
            "(input_source = 'linkedin_url' "
            "AND linkedin_url IS NOT NULL "
            "AND resume_filename IS NULL "
            "AND resume_content_type IS NULL "
            "AND resume_size_bytes IS NULL "
            "AND resume_storage_key IS NULL) "
            "OR "
            "(input_source = 'resume_pdf' "
            "AND linkedin_url IS NULL "
            "AND resume_filename IS NOT NULL "
            "AND resume_size_bytes IS NOT NULL "
            "AND resume_storage_key IS NOT NULL)",
            name="ck_candidates_source_fields",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    input_source: Mapped[str] = mapped_column(String(20), nullable=False)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resume_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resume_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )

    research_runs: Mapped[list["ResearchRun"]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
