"""Deterministic requirement↔specification matching engine.

Public surface for the rest of the app. Never calls the LLM.
"""

from app.services.matching.engine import MatchOutcome, evaluate_requirement, match_requirements
from app.services.matching.scoring import (
    ScoredEntry,
    VendorComplianceSummary,
    compute_compliance_summary,
)

__all__ = [
    "MatchOutcome",
    "evaluate_requirement",
    "match_requirements",
    "ScoredEntry",
    "VendorComplianceSummary",
    "compute_compliance_summary",
]
