"""equipment_matches: persisted stage-1 equipment pairing per (requirement, vendor)

Revision ID: 0010_equipment_matches
Revises: 0009_doc_uploaded_status
Create Date: 2026-07-21

Splits matching into two persisted stages. Stage 1 (this table) picks, for each
RFP equipment, the single best-matching vendor equipment group for a vendor - or
marks it unmatched. Stage 2 (compliance_matrix, unchanged) then only compares
specs for equipment Stage 1 actually paired, never falling back to the full
vendor spec pool.

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_equipment_matches"
down_revision: Union[str, None] = "0009_doc_uploaded_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "equipment_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("matched_equipment_key", sa.String(), nullable=True),
        sa.Column("matched_equipment_label", sa.String(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("match_status", sa.String(), nullable=False),
        sa.Column("vendor_source_page", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_equipment_matches_project_id", "equipment_matches", ["project_id"])
    op.create_index("ix_equipment_matches_vendor_id", "equipment_matches", ["vendor_id"])
    op.create_unique_constraint(
        "uq_equipment_matches_requirement_vendor", "equipment_matches", ["requirement_id", "vendor_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_equipment_matches_requirement_vendor", "equipment_matches", type_="unique")
    op.drop_index("ix_equipment_matches_vendor_id", table_name="equipment_matches")
    op.drop_index("ix_equipment_matches_project_id", table_name="equipment_matches")
    op.drop_table("equipment_matches")
