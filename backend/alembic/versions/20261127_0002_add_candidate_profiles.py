"""add candidate_profiles table

Revision ID: 20261127_0002
Revises: 20261127_0001
Create Date: 2026-11-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0002"
down_revision: Union[str, Sequence[str], None] = "20261127_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("research_run_id", sa.String(length=36), nullable=True),
        sa.Column("extraction_status", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("data_origin", sa.String(length=16), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("profile_data", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "extraction_status IN ('extracted', 'extracted_with_warnings', 'requires_manual_review', 'failed')",
            name="ck_candidate_profiles_extraction_status",
        ),
        sa.CheckConstraint(
            "source_type IN ('resume_pdf', 'linkedin_url')",
            name="ck_candidate_profiles_source_type",
        ),
        sa.CheckConstraint(
            "data_origin IN ('real', 'demo')",
            name="ck_candidate_profiles_data_origin",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["candidates.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["research_run_id"],
            ["research_runs.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    op.create_index(
        op.f("ix_candidate_profiles_candidate_id"),
        "candidate_profiles",
        ["candidate_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_candidate_profiles_research_run_id"),
        "candidate_profiles",
        ["research_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_candidate_profiles_research_run_id"), table_name="candidate_profiles")
    op.drop_index(op.f("ix_candidate_profiles_candidate_id"), table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
