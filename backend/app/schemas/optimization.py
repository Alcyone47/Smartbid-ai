import uuid

from pydantic import BaseModel


class VendorCandidateRead(BaseModel):
    """One vendor's compliance for a single equipment item, considered during
    stack optimization."""

    vendor_id: uuid.UUID
    vendor_name: str
    compliance_pct: float
    match_status: str
    equipment_match_confidence: float | None


class OptimizedEquipmentSelectionRead(BaseModel):
    """The recommended vendor for one equipment item, plus the ranked candidates
    it was chosen from (explainability)."""

    equipment_key: str
    equipment_label: str
    best_vendor_id: uuid.UUID | None
    best_vendor_name: str | None
    compliance_pct: float
    match_status: str
    total_specs: int
    matched: int
    partial: int
    unmatched: int
    candidates: list[VendorCandidateRead]


class VendorUsageRead(BaseModel):
    """How many equipment items in the recommended stack come from each vendor."""

    vendor_id: uuid.UUID
    vendor_name: str
    equipment_count: int


class VendorStackOptimizationRead(BaseModel):
    equipment: list[OptimizedEquipmentSelectionRead]
    overall_optimized_compliance_pct: float
    vendor_usage: list[VendorUsageRead]
