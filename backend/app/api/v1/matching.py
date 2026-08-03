import uuid
from decimal import Decimal
from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.core.exceptions import AppException
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.models.compliance import ComplianceMatrixEntry, EquipmentMatch
from app.repositories.compliance_repository import ComplianceRepository
from app.repositories.equipment_match_repository import EquipmentMatchRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.repositories.vendor_repository import VendorRepository
from app.schemas.compliance import EquipmentComplianceGroup, VendorComplianceSummaryRead
from app.schemas.optimization import VendorStackOptimizationRead
from app.services.matching import (
    EQUIPMENT_MATCHED,
    ScoredEntry,
    compute_compliance_summary,
    match_equipment,
    match_equipment_parameters,
)
from app.services.matching.compliance_groups import build_equipment_groups as _build_equipment_groups
from app.services.matching.optimization import optimize_vendor_stack
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/projects/{project_id}", tags=["matching"])


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

    # Stage 1: pair each RFP equipment with its best-matching vendor equipment (or
    # mark it unmatched) — persisted so unmatched equipment surfaces on later reads.
    equipment_outcomes = match_equipment(requirements, specifications)
    equipment_rows_to_persist = [
        EquipmentMatch(
            org_id=current_user.org_id,
            project_id=project_id,
            requirement_id=eo.requirement.id,
            vendor_id=vendor_id,
            matched_equipment_key=eo.matched_equipment_key,
            matched_equipment_label=eo.matched_equipment_label,
            confidence_score=Decimal(str(eo.confidence_score)),
            match_status=eo.status,
            vendor_source_page=eo.vendor_source_page,
        )
        for eo in equipment_outcomes
    ]
    equipment_match_repo = EquipmentMatchRepository(db)
    await equipment_match_repo.replace_for_vendor(vendor_id, equipment_rows_to_persist)

    # Stage 2: only for matched equipment, compare its parameters against ONLY its
    # matched vendor equipment's specs — never a fallback to unrelated equipment.
    parameter_outcomes = [
        outcome
        for eo in equipment_outcomes
        if eo.status == EQUIPMENT_MATCHED
        for outcome in match_equipment_parameters(eo.requirement.parameters, eo.matched_specifications)
    ]
    entries = [
        ComplianceMatrixEntry(
            org_id=current_user.org_id,
            project_id=project_id,
            parameter_id=outcome.requirement.id,
            vendor_id=vendor_id,
            matched_specification_id=(
                outcome.matched_specification.id if outcome.matched_specification else None
            ),
            status=outcome.status,
            match_score=outcome.match_score,
            rationale=outcome.rationale,
        )
        for outcome in parameter_outcomes
    ]

    compliance_repo = ComplianceRepository(db)
    await compliance_repo.replace_for_vendor(vendor_id, entries)

    equipment_rows: Sequence[Row] = await equipment_match_repo.list_by_project_with_details(
        project_id, vendor_id
    )
    compliance_rows: Sequence[Row] = await compliance_repo.list_by_project_with_details(
        project_id, vendor_id
    )
    groups = _build_equipment_groups(equipment_rows, compliance_rows)

    scored = [
        ScoredEntry(
            vendor_name=vendor.name,
            status=outcome.status,
            match_score=outcome.match_score,
            is_mandatory=outcome.requirement.is_mandatory,
        )
        for outcome in parameter_outcomes
    ]
    summaries = compute_compliance_summary(scored)
    compliance_pct = summaries[0].overall_compliance_pct if summaries else 0.0
    await NotificationService(db).notify_matching_completed(
        org_id=current_user.org_id, project_id=project_id, vendor_name=vendor.name, compliance_pct=compliance_pct
    )

    return groups


@router.get("/compliance-matrix", response_model=list[EquipmentComplianceGroup])
async def list_compliance_matrix(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[EquipmentComplianceGroup]:
    await _get_org_project(project_id, current_user.org_id, db)
    equipment_match_repo = EquipmentMatchRepository(db)
    compliance_repo = ComplianceRepository(db)
    equipment_rows = await equipment_match_repo.list_by_project_with_details(project_id)
    compliance_rows = await compliance_repo.list_by_project_with_details(project_id)
    return _build_equipment_groups(equipment_rows, compliance_rows)


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
            is_mandatory=parameter.is_mandatory,
        )
        for entry, parameter, _specification, vendor_name in rows
    ]
    summaries = compute_compliance_summary(scored)
    return [VendorComplianceSummaryRead(**vars(summary)) for summary in summaries]


@router.get("/vendor-stack-optimization", response_model=VendorStackOptimizationRead)
async def vendor_stack_optimization(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> VendorStackOptimizationRead:
    """For each equipment item, recommend whichever already-matched vendor scores
    highest, and compute the overall compliance % of that optimized stack.
    Deterministic aggregation over the existing per-vendor match rows — does not
    change or re-run any per-vendor matching/compliance data."""
    await _get_org_project(project_id, current_user.org_id, db)
    equipment_match_repo = EquipmentMatchRepository(db)
    compliance_repo = ComplianceRepository(db)
    equipment_rows = await equipment_match_repo.list_by_project_with_details(project_id)
    compliance_rows = await compliance_repo.list_by_project_with_details(project_id)
    groups = _build_equipment_groups(equipment_rows, compliance_rows)
    result = optimize_vendor_stack(groups)
    return VendorStackOptimizationRead.model_validate(result, from_attributes=True)
