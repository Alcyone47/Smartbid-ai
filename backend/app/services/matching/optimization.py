"""Vendor stack optimization: pick the best-performing vendor per equipment item
and roll that up into an overall optimized project compliance %.

Pure aggregation over already-computed ``EquipmentComplianceGroup`` rows (one row
per vendor per equipment, produced by
``app.services.matching.compliance_groups.build_equipment_groups``) — no LLM, no
DB, no re-matching. Existing per-vendor matching/compliance data is read-only
input here and is never modified.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.schemas.compliance import EquipmentComplianceGroup
from app.services.matching.scoring import ScoredEntry, compute_compliance_summary

_OPTIMIZED_STACK_LABEL = "__optimized_stack__"


@dataclass(frozen=True)
class VendorCandidate:
    vendor_id: uuid.UUID
    vendor_name: str
    compliance_pct: float
    match_status: str
    equipment_match_confidence: float | None


@dataclass(frozen=True)
class OptimizedEquipmentSelection:
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
    candidates: list[VendorCandidate]


@dataclass(frozen=True)
class VendorUsage:
    vendor_id: uuid.UUID
    vendor_name: str
    equipment_count: int


@dataclass
class VendorStackOptimizationResult:
    equipment: list[OptimizedEquipmentSelection]
    overall_optimized_compliance_pct: float
    vendor_usage: list[VendorUsage]


def _rank_key(candidate: VendorCandidate) -> tuple:
    """Ascending sort key whose lowest value is the most preferred candidate:
    higher compliance % wins, then a "matched" equipment pairing beats
    "unmatched", then higher equipment-match confidence, then vendor name
    ascending (deterministic tie-break — never random)."""
    return (
        -candidate.compliance_pct,
        candidate.match_status != "matched",
        -(candidate.equipment_match_confidence or 0.0),
        candidate.vendor_name.lower(),
    )


def optimize_vendor_stack(groups: list[EquipmentComplianceGroup]) -> VendorStackOptimizationResult:
    """Group per-(vendor, equipment) compliance rows by equipment, select the
    highest-scoring vendor for each, and compute the overall compliance % of the
    resulting recommended vendor stack."""
    by_equipment: dict[str, list[EquipmentComplianceGroup]] = {}
    order: list[str] = []
    for group in groups:
        if group.equipment_key not in by_equipment:
            order.append(group.equipment_key)
        by_equipment.setdefault(group.equipment_key, []).append(group)

    selections: list[OptimizedEquipmentSelection] = []
    selected_scored_entries: list[ScoredEntry] = []
    usage_counts: dict[uuid.UUID, VendorUsage] = {}

    for equipment_key in order:
        equipment_groups = by_equipment[equipment_key]
        candidates = [
            VendorCandidate(
                vendor_id=g.vendor_id,
                vendor_name=g.vendor_name,
                compliance_pct=g.compliance_pct,
                match_status=g.match_status,
                equipment_match_confidence=g.equipment_match_confidence,
            )
            for g in equipment_groups
        ]
        ranked = sorted(candidates, key=_rank_key)
        best_candidate = ranked[0]
        best_group = next(g for g in equipment_groups if g.vendor_id == best_candidate.vendor_id)

        if best_candidate.match_status == "matched":
            selections.append(
                OptimizedEquipmentSelection(
                    equipment_key=equipment_key,
                    equipment_label=best_group.equipment_label,
                    best_vendor_id=best_group.vendor_id,
                    best_vendor_name=best_group.vendor_name,
                    compliance_pct=best_group.compliance_pct,
                    match_status=best_group.match_status,
                    total_specs=best_group.total_specs,
                    matched=best_group.matched,
                    partial=best_group.partial,
                    unmatched=best_group.unmatched,
                    candidates=ranked,
                )
            )
            selected_scored_entries.extend(
                ScoredEntry(
                    vendor_name=_OPTIMIZED_STACK_LABEL,
                    status=spec.status,
                    match_score=spec.match_score,
                    is_mandatory=spec.is_mandatory,
                )
                for spec in best_group.specs
            )
            usage = usage_counts.get(best_group.vendor_id)
            if usage is None:
                usage_counts[best_group.vendor_id] = VendorUsage(
                    vendor_id=best_group.vendor_id, vendor_name=best_group.vendor_name, equipment_count=1
                )
            else:
                usage_counts[best_group.vendor_id] = VendorUsage(
                    vendor_id=usage.vendor_id,
                    vendor_name=usage.vendor_name,
                    equipment_count=usage.equipment_count + 1,
                )
        else:
            # No vendor's equipment pairing cleared the matching threshold at all —
            # nothing to recommend for this equipment; excluded from the weighted
            # score, mirroring how unmatched equipment already behaves in the
            # existing per-vendor compliance summary.
            selections.append(
                OptimizedEquipmentSelection(
                    equipment_key=equipment_key,
                    equipment_label=best_group.equipment_label,
                    best_vendor_id=None,
                    best_vendor_name=None,
                    compliance_pct=0.0,
                    match_status="unmatched",
                    total_specs=0,
                    matched=0,
                    partial=0,
                    unmatched=0,
                    candidates=ranked,
                )
            )

    summaries = compute_compliance_summary(selected_scored_entries)
    overall_pct = summaries[0].overall_compliance_pct if summaries else 0.0

    vendor_usage = sorted(usage_counts.values(), key=lambda u: (-u.equipment_count, u.vendor_name.lower()))

    return VendorStackOptimizationResult(
        equipment=selections,
        overall_optimized_compliance_pct=overall_pct,
        vendor_usage=vendor_usage,
    )
