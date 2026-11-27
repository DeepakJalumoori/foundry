"""add M5 RAG and matching tables

Revision ID: 20261127_0004
Revises: 20261127_0003
Create Date: 2026-11-27 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0004"
down_revision: Union[str, Sequence[str], None] = "20261127_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_evidence_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("document_title", sa.String(length=500), nullable=False),
        sa.Column("normalized_content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "verification_status IN ('verified', 'unverified', 'requires_review')",
            name="ck_evidence_documents_verification_status",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_evidence_documents_data_origin",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["source_evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "entity_type",
            "entity_id",
            "chunk_index",
            name="uq_evidence_documents_entity_chunk",
        ),
    )
    op.create_index(op.f("ix_evidence_documents_company_id"), "evidence_documents", ["company_id"], unique=False)
    op.create_index(op.f("ix_evidence_documents_content_hash"), "evidence_documents", ["content_hash"], unique=False)
    op.create_index(op.f("ix_evidence_documents_data_origin"), "evidence_documents", ["data_origin"], unique=False)
    op.create_index(op.f("ix_evidence_documents_entity_id"), "evidence_documents", ["entity_id"], unique=False)
    op.create_index(op.f("ix_evidence_documents_entity_type"), "evidence_documents", ["entity_type"], unique=False)
    op.create_index(
        op.f("ix_evidence_documents_source_evidence_id"),
        "evidence_documents",
        ["source_evidence_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_documents_verification_status"),
        "evidence_documents",
        ["verification_status"],
        unique=False,
    )

    op.execute(
        """
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
    )

    op.create_table(
        "matching_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("discovery_run_id", sa.String(length=36), nullable=True),
        sa.Column("company_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("ranking_version", sa.String(length=32), nullable=False),
        sa.Column("retrieval_config", sa.JSON(), nullable=False),
        sa.Column("candidate_profile_snapshot", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'completed_with_warnings', 'failed')",
            name="ck_matching_runs_status",
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discovery_run_id"], ["discovery_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_matching_runs_candidate_id"), "matching_runs", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_matching_runs_discovery_run_id"), "matching_runs", ["discovery_run_id"], unique=False)
    op.create_index(op.f("ix_matching_runs_status"), "matching_runs", ["status"], unique=False)

    op.create_table(
        "company_assessments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("assessment_data", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("uncertainties", sa.JSON(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matching_run_id"], ["matching_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matching_run_id", "company_id", name="uq_company_assessments_run_company"),
    )
    op.create_index(op.f("ix_company_assessments_company_id"), "company_assessments", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_company_assessments_matching_run_id"),
        "company_assessments",
        ["matching_run_id"],
        unique=False,
    )

    op.create_table(
        "match_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("company_assessment_id", sa.String(length=36), nullable=True),
        sa.Column("fit_score", sa.Float(), nullable=False),
        sa.Column("fit_coverage", sa.Float(), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("dimension_breakdown", sa.JSON(), nullable=False),
        sa.Column("opportunity_type", sa.String(length=32), nullable=False),
        sa.Column("evidence_strength", sa.String(length=20), nullable=False),
        sa.Column("opportunity_assessment", sa.JSON(), nullable=False),
        sa.Column("ranking_position", sa.Integer(), nullable=False),
        sa.Column("ranking_version", sa.String(length=32), nullable=False),
        sa.Column("ranking_score", sa.Float(), nullable=False),
        sa.Column("ranking_explanation", sa.Text(), nullable=False),
        sa.Column("ranking_factors", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("company_snapshot", sa.JSON(), nullable=False),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("fit_score >= 0.0 AND fit_score <= 100.0", name="ck_match_results_fit_score"),
        sa.CheckConstraint("fit_coverage >= 0.0 AND fit_coverage <= 100.0", name="ck_match_results_fit_coverage"),
        sa.CheckConstraint(
            "opportunity_type IN ('active', 'hidden', 'insufficient_evidence')",
            name="ck_match_results_opportunity_type",
        ),
        sa.CheckConstraint(
            "evidence_strength IN ('strong', 'moderate', 'weak', 'insufficient')",
            name="ck_match_results_evidence_strength",
        ),
        sa.CheckConstraint("data_origin IN ('real', 'demo')", name="ck_match_results_data_origin"),
        sa.ForeignKeyConstraint(["company_assessment_id"], ["company_assessments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matching_run_id"], ["matching_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("matching_run_id", "company_id", name="uq_match_results_run_company"),
    )
    op.create_index(op.f("ix_match_results_company_id"), "match_results", ["company_id"], unique=False)
    op.create_index(op.f("ix_match_results_evidence_strength"), "match_results", ["evidence_strength"], unique=False)
    op.create_index(op.f("ix_match_results_matching_run_id"), "match_results", ["matching_run_id"], unique=False)
    op.create_index(op.f("ix_match_results_opportunity_type"), "match_results", ["opportunity_type"], unique=False)
    op.create_index(op.f("ix_match_results_ranking_position"), "match_results", ["ranking_position"], unique=False)

    op.create_table(
        "retrieval_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=False),
        sa.Column("evidence_document_id", sa.String(length=36), nullable=True),
        sa.Column("source_evidence_id", sa.String(length=36), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("bm25_score", sa.Float(), nullable=True),
        sa.Column("retrieved_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_document_id"], ["evidence_documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matching_run_id"], ["matching_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_evidence_id"], ["source_evidence.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retrieval_records_company_id"), "retrieval_records", ["company_id"], unique=False)
    op.create_index(
        op.f("ix_retrieval_records_evidence_document_id"),
        "retrieval_records",
        ["evidence_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retrieval_records_matching_run_id"),
        "retrieval_records",
        ["matching_run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_retrieval_records_source_evidence_id"),
        "retrieval_records",
        ["source_evidence_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("retrieval_records")
    op.drop_table("match_results")
    op.drop_table("company_assessments")
    op.drop_table("matching_runs")
    op.execute("DROP TABLE IF EXISTS evidence_documents_fts")
    op.drop_table("evidence_documents")
