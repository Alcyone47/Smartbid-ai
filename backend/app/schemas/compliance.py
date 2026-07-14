import uuid
from decimal import Decimal

from pydantic import BaseModel


class EquipmentSpecComparison(BaseModel):
    """One required-spec vs vendor-spec comparison within an equipment group."""

    id: uuid.UUID
    requirement_id: uuid.UUID
    matched_specification_id: uuid.UUID | None
    requirement_label: str
    requirement_text: str
    expected_value: str | None
    unit: str | None
    operator: str | None
    is_mandatory: bool
    vendor_value: str | None
    source_page: int | None
    status: str
    match_score: Decimal | None
    rationale: str


class EquipmentComplianceGroup(BaseModel):
    """One equipment/item for a vendor, with its per-spec comparisons and overall compliance."""

    equipment_key: str
    equipment_label: str
    vendor_name: str
    vendor_id: uuid.UUID
    compliance_pct: float
    total_specs: int
    matched: int
    partial: int
    unmatched: int
    specs: list[EquipmentSpecComparison]


class VendorComplianceSummaryRead(BaseModel):
    vendor_name: str
    overall_compliance_pct: float
    total_requirements: int
    matched: int
    partial: int
    unmatched: int
    mandatory_total: int
    mandatory_met: int
    mandatory_partial: int
    mandatory_unmet: int
    optional_total: int
    optional_met: int
    optional_partial: int
    optional_unmet: int
