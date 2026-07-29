"""add summary column to documents

Revision ID: 0011_document_summary
Revises: 0010_equipment_matches
Create Date: 2026-07-21

Plain-language LLM summary of an RFP document, generated once during extraction
(see ExtractionService._summarize). Best-effort — nullable, since generation may
be disabled or fail without blocking the requirements extraction itself.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_document_summary"
down_revision: Union[str, None] = "0010_equipment_matches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "summary")
