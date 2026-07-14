"""add equipment grouping to extracted requirements and specifications

Revision ID: 0003_add_equipment_grouping
Revises: 0002_add_extraction_progress
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_equipment_grouping"
down_revision: Union[str, None] = "0002_add_extraction_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("extracted_requirements", "extracted_specifications"):
        # server_default keeps existing rows valid; they group under a single
        # "general" equipment until the document is re-extracted.
        op.add_column(
            table,
            sa.Column("equipment_key", sa.String(), nullable=False, server_default=sa.text("'general'")),
        )
        op.add_column(
            table,
            sa.Column("equipment_label", sa.String(), nullable=False, server_default=sa.text("'General'")),
        )
        op.create_index(f"ix_{table}_equipment_key", table, ["equipment_key"])


def downgrade() -> None:
    for table in ("extracted_requirements", "extracted_specifications"):
        op.drop_index(f"ix_{table}_equipment_key", table_name=table)
        op.drop_column(table, "equipment_label")
        op.drop_column(table, "equipment_key")
