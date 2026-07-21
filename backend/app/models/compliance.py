import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ComplianceMatrixEntry(Base):
    __tablename__ = "compliance_matrix"
    __table_args__ = (UniqueConstraint("parameter_id", "vendor_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parameter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirement_parameters.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    matched_specification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_specifications.id")
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    match_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class EquipmentMatch(Base):
    """Stage-1 result: the vendor equipment group (if any) that best corresponds to
    one RFP Requirement (equipment), for one vendor. One row per (requirement,
    vendor). Stage 2 (ComplianceMatrixEntry rows) only runs for requirements with
    a "matched" row here — never for "unmatched" ones.
    """

    __tablename__ = "equipment_matches"
    __table_args__ = (UniqueConstraint("requirement_id", "vendor_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_equipment_key: Mapped[str | None] = mapped_column(String)
    matched_equipment_label: Mapped[str | None] = mapped_column(String)
    # Best equipment-similarity score found (0-100), populated even when unmatched
    # (sub-threshold) — the audit trail for why no vendor equipment was paired.
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, server_default=text("0"))
    match_status: Mapped[str] = mapped_column(String, nullable=False)
    vendor_source_page: Mapped[int | None] = mapped_column()
    computed_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
