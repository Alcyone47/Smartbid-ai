import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ComplianceMatrixEntry(Base):
    __tablename__ = "compliance_matrix"
    __table_args__ = (UniqueConstraint("requirement_id", "vendor_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_requirements.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    matched_specification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_specifications.id")
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
