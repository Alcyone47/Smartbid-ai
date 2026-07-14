"""add manual status_override to projects

Revision ID: 0004_add_project_status_override
Revises: 0003_add_equipment_grouping
Create Date: 2026-07-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_project_status_override"
down_revision: Union[str, None] = "0003_add_equipment_grouping"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: null means "auto" (use the derived status).
    op.add_column("projects", sa.Column("status_override", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "status_override")
