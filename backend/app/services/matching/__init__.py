"""Deterministic requirement↔specification matching engine.

Public surface for the rest of the app. Never calls the LLM.
"""

from app.services.matching.engine import (
    EQUIPMENT_MATCHED,
    EQUIPMENT_UNMATCHED,
    EquipmentMatchOutcome,
    MatchOutcome,
    evaluate_requirement,
    match_equipment,
    match_equipment_parameters,
    match_requirements,
)
from app.services.matching.scoring import (
    ScoredEntry,
    VendorComplianceSummary,
    compute_compliance_summary,
)

__all__ = [
    "EQUIPMENT_MATCHED",
    "EQUIPMENT_UNMATCHED",
    "EquipmentMatchOutcome",
    "MatchOutcome",
    "evaluate_requirement",
    "match_equipment",
    "match_equipment_parameters",
    "match_requirements",
    "ScoredEntry",
    "VendorComplianceSummary",
    "compute_compliance_summary",
]
