"""add vendor entity; re-grain compliance from vendor_document to vendor

Revision ID: 0005_add_vendor_entity
Revises: 0004_add_project_status_override
Create Date: 2026-07-12

Introduces a first-class ``vendors`` table so a vendor can own multiple proposal
PDFs. Documents and extracted specifications gain a ``vendor_id``; the compliance
matrix is re-grained from (requirement, vendor_document) to (requirement, vendor)
so all of a vendor's PDFs are matched together into one column.

Existing data is backfilled: one vendor per distinct (project, vendor_name) among
vendor_proposal documents, then vendor_id propagated to documents, specifications,
and compliance rows.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_add_vendor_entity"
down_revision: Union[str, None] = "0004_add_project_status_override"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. vendors table
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vendors_project_id", "vendors", ["project_id"])

    # 2. documents.vendor_id + backfill (one vendor per distinct project/name)
    op.add_column(
        "documents",
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_documents_vendor_id", "documents", ["vendor_id"])
    op.execute(
        """
        INSERT INTO vendors (id, org_id, project_id, name)
        SELECT gen_random_uuid(), org_id, project_id, vendor_name
        FROM documents
        WHERE doc_type = 'vendor_proposal' AND vendor_name IS NOT NULL
        GROUP BY org_id, project_id, vendor_name
        """
    )
    op.execute(
        """
        UPDATE documents d
        SET vendor_id = v.id
        FROM vendors v
        WHERE d.doc_type = 'vendor_proposal'
          AND d.vendor_name IS NOT NULL
          AND d.org_id = v.org_id
          AND d.project_id = v.project_id
          AND d.vendor_name = v.name
        """
    )

    # 3. extracted_specifications.vendor_id + backfill from its document
    op.add_column(
        "extracted_specifications",
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_extracted_specifications_vendor_id", "extracted_specifications", ["vendor_id"])
    op.execute(
        """
        UPDATE extracted_specifications es
        SET vendor_id = d.vendor_id
        FROM documents d
        WHERE es.document_id = d.id
        """
    )

    # 4. compliance_matrix: add vendor_id, backfill, drop vendor_document_id grain
    op.add_column(
        "compliance_matrix",
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=True),
    )
    op.execute(
        """
        UPDATE compliance_matrix cm
        SET vendor_id = d.vendor_id
        FROM documents d
        WHERE cm.vendor_document_id = d.id
        """
    )
    # Drop rows that couldn't be attributed to a vendor (should be none in practice).
    op.execute("DELETE FROM compliance_matrix WHERE vendor_id IS NULL")
    op.alter_column("compliance_matrix", "vendor_id", nullable=False)
    # Dropping the column cascades its FK and the old (requirement_id, vendor_document_id) unique constraint.
    op.drop_column("compliance_matrix", "vendor_document_id")
    op.create_unique_constraint(
        "uq_compliance_matrix_requirement_vendor", "compliance_matrix", ["requirement_id", "vendor_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_compliance_matrix_requirement_vendor", "compliance_matrix", type_="unique")
    op.add_column(
        "compliance_matrix",
        sa.Column("vendor_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=True),
    )
    op.drop_column("compliance_matrix", "vendor_id")

    op.drop_index("ix_extracted_specifications_vendor_id", table_name="extracted_specifications")
    op.drop_column("extracted_specifications", "vendor_id")

    op.drop_index("ix_documents_vendor_id", table_name="documents")
    op.drop_column("documents", "vendor_id")

    op.drop_index("ix_vendors_project_id", table_name="vendors")
    op.drop_table("vendors")
