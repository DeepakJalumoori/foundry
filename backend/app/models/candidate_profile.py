from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate


def _utc_now() -> datetime:
    return datetime.now(UTC)


class CandidateProfile(Base):
    """Persisted structured candidate profile extracted from a candidate's resume."""

    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint(
            "extraction_status IN ('extracted', 'extracted_with_warnings', 'requires_manual_review', 'failed')",
            name="ck_candidate_profiles_extraction_status",
        ),
        CheckConstraint(
            "source_type IN ('resume_pdf', 'linkedin_url')",
            name="ck_candidate_profiles_source_type",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_candidate_profiles_data_origin",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    research_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("research_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    extraction_status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    profile_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="profile")
