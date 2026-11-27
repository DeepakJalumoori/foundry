from datetime import UTC, datetime
from typing import Any
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SourceEvidence(Base):
    """Normalized source provenance record shared across M4 entities."""

    __tablename__ = "source_evidence"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_source_evidence_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_source_evidence_data_origin",
        ),
        UniqueConstraint("source_url", "excerpt_hash", name="uq_source_evidence_url_excerpt"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)


class EvidenceLink(Base):
    """Links any M4 domain entity to a SourceEvidence record without duplicating URLs."""

    __tablename__ = "evidence_links"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "evidence_id", name="uq_evidence_links_entity_evidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    evidence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("source_evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evidence: Mapped["SourceEvidence"] = relationship()


class DiscoveryRun(Base):
    """Tracks an M4 startup discovery and intelligence run for a candidate."""

    __tablename__ = "discovery_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'completed_with_warnings', 'failed')",
            name="ck_discovery_runs_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    discovered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    company_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Company(Base):
    """Normalized startup company identity and latest profile summary."""

    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint(
            "stage IN ('pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'other', 'unknown')",
            name="ck_companies_stage",
        ),
        CheckConstraint(
            "opportunity_type IN ('active', 'hidden', 'unknown')",
            name="ck_companies_opportunity_type",
        ),
        CheckConstraint(
            "research_status IN ('pending', 'completed', 'completed_with_warnings', 'requires_review', 'failed')",
            name="ck_companies_research_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_companies_data_origin",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    official_website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_domain: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    product_or_service: Mapped[str | None] = mapped_column(Text, nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", index=True)
    employee_range: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    business_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    research_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    opportunity_type: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown", index=True)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    last_researched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )

    research_records: Mapped[list["CompanyResearch"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    funding_events: Mapped[list["FundingEvent"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    hiring_signals: Mapped[list["HiringSignal"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    job_opportunities: Mapped[list["JobOpportunity"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    founders: Mapped[list["Founder"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )


class CompanyResearch(Base):
    """Point-in-time company research record with claims and conflict notes."""

    __tablename__ = "company_research"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'completed_with_warnings', 'requires_review', 'failed')",
            name="ck_company_research_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_company_research_data_origin",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    discovery_run_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("discovery_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_claims: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    conflicts: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    warnings: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    researched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    company: Mapped["Company"] = relationship(back_populates="research_records")


class FundingEvent(Base):
    """Normalized funding event with separate amount, currency, and dates."""

    __tablename__ = "funding_events"
    __table_args__ = (
        CheckConstraint(
            "round_type IN ('pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'other', 'unknown')",
            name="ck_funding_events_round_type",
        ),
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_funding_events_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_funding_events_data_origin",
        ),
        UniqueConstraint("company_id", "dedup_key", name="uq_funding_events_company_dedup"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dedup_key: Mapped[str] = mapped_column(String(128), nullable=False)
    round_type: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    announced_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    investors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    lead_investor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_claim: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_recent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    company: Mapped["Company"] = relationship(back_populates="funding_events")


class HiringSignal(Base):
    """Explainable hiring signal distinguishing active vs hidden opportunities."""

    __tablename__ = "hiring_signals"
    __table_args__ = (
        CheckConstraint(
            "opportunity_category IN ('active', 'hidden')",
            name="ck_hiring_signals_opportunity_category",
        ),
        CheckConstraint(
            "conclusion_type IN ('verified', 'inferred')",
            name="ck_hiring_signals_conclusion_type",
        ),
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_hiring_signals_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_hiring_signals_data_origin",
        ),
        UniqueConstraint("company_id", "dedup_key", name="uq_hiring_signals_company_dedup"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dedup_key: Mapped[str] = mapped_column(String(128), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    opportunity_category: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_titles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_posting_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    observed_fact: Mapped[str] = mapped_column(Text, nullable=False)
    classification_reason: Mapped[str] = mapped_column(Text, nullable=False)
    conclusion_type: Mapped[str] = mapped_column(String(16), nullable=False, default="inferred")
    uncertainties: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    company: Mapped["Company"] = relationship(back_populates="hiring_signals")


class JobOpportunity(Base):
    """Public job opening associated with a company and hiring signal."""

    __tablename__ = "job_opportunities"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_job_opportunities_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_job_opportunities_data_origin",
        ),
        UniqueConstraint("company_id", "job_url", name="uq_job_opportunities_company_url"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hiring_signal_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("hiring_signals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    posting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    company: Mapped["Company"] = relationship(back_populates="job_opportunities")


class Founder(Base):
    """Discovered founder or co-founder record for a company."""

    __tablename__ = "founders"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_founders_verification_status",
        ),
        CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_founders_data_origin",
        ),
        UniqueConstraint("company_id", "normalized_name", name="uq_founders_company_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_profile_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unverified")
    conflict_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_origin: Mapped[str] = mapped_column(String(16), nullable=False, default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
        onupdate=_utc_now,
    )

    company: Mapped["Company"] = relationship(back_populates="founders")
