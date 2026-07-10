"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "orgs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "org_members",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(), server_default="member", nullable=False),
    )

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("client_name", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="draft", nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_projects_org_id", "projects", ["org_id"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("vendor_name", sa.String(), nullable=True),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("mime_type", sa.String(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="uploaded", nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])

    op.create_table(
        "extracted_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requirement_key", sa.String(), nullable=False),
        sa.Column("requirement_label", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("requirement_text", sa.String(), nullable=False),
        sa.Column("expected_value", sa.String(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("operator", sa.String(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_span", postgresql.JSONB(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("raw_llm_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_extracted_requirements_project_id", "extracted_requirements", ["project_id"])
    op.create_index("ix_extracted_requirements_document_id", "extracted_requirements", ["document_id"])

    op.create_table(
        "extracted_specifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_name", sa.String(), nullable=False),
        sa.Column("spec_key", sa.String(), nullable=False),
        sa.Column("spec_label", sa.String(), nullable=False),
        sa.Column("spec_text", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_span", postgresql.JSONB(), nullable=True),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("raw_llm_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_extracted_specifications_project_id", "extracted_specifications", ["project_id"])
    op.create_index("ix_extracted_specifications_document_id", "extracted_specifications", ["document_id"])

    op.create_table(
        "compliance_matrix",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extracted_requirements.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "matched_specification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extracted_specifications.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("match_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("requirement_id", "vendor_document_id"),
    )
    op.create_index("ix_compliance_matrix_project_id", "compliance_matrix", ["project_id"])


def downgrade() -> None:
    op.drop_table("compliance_matrix")
    op.drop_table("extracted_specifications")
    op.drop_table("extracted_requirements")
    op.drop_table("documents")
    op.drop_table("projects")
    op.drop_table("org_members")
    op.drop_table("orgs")
