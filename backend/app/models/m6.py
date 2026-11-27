from datetime import UTC, datetime
from typing import Any
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class OutreachDraft(Base):
    """Persisted evidence-grounded founder outreach draft with human review lifecycle."""

    __tablename__ = "outreach_drafts"
    __table_args__ = (
        CheckConstraint(
            "outreach_intent IN ('job_interest', 'exploratory', 'general_interest')",
            name="ck_outreach_drafts_intent",
        ),
        CheckConstraint(
            "status IN ('draft', 'reviewed', 'approved', 'archived')",
            name="ck_outreach_drafts_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_outreach_drafts_data_origin",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_outreach_drafts_version",
        ),
        Index(
            "uq_outreach_drafts_active_unique",
            "matching_run_id",
            "company_id",
            "founder_id",
            "outreach_intent",
            unique=True,
            sqlite_where=text("status != 'archived'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matching_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matching_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    founder_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("founders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    outreach_intent: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    original_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    original_body: Mapped[str] = mapped_column(Text, nullable=False)
    personalization_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    strategy_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    structured_sections_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    candidate_strengths_used: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    company_facts_used: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    unsupported_claims: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    review_warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generation_provider: Mapped[str] = mapped_column(String(64), nullable=False)
    generation_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence_items: Mapped[list["OutreachDraftEvidence"]] = relationship(
        back_populates="draft",
        cascade="all, delete-orphan",
    )
    versions: Mapped[list["OutreachDraftVersion"]] = relationship(
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="OutreachDraftVersion.version.asc()",
    )


class OutreachDraftEvidence(Base):
    """Claim-level evidence grounding record linked to an OutreachDraft and SourceEvidence."""

    __tablename__ = "outreach_draft_evidence"
    __table_args__ = (
        CheckConstraint(
            "claim_category IN ('company', 'founder', 'hiring', 'funding', 'job_opportunity', 'candidate_profile')",
            name="ck_outreach_draft_evidence_category",
        ),
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_outreach_draft_evidence_verification",
        ),
        CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'unsupported')",
            name="ck_outreach_draft_evidence_support",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    outreach_draft_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("outreach_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_evidence_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("source_evidence.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    claim_category: Mapped[str] = mapped_column(String(40), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    support_status: Mapped[str] = mapped_column(String(24), nullable=False, default="supported")
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    draft: Mapped["OutreachDraft"] = relationship(back_populates="evidence_items")


class OutreachDraftVersion(Base):
    """Lightweight version history preserving generated and edited outreach draft snapshots."""

    __tablename__ = "outreach_draft_versions"
    __table_args__ = (
        CheckConstraint(
            "change_type IN ('generated', 'edited', 'status_change')",
            name="ck_outreach_draft_versions_change_type",
        ),
        CheckConstraint(
            "status_at_version IN ('draft', 'reviewed', 'approved', 'archived')",
            name="ck_outreach_draft_versions_status",
        ),
        UniqueConstraint("outreach_draft_id", "version", name="uq_outreach_draft_versions_draft_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    outreach_draft_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("outreach_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status_at_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    draft: Mapped["OutreachDraft"] = relationship(back_populates="versions")
