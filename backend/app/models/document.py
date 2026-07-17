import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String)
    # Set for vendor_proposal documents; groups multiple PDFs under one vendor.
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    page_count: Mapped[int | None] = mapped_column()
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="queued")
    # Audit trail of the structure pre-pass (classified sections + selected
    # pages) so "why was this page skipped?" is answerable from the DB.
    structure_analysis: Mapped[dict | None] = mapped_column(JSONB)
    extraction_progress: Mapped[int] = mapped_column(nullable=False, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(String)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
