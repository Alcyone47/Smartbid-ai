"""Fold persisted Stage-1/Stage-2 match rows into per-(vendor, equipment) groups.

Moved as-is from the API layer (backend/app/api/v1/matching.py) so both the
compliance-matrix endpoint and vendor stack optimization can share it without
services importing from the API layer.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import Row

from app.schemas.compliance import EquipmentComplianceGroup, EquipmentSpecComparison


def _to_spec_comparison(row: Row) -> EquipmentSpecComparison:
    entry, parameter, specification, _vendor_name = row
    vendor_value = None
    source_page = parameter.source_page
    if specification is not None:
        vendor_value = specification.value or specification.spec_text
        source_page = specification.source_page
    return EquipmentSpecComparison(
        id=entry.id,
        requirement_id=entry.parameter_id,
        matched_specification_id=entry.matched_specification_id,
        requirement_label=parameter.parameter_label,
        requirement_text=parameter.parameter_text,
        expected_value=parameter.expected_value,
        unit=parameter.unit,
        operator=parameter.operator,
        is_mandatory=parameter.is_mandatory,
        vendor_value=vendor_value,
        source_page=source_page,
        status=entry.status,
        match_score=entry.match_score,
        rationale=entry.rationale,
    )


def build_equipment_groups(
    equipment_rows: Sequence[Row], compliance_rows: Sequence[Row]
) -> list[EquipmentComplianceGroup]:
    """Fold Stage-1 EquipmentMatch rows (one per requirement/vendor, including
    unmatched equipment with zero specs) together with Stage-2 compliance rows
    (keyed by vendor + requirement) into one group per (vendor, equipment).
    """
    specs_by_group: dict[tuple[uuid.UUID, uuid.UUID], list[EquipmentSpecComparison]] = {}
    for row in compliance_rows:
        entry, parameter, _specification, _vendor_name = row
        key = (entry.vendor_id, parameter.requirement_id)
        specs_by_group.setdefault(key, []).append(_to_spec_comparison(row))

    result: list[EquipmentComplianceGroup] = []
    for equipment_match, requirement, vendor_name in equipment_rows:
        specs = specs_by_group.get((equipment_match.vendor_id, requirement.id), [])
        total = len(specs)
        credit_sum = sum(float(s.match_score) if s.match_score is not None else 0.0 for s in specs)
        matched = sum(1 for s in specs if s.status == "match")
        partial = sum(1 for s in specs if s.status == "partial")
        unmatched = sum(1 for s in specs if s.status not in ("match", "partial"))
        compliance_pct = round(credit_sum / total * 100, 1) if total else 0.0
        result.append(
            EquipmentComplianceGroup(
                equipment_key=requirement.equipment_key,
                equipment_label=requirement.equipment_label,
                vendor_name=vendor_name,
                vendor_id=equipment_match.vendor_id,
                match_status=equipment_match.match_status,
                equipment_match_confidence=float(equipment_match.confidence_score),
                compliance_pct=compliance_pct,
                total_specs=total,
                matched=matched,
                partial=partial,
                unmatched=unmatched,
                specs=specs,
            )
        )
    return result
