"""Flatten persisted compliance rows into a plain shape the report generators render.

Pure data adaptation — no DB, no LLM. Mirrors the derivations used by the
compliance-matrix API (`vendor_value = spec.value or spec.spec_text`; the spec's
page is preferred over the requirement's) and additionally exposes ``category``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class ReportRow:
    equipment_key: str
    equipment_label: str
    requirement_label: str
    requirement_text: str
    category: str | None
    is_mandatory: bool
    expected_value: str | None
    unit: str | None
    operator: str | None
    vendor_name: str
    vendor_value: str | None
    status: str
    compliance_pct: int
    rationale: str
    source_page: int | None


def build_report_rows(rows: Iterable[Sequence]) -> list[ReportRow]:
    """Adapt ``ComplianceRepository.list_by_project_with_details`` tuples.

    Each row is ``(ComplianceMatrixEntry, ExtractedRequirement,
    ExtractedSpecification | None, vendor_name)``.
    """
    report_rows: list[ReportRow] = []
    for entry, requirement, specification, vendor_name in rows:
        vendor_value = None
        source_page = requirement.source_page
        if specification is not None:
            vendor_value = specification.value or specification.spec_text
            source_page = specification.source_page
        report_rows.append(
            ReportRow(
                equipment_key=requirement.equipment_key,
                equipment_label=requirement.equipment_label,
                requirement_label=requirement.requirement_label,
                requirement_text=requirement.requirement_text,
                category=requirement.category,
                is_mandatory=requirement.is_mandatory,
                expected_value=requirement.expected_value,
                unit=requirement.unit,
                operator=requirement.operator,
                vendor_name=vendor_name,
                vendor_value=vendor_value,
                status=entry.status,
                compliance_pct=round(float(entry.match_score or 0) * 100),
                rationale=entry.rationale,
                source_page=source_page,
            )
        )
    # Group rows so each vendor's equipment items are contiguous in the reports.
    report_rows.sort(key=lambda r: (r.vendor_name, r.equipment_label, r.requirement_label))
    return report_rows


STATUS_LABELS = {"match": "Match", "partial": "Partial", "no_match": "No Match"}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)
