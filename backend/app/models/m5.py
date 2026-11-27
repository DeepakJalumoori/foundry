from datetime import UTC, datetime
from typing import Any
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    DDL,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


FTS5_CREATE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_documents_fts USING fts5(
    document_id UNINDEXED,
    source_evidence_id UNINDEXED,
    company_id UNINDEXED,
    entity_type UNINDEXED,
    verification_status UNINDEXED,
    data_origin UNINDEXED,
    document_title,
    normalized_content,
    tokenize='unicode61'
)
"""

FTS5_DROP_SQL = "DROP TABLE IF EXISTS evidence_documents_fts"


class EvidenceDocument(Base):
    """Normalized searchable document referencing an existing M4 SourceEvidence record."""

    __tablename__ = "evidence_documents"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_evidence_documents_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_evidence_documents_data_origin",
        ),
        UniqueConstraint(
            "company_id",
            "entity_type",
            "entity_id",
            "chunk_index",
            name="uq_evidence_documents_entity_chunk",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_evidence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("source_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    document_title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified", index=True)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo", index=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )


event.listen(
    EvidenceDocument.__table__,
    "after_create",
    DDL(FTS5_CREATE_SQL).execute_if(dialect="sqlite"),
)


class MatchingRun(Base):
    """Tracks an M5 LangGraph candidate-company matching workflow execution."""

    __tablename__ = "matching_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'completed_with_warnings', 'failed')",
            name="ck_matching_runs_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    discovery_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("discovery_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="fit_v1")
    ranking_version: Mapped[str] = mapped_column(String(32), nullable=False, default="rank_v1")
    retrieval_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    candidate_profile_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessments: Mapped[list["CompanyAssessment"]] = relationship(
        back_populates="matching_run",
        cascade="all, delete-orphan",
    )
    results: Mapped[list["MatchResult"]] = relationship(
        back_populates="matching_run",
        cascade="all, delete-orphan",
    )


class CompanyAssessment(Base):
    """Persisted qualitative structured LLM assessment for a candidate-company pair."""

    __tablename__ = "company_assessments"
    __table_args__ = (
        UniqueConstraint("matching_run_id", "company_id", name="uq_company_assessments_run_company"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    matching_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matching_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assessment_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    uncertainties: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    matching_run: Mapped["MatchingRun"] = relationship(back_populates="assessments")


class MatchResult(Base):
    """Persisted explainable candidate-company fit score and independent opportunity assessment."""

    __tablename__ = "match_results"
    __table_args__ = (
        CheckConstraint("fit_score >= 0.0 AND fit_score <= 100.0", name="ck_match_results_fit_score"),
        CheckConstraint("fit_coverage >= 0.0 AND fit_coverage <= 100.0", name="ck_match_results_fit_coverage"),
        CheckConstraint(
            "opportunity_type IN ('active', 'hidden', 'insufficient_evidence')",
            name="ck_match_results_opportunity_type",
        ),
        CheckConstraint(
            "evidence_strength IN ('strong', 'moderate', 'weak', 'insufficient')",
            name="ck_match_results_evidence_strength",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_match_results_data_origin",
        ),
        UniqueConstraint("matching_run_id", "company_id", name="uq_match_results_run_company"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    matching_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matching_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_assessment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("company_assessments.id", ondelete="SET NULL"),
        nullable=True,
    )
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    fit_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="fit_v1")
    dimension_breakdown: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    opportunity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    evidence_strength: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    opportunity_assessment: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    ranking_position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ranking_version: Mapped[str] = mapped_column(String(32), nullable=False, default="rank_v1")
    ranking_score: Mapped[float] = mapped_column(Float, nullable=False)
    ranking_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    ranking_factors: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    company_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    matching_run: Mapped["MatchingRun"] = relationship(back_populates="results")


class RetrievalRecord(Base):
    """Persists retrieved evidence chunks and provenance for a matching run."""

    __tablename__ = "retrieval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    matching_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("matching_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    evidence_document_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("evidence_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_evidence_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("source_evidence.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    bm25_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    retrieved_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
