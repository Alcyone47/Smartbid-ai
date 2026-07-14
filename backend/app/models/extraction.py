import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

EMBEDDING_DIM = 1024


class Requirement(Base):
    """One equipment/item required by the RFP (the top of the hierarchy).

    A Requirement groups a list of ``RequirementParameter`` rows, each stating a
    Minimum Required Specification. ``equipment_key``/``equipment_label`` are the
    equipment identity used to pair against vendor specifications.
    """

    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    equipment_key: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'general'"), index=True)
    equipment_label: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'General'"))
    category: Mapped[str | None] = mapped_column(String)
    source_page: Mapped[int | None] = mapped_column()
    raw_llm_response: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    parameters: Mapped[list["RequirementParameter"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
        order_by="RequirementParameter.created_at",
    )


class RequirementParameter(Base):
    """A single measurable parameter of a Requirement with its Minimum Required
    Specification (``expected_value``/``unit``/``operator`` + mandatory flag).

    ``equipment_key``/``equipment_label`` are denormalized from the parent so the
    deterministic matching engine and report joins can read them without loading
    the parent. The ``requirement_*`` read-only properties preserve the attribute
    names the matching engine already reads, keeping that package unchanged.
    """

    __tablename__ = "requirement_parameters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    equipment_key: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'general'"), index=True)
    equipment_label: Mapped[str] = mapped_column(String, nullable=False, server_default=text("'General'"))
    category: Mapped[str | None] = mapped_column(String)
    parameter_key: Mapped[str] = mapped_column(String, nullable=False)
    parameter_label: Mapped[str] = mapped_column(String, nullable=False)
    parameter_text: Mapped[str] = mapped_column(String, nullable=False)
    expected_value: Mapped[str | None] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    operator: Mapped[str | None] = mapped_column(String)
    is_mandatory: Mapped[bool] = mapped_column(server_default=text("true"))
    source_page: Mapped[int | None] = mapped_column()
    source_span: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    requirement: Mapped["Requirement"] = relationship(back_populates="parameters")

    # Aliases so the deterministic matching engine (which reads requirement_key /
    # requirement_label / requirement_text) consumes a Parameter unchanged.
    @property
    def requirement_key(self) -> str:
        return self.parameter_key

    @property
    def requirement_label(self) -> str:
        return self.parameter_label

    @property
    def requirement_text(self) -> str:
        return self.parameter_text


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
