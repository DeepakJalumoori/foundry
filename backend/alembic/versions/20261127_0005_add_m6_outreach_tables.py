"""add M6 outreach draft tables

Revision ID: 20261127_0005
Revises: 20261127_0004
Create Date: 2026-11-27 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0005"
down_revision: Union[str, Sequence[str], None] = "20261127_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outreach_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=False),
        sa.Column("match_result_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("founder_id", sa.String(length=36), nullable=False),
        sa.Column("outreach_intent", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("original_subject", sa.String(length=500), nullable=False),
        sa.Column("original_body", sa.Text(), nullable=False),
        sa.Column("personalization_rationale", sa.Text(), nullable=False),
        sa.Column("strategy_json", sa.JSON(), nullable=False),
        sa.Column("structured_sections_json", sa.JSON(), nullable=False),
        sa.Column("candidate_strengths_used", sa.JSON(), nullable=False),
        sa.Column("company_facts_used", sa.JSON(), nullable=False),
        sa.Column("unsupported_claims", sa.JSON(), nullable=False),
        sa.Column("review_warnings", sa.JSON(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("generation_provider", sa.String(length=64), nullable=False),
        sa.Column("generation_model", sa.String(length=128), nullable=True),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "outreach_intent IN ('job_interest', 'exploratory', 'general_interest')",
            name="ck_outreach_drafts_intent",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'reviewed', 'approved', 'archived')",
            name="ck_outreach_drafts_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_outreach_drafts_data_origin",
        ),
        sa.CheckConstraint("version >= 1", name="ck_outreach_drafts_version"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["founder_id"], ["founders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_result_id"], ["match_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matching_run_id"], ["matching_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outreach_drafts_candidate_id", "outreach_drafts", ["candidate_id"])
    op.create_index("ix_outreach_drafts_matching_run_id", "outreach_drafts", ["matching_run_id"])
    op.create_index("ix_outreach_drafts_match_result_id", "outreach_drafts", ["match_result_id"])
    op.create_index("ix_outreach_drafts_company_id", "outreach_drafts", ["company_id"])
    op.create_index("ix_outreach_drafts_founder_id", "outreach_drafts", ["founder_id"])
    op.create_index("ix_outreach_drafts_outreach_intent", "outreach_drafts", ["outreach_intent"])
    op.create_index("ix_outreach_drafts_status", "outreach_drafts", ["status"])

    op.create_table(
        "outreach_draft_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("outreach_draft_id", sa.String(length=36), nullable=False),
        sa.Column("source_evidence_id", sa.String(length=36), nullable=True),
        sa.Column("company_id", sa.String(length=36), nullable=True),
        sa.Column("claim_category", sa.String(length=40), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("support_status", sa.String(length=24), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "claim_category IN ('company', 'founder', 'hiring', 'funding', 'job_opportunity', 'candidate_profile')",
            name="ck_outreach_draft_evidence_category",
        ),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_outreach_draft_evidence_verification",
        ),
        sa.CheckConstraint(
            "support_status IN ('supported', 'partially_supported', 'unsupported')",
            name="ck_outreach_draft_evidence_support",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["outreach_draft_id"], ["outreach_drafts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["source_evidence.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_outreach_draft_evidence_outreach_draft_id",
        "outreach_draft_evidence",
        ["outreach_draft_id"],
    )
    op.create_index(
        "ix_outreach_draft_evidence_source_evidence_id",
        "outreach_draft_evidence",
        ["source_evidence_id"],
    )
    op.create_index(
        "ix_outreach_draft_evidence_company_id",
        "outreach_draft_evidence",
        ["company_id"],
    )

    op.create_table(
        "outreach_draft_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("outreach_draft_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(length=24), nullable=False),
        sa.Column("status_at_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "change_type IN ('generated', 'edited', 'status_change')",
            name="ck_outreach_draft_versions_change_type",
        ),
        sa.CheckConstraint(
            "status_at_version IN ('draft', 'reviewed', 'approved', 'archived')",
            name="ck_outreach_draft_versions_status",
        ),
        sa.ForeignKeyConstraint(["outreach_draft_id"], ["outreach_drafts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("outreach_draft_id", "version", name="uq_outreach_draft_versions_draft_version"),
    )
    op.create_index(
        "ix_outreach_draft_versions_outreach_draft_id",
        "outreach_draft_versions",
        ["outreach_draft_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_outreach_draft_versions_outreach_draft_id", table_name="outreach_draft_versions")
    op.drop_table("outreach_draft_versions")

    op.drop_index("ix_outreach_draft_evidence_company_id", table_name="outreach_draft_evidence")
    op.drop_index("ix_outreach_draft_evidence_source_evidence_id", table_name="outreach_draft_evidence")
    op.drop_index("ix_outreach_draft_evidence_outreach_draft_id", table_name="outreach_draft_evidence")
    op.drop_table("outreach_draft_evidence")

    op.drop_index("ix_outreach_drafts_status", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_outreach_intent", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_founder_id", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_company_id", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_match_result_id", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_matching_run_id", table_name="outreach_drafts")
    op.drop_index("ix_outreach_drafts_candidate_id", table_name="outreach_drafts")
    op.drop_table("outreach_drafts")
