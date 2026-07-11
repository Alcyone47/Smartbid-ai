"""add extraction_progress to documents

Revision ID: 0002_add_extraction_progress
Revises: 0001_initial_schema
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_extraction_progress"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("extraction_progress", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    # Already-extracted documents are complete.
    op.execute("UPDATE documents SET extraction_progress = 100 WHERE status = 'extracted'")


def downgrade() -> None:
    op.drop_column("documents", "extraction_progress")
