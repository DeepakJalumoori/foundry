"""add partial unique index for active outreach drafts

Revision ID: 20261127_0006
Revises: 20261127_0005
Create Date: 2026-11-27 22:32:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261127_0006"
down_revision: Union[str, Sequence[str], None] = "20261127_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_outreach_drafts_active_unique",
        "outreach_drafts",
        ["matching_run_id", "company_id", "founder_id", "outreach_intent"],
        unique=True,
        sqlite_where=sa.text("status != 'archived'"),
    )


def downgrade() -> None:
    op.drop_index("uq_outreach_drafts_active_unique", table_name="outreach_drafts")
