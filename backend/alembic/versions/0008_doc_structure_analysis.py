"""add structure_analysis audit column to documents

Revision ID: 0008_doc_structure_analysis
Revises: 0007_hierarchical_requirements
Create Date: 2026-07-17

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008_doc_structure_analysis"
down_revision: Union[str, None] = "0007_hierarchical_requirements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: null means the structure pre-pass was skipped or failed.
    op.add_column("documents", sa.Column("structure_analysis", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "structure_analysis")
