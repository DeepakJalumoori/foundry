"""create candidates and research_runs tables

Revision ID: 20261127_0001
Revises:
Create Date: 2026-11-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("input_source", sa.String(length=20), nullable=False),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("resume_filename", sa.String(length=255), nullable=True),
        sa.Column("resume_content_type", sa.String(length=100), nullable=True),
        sa.Column("resume_size_bytes", sa.Integer(), nullable=True),
        sa.Column("resume_storage_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "input_source IN ('linkedin_url', 'resume_pdf')",
            name="ck_candidates_input_source",
        ),
        sa.CheckConstraint(
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "research_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_research_runs_status",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_runs_candidate_id"), "research_runs", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_research_runs_status"), "research_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_research_runs_status"), table_name="research_runs")
    op.drop_index(op.f("ix_research_runs_candidate_id"), table_name="research_runs")
    op.drop_table("research_runs")
    op.drop_table("candidates")
