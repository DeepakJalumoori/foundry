"""add M4 startup intelligence tables

Revision ID: 20261127_0003
Revises: 20261127_0002
Create Date: 2026-11-27 17:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0003"
down_revision: Union[str, Sequence[str], None] = "20261127_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=False),
        sa.Column("source_domain", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("excerpt_hash", sa.String(length=64), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_source_evidence_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_source_evidence_data_origin",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url", "excerpt_hash", name="uq_source_evidence_url_excerpt"),
    )
    op.create_index(op.f("ix_source_evidence_source_domain"), "source_evidence", ["source_domain"], unique=False)
    op.create_index(op.f("ix_source_evidence_source_url"), "source_evidence", ["source_url"], unique=False)

    op.create_table(
        "evidence_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["source_evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "entity_id", "evidence_id", name="uq_evidence_links_entity_evidence"),
    )
    op.create_index(op.f("ix_evidence_links_entity_id"), "evidence_links", ["entity_id"], unique=False)
    op.create_index(op.f("ix_evidence_links_entity_type"), "evidence_links", ["entity_type"], unique=False)
    op.create_index(op.f("ix_evidence_links_evidence_id"), "evidence_links", ["evidence_id"], unique=False)

    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.Column("discovered_count", sa.Integer(), nullable=False),
        sa.Column("company_ids", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'completed_with_warnings', 'failed')",
            name="ck_discovery_runs_status",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_discovery_runs_candidate_id"), "discovery_runs", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_discovery_runs_status"), "discovery_runs", ["status"], unique=False)

    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("official_website", sa.String(length=500), nullable=True),
        sa.Column("normalized_domain", sa.String(length=255), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("product_or_service", sa.Text(), nullable=True),
        sa.Column("headquarters", sa.String(length=255), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=20), nullable=False),
        sa.Column("employee_range", sa.String(length=64), nullable=True),
        sa.Column("tech_stack", sa.JSON(), nullable=False),
        sa.Column("business_model", sa.String(length=255), nullable=True),
        sa.Column("research_status", sa.String(length=32), nullable=False),
        sa.Column("opportunity_type", sa.String(length=16), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("last_researched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "stage IN ('pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'other', 'unknown')",
            name="ck_companies_stage",
        ),
        sa.CheckConstraint(
            "opportunity_type IN ('active', 'hidden', 'unknown')",
            name="ck_companies_opportunity_type",
        ),
        sa.CheckConstraint(
            "research_status IN ('pending', 'completed', 'completed_with_warnings', 'requires_review', 'failed')",
            name="ck_companies_research_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_companies_data_origin",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_domain"),
    )
    op.create_index(op.f("ix_companies_external_id"), "companies", ["external_id"], unique=False)
    op.create_index(op.f("ix_companies_industry"), "companies", ["industry"], unique=False)
    op.create_index(op.f("ix_companies_normalized_domain"), "companies", ["normalized_domain"], unique=True)
    op.create_index(op.f("ix_companies_normalized_name"), "companies", ["normalized_name"], unique=False)
    op.create_index(op.f("ix_companies_opportunity_type"), "companies", ["opportunity_type"], unique=False)
    op.create_index(op.f("ix_companies_stage"), "companies", ["stage"], unique=False)

    op.create_table(
        "company_research",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("discovery_run_id", sa.String(length=36), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_claims", sa.JSON(), nullable=False),
        sa.Column("conflicts", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("researched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'completed_with_warnings', 'requires_review', 'failed')",
            name="ck_company_research_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_company_research_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["discovery_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_company_research_company_id"), "company_research", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_company_research_discovery_run_id"),
        "company_research",
        ["discovery_run_id"],
        unique=False,
    )

    op.create_table(
        "funding_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("round_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("announced_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("investors", sa.JSON(), nullable=False),
        sa.Column("lead_investor", sa.String(length=255), nullable=True),
        sa.Column("original_claim", sa.Text(), nullable=True),
        sa.Column("normalized_summary", sa.Text(), nullable=True),
        sa.Column("is_recent", sa.Boolean(), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "round_type IN ('pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'other', 'unknown')",
            name="ck_funding_events_round_type",
        ),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_funding_events_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_funding_events_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "dedup_key", name="uq_funding_events_company_dedup"),
    )
    op.create_index(op.f("ix_funding_events_company_id"), "funding_events", ["company_id"], unique=False)

    op.create_table(
        "hiring_signals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("dedup_key", sa.String(length=128), nullable=False),
        sa.Column("signal_type", sa.String(length=40), nullable=False),
        sa.Column("opportunity_category", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_titles", sa.JSON(), nullable=False),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("job_posting_url", sa.String(length=1000), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_fact", sa.Text(), nullable=False),
        sa.Column("classification_reason", sa.Text(), nullable=False),
        sa.Column("conclusion_type", sa.String(length=16), nullable=False),
        sa.Column("uncertainties", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "opportunity_category IN ('active', 'hidden')",
            name="ck_hiring_signals_opportunity_category",
        ),
        sa.CheckConstraint(
            "conclusion_type IN ('verified', 'inferred')",
            name="ck_hiring_signals_conclusion_type",
        ),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_hiring_signals_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_hiring_signals_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "dedup_key", name="uq_hiring_signals_company_dedup"),
    )
    op.create_index(op.f("ix_hiring_signals_company_id"), "hiring_signals", ["company_id"], unique=False)

    op.create_table(
        "job_opportunities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("hiring_signal_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("job_url", sa.String(length=1000), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("posting_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_job_opportunities_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_job_opportunities_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hiring_signal_id"], ["hiring_signals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "job_url", name="uq_job_opportunities_company_url"),
    )
    op.create_index(op.f("ix_job_opportunities_company_id"), "job_opportunities", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_job_opportunities_hiring_signal_id"),
        "job_opportunities",
        ["hiring_signal_id"],
        unique=False,
    )

    op.create_table(
        "founders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("role_title", sa.String(length=255), nullable=True),
        sa.Column("public_profile_url", sa.String(length=1000), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("conflict_notes", sa.Text(), nullable=True),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_founders_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_founders_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "normalized_name", name="uq_founders_company_name"),
    )
    op.create_index(op.f("ix_founders_company_id"), "founders", ["company_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_founders_company_id"), table_name="founders")
    op.drop_table("founders")

    op.drop_index(op.f("ix_job_opportunities_hiring_signal_id"), table_name="job_opportunities")
    op.drop_index(op.f("ix_job_opportunities_company_id"), table_name="job_opportunities")
    op.drop_table("job_opportunities")

    op.drop_index(op.f("ix_hiring_signals_company_id"), table_name="hiring_signals")
    op.drop_table("hiring_signals")

    op.drop_index(op.f("ix_funding_events_company_id"), table_name="funding_events")
    op.drop_table("funding_events")

    op.drop_index(op.f("ix_company_research_discovery_run_id"), table_name="company_research")
    op.drop_index(op.f("ix_company_research_company_id"), table_name="company_research")
    op.drop_table("company_research")

    op.drop_index(op.f("ix_companies_stage"), table_name="companies")
    op.drop_index(op.f("ix_companies_opportunity_type"), table_name="companies")
    op.drop_index(op.f("ix_companies_normalized_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_normalized_domain"), table_name="companies")
    op.drop_index(op.f("ix_companies_industry"), table_name="companies")
    op.drop_index(op.f("ix_companies_external_id"), table_name="companies")
    op.drop_table("companies")

    op.drop_index(op.f("ix_discovery_runs_status"), table_name="discovery_runs")
    op.drop_index(op.f("ix_discovery_runs_candidate_id"), table_name="discovery_runs")
    op.drop_table("discovery_runs")

    op.drop_index(op.f("ix_evidence_links_evidence_id"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_entity_type"), table_name="evidence_links")
    op.drop_index(op.f("ix_evidence_links_entity_id"), table_name="evidence_links")
    op.drop_table("evidence_links")

    op.drop_index(op.f("ix_source_evidence_source_url"), table_name="source_evidence")
    op.drop_index(op.f("ix_source_evidence_source_domain"), table_name="source_evidence")
    op.drop_table("source_evidence")
