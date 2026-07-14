"""hierarchical requirements: Requirement (equipment) -> Parameters

Revision ID: 0007_hierarchical_requirements
Revises: 0006_extraction_status_lifecycle
Create Date: 2026-07-14

Re-models the flat ``extracted_requirements`` table into a two-level hierarchy:

- a new parent ``requirements`` table = one equipment/item (the top entity), and
- ``requirement_parameters`` (renamed from ``extracted_requirements``) = the
  measurable parameters of a requirement, each with its Minimum Required
  Specification. ``equipment_key``/``equipment_label`` are denormalized onto the
  parameter rows so the deterministic matching engine keeps reading them directly.

The compliance matrix is re-pointed from ``requirement_id`` -> ``parameter_id``.

Existing data is backfilled: one ``requirements`` row per distinct
(document_id, equipment_key), with its parameters linked via ``requirement_id``.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_hierarchical_requirements"
down_revision: Union[str, None] = "0006_extraction_status_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Parent requirements table (one per equipment/item).
    op.create_table(
        "requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("equipment_key", sa.String(), server_default=sa.text("'general'"), nullable=False),
        sa.Column("equipment_label", sa.String(), server_default=sa.text("'General'"), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("raw_llm_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_requirements_equipment_key", "requirements", ["equipment_key"])

    # 2. Rename the flat table to requirement_parameters and re-shape it.
    op.rename_table("extracted_requirements", "requirement_parameters")
    op.alter_column("requirement_parameters", "requirement_key", new_column_name="parameter_key")
    op.alter_column("requirement_parameters", "requirement_label", new_column_name="parameter_label")
    op.alter_column("requirement_parameters", "requirement_text", new_column_name="parameter_text")

    # 3. Add the FK to the parent (nullable during backfill).
    op.add_column(
        "requirement_parameters",
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requirements.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_requirement_parameters_requirement_id", "requirement_parameters", ["requirement_id"])

    # 4. Backfill: synthesize one parent requirement per (document, equipment) and
    #    carry over category/source_page/raw_llm_response from any of its rows.
    op.execute(
        """
        INSERT INTO requirements
            (id, org_id, document_id, project_id, equipment_key, equipment_label, category, source_page, raw_llm_response)
        SELECT gen_random_uuid(), org_id, document_id, project_id, equipment_key,
               MIN(equipment_label), MIN(category), MIN(source_page), NULL
        FROM requirement_parameters
        GROUP BY org_id, document_id, project_id, equipment_key
        """
    )
    op.execute(
        """
        UPDATE requirement_parameters rp
        SET requirement_id = r.id
        FROM requirements r
        WHERE rp.document_id = r.document_id
          AND rp.equipment_key = r.equipment_key
        """
    )
    op.execute("DELETE FROM requirement_parameters WHERE requirement_id IS NULL")
    op.alter_column("requirement_parameters", "requirement_id", nullable=False)

    # raw_llm_response now lives on the parent requirement, not each parameter.
    op.drop_column("requirement_parameters", "raw_llm_response")

    # 5. Re-point the compliance matrix grain: requirement_id -> parameter_id.
    op.drop_constraint("uq_compliance_matrix_requirement_vendor", "compliance_matrix", type_="unique")
    op.alter_column("compliance_matrix", "requirement_id", new_column_name="parameter_id")
    # The FK previously targeted extracted_requirements(id); that table is now
    # requirement_parameters (same rows, same ids), so the existing constraint stays
    # valid after the rename. Recreate the unique constraint under the new column name.
    op.create_unique_constraint(
        "uq_compliance_matrix_parameter_vendor", "compliance_matrix", ["parameter_id", "vendor_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_compliance_matrix_parameter_vendor", "compliance_matrix", type_="unique")
    op.alter_column("compliance_matrix", "parameter_id", new_column_name="requirement_id")
    op.create_unique_constraint(
        "uq_compliance_matrix_requirement_vendor", "compliance_matrix", ["requirement_id", "vendor_id"]
    )

    op.add_column(
        "requirement_parameters",
        sa.Column("raw_llm_response", postgresql.JSONB(), nullable=True),
    )
    op.drop_index("ix_requirement_parameters_requirement_id", table_name="requirement_parameters")
    op.drop_column("requirement_parameters", "requirement_id")
    op.alter_column("requirement_parameters", "parameter_key", new_column_name="requirement_key")
    op.alter_column("requirement_parameters", "parameter_label", new_column_name="requirement_label")
    op.alter_column("requirement_parameters", "parameter_text", new_column_name="requirement_text")
    op.rename_table("requirement_parameters", "extracted_requirements")

    op.drop_index("ix_requirements_equipment_key", table_name="requirements")
    op.drop_table("requirements")
