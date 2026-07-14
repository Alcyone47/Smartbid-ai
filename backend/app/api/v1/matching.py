import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.core.exceptions import AppException
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.models.compliance import ComplianceMatrixEntry
from app.repositories.compliance_repository import ComplianceRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.vendor_repository import VendorRepository
from app.schemas.compliance import (
    EquipmentComplianceGroup,
    EquipmentSpecComparison,
    VendorComplianceSummaryRead,
)
from app.services.matching import ScoredEntry, compute_compliance_summary, match_requirements

router = APIRouter(prefix="/projects/{project_id}", tags=["matching"])


def _to_spec_comparison(row: Row) -> EquipmentSpecComparison:
    entry, requirement, specification, _vendor_name = row
    vendor_value = None
    source_page = requirement.source_page
    if specification is not None:
        vendor_value = specification.value or specification.spec_text
        source_page = specification.source_page
    return EquipmentSpecComparison(
        id=entry.id,
        requirement_id=entry.requirement_id,
        matched_specification_id=entry.matched_specification_id,
        requirement_label=requirement.requirement_label,
        requirement_text=requirement.requirement_text,
        expected_value=requirement.expected_value,
        unit=requirement.unit,
        operator=requirement.operator,
        is_mandatory=requirement.is_mandatory,
        vendor_value=vendor_value,
        source_page=source_page,
        status=entry.status,
        match_score=entry.match_score,
        rationale=entry.rationale,
    )


def _group_by_equipment(rows: Sequence[Row]) -> list[EquipmentComplianceGroup]:
    """Fold flat (entry, requirement, specification, vendor_name) rows into one
    group per (vendor, equipment), computing fractional-credit compliance.
    """
    groups: dict[tuple[uuid.UUID, str], dict] = {}
    order: list[tuple[uuid.UUID, str]] = []
    for row in rows:
        entry, requirement, _specification, vendor_name = row
        key = (entry.vendor_id, requirement.equipment_key)
        if key not in groups:
            groups[key] = {
                "equipment_key": requirement.equipment_key,
                "equipment_label": requirement.equipment_label,
                "vendor_name": vendor_name,
                "vendor_id": entry.vendor_id,
                "credit_sum": 0.0,
                "matched": 0,
                "partial": 0,
                "unmatched": 0,
                "specs": [],
            }
            order.append(key)
        bucket = groups[key]
        bucket["specs"].append(_to_spec_comparison(row))
        bucket["credit_sum"] += float(entry.match_score) if entry.match_score is not None else 0.0
        if entry.status == "match":
            bucket["matched"] += 1
        elif entry.status == "partial":
            bucket["partial"] += 1
        else:
            bucket["unmatched"] += 1

    result: list[EquipmentComplianceGroup] = []
    for key in order:
        bucket = groups[key]
        total = len(bucket["specs"])
        compliance_pct = round(bucket["credit_sum"] / total * 100, 1) if total else 0.0
        result.append(
            EquipmentComplianceGroup(
                equipment_key=bucket["equipment_key"],
                equipment_label=bucket["equipment_label"],
                vendor_name=bucket["vendor_name"],
                vendor_id=bucket["vendor_id"],
                compliance_pct=compliance_pct,
                total_specs=total,
                matched=bucket["matched"],
                partial=bucket["partial"],
                unmatched=bucket["unmatched"],
                specs=bucket["specs"],
            )
        )
    return result


@router.post("/vendors/{vendor_id}/match", response_model=list[EquipmentComplianceGroup])
async def trigger_matching(
    project_id: uuid.UUID,
    vendor_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentComplianceGroup]:
    """Match the RFP against a vendor's combined specifications (across all of its
    uploaded PDFs) and persist one compliance row per requirement for the vendor."""
    await _get_org_project(project_id, current_user.org_id, db)

    vendor_repo = VendorRepository(db)
    vendor = await vendor_repo.get_by_id(vendor_id, project_id)
    if vendor is None:
        raise AppException(
            "Vendor not found",
            error_code="VENDOR_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    requirement_repo = RequirementRepository(db)
    specification_repo = SpecificationRepository(db)
    requirements = await requirement_repo.list_by_project(project_id)
    specifications = await specification_repo.list_by_vendor(vendor_id)

    outcomes = match_requirements(requirements, specifications)
    entries = [
        ComplianceMatrixEntry(
            org_id=current_user.org_id,
            project_id=project_id,
            requirement_id=outcome.requirement.id,
            vendor_id=vendor_id,
            matched_specification_id=(
                outcome.matched_specification.id if outcome.matched_specification else None
            ),
            status=outcome.status,
            match_score=outcome.match_score,
            rationale=outcome.rationale,
        )
        for outcome in outcomes
    ]

    compliance_repo = ComplianceRepository(db)
    await compliance_repo.replace_for_vendor(vendor_id, entries)

    rows: Sequence[Row] = await compliance_repo.list_by_project_with_details(project_id, vendor_id)
    return _group_by_equipment(rows)


@router.get("/compliance-matrix", response_model=list[EquipmentComplianceGroup])
async def list_compliance_matrix(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentComplianceGroup]:
    await _get_org_project(project_id, current_user.org_id, db)
    compliance_repo = ComplianceRepository(db)
    rows = await compliance_repo.list_by_project_with_details(project_id)
    return _group_by_equipment(rows)


@router.get("/compliance-summary", response_model=list[VendorComplianceSummaryRead])
async def compliance_summary(
    project_id: uuid.UUID,
    vendor_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[VendorComplianceSummaryRead]:
    """Deterministic per-vendor compliance rollup computed from the persisted match rows."""
    await _get_org_project(project_id, current_user.org_id, db)
    compliance_repo = ComplianceRepository(db)
    rows = await compliance_repo.list_by_project_with_details(project_id, vendor_id)

    scored = [
        ScoredEntry(
            vendor_name=vendor_name,
            status=entry.status,
            match_score=entry.match_score,
            is_mandatory=requirement.is_mandatory,
        )
        for entry, requirement, _specification, vendor_name in rows
    ]
    summaries = compute_compliance_summary(scored)
    return [VendorComplianceSummaryRead(**vars(summary)) for summary in summaries]
