import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

EMBEDDING_DIM = 1024


class ExtractedRequirement(Base):
    __tablename__ = "extracted_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    equipment_key: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'general'"), index=True)
    equipment_label: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'General'"))
    requirement_key: Mapped[str] = mapped_column(String, nullable=False)
    requirement_label: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String)
    requirement_text: Mapped[str] = mapped_column(String, nullable=False)
    expected_value: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    operator: Mapped[str | None] = mapped_column(String)
    is_mandatory: Mapped[bool] = mapped_column(server_default=text("true"))
    source_page: Mapped[int | None] = mapped_column()
    source_span: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    raw_llm_response: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class ExtractedSpecification(Base):
    __tablename__ = "extracted_specifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String, nullable=False)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    equipment_key: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'general'"), index=True)
    equipment_label: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'General'"))
    spec_key: Mapped[str] = mapped_column(String, nullable=False)
    spec_label: Mapped[str] = mapped_column(String, nullable=False)
    spec_text: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    source_page: Mapped[int | None] = mapped_column()
    source_span: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    raw_llm_response: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
