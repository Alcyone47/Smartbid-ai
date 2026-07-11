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
from app.repositories.document_repository import DocumentRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.schemas.compliance import ComplianceMatrixEntryRead, VendorComplianceSummaryRead
from app.services.matching import ScoredEntry, compute_compliance_summary, match_requirements

router = APIRouter(prefix="/projects/{project_id}", tags=["matching"])


def _to_read_schema(row: Row) -> ComplianceMatrixEntryRead:
    entry, requirement, specification, vendor_name = row
    vendor_value = None
    source_page = requirement.source_page
    if specification is not None:
        vendor_value = specification.value or specification.spec_text
        source_page = specification.source_page
    return ComplianceMatrixEntryRead(
        id=entry.id,
        project_id=entry.project_id,
        requirement_id=entry.requirement_id,
        vendor_document_id=entry.vendor_document_id,
        matched_specification_id=entry.matched_specification_id,
        vendor_name=vendor_name,
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
        computed_at=entry.computed_at,
    )


@router.post("/documents/{document_id}/match", response_model=list[ComplianceMatrixEntryRead])
async def trigger_matching(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComplianceMatrixEntryRead]:
    await _get_org_project(project_id, current_user.org_id, db)

    document_repo = DocumentRepository(db)
    vendor_document = await document_repo.get_by_id(document_id, current_user.org_id)
    if vendor_document.doc_type != "vendor_proposal":
        raise AppException(
            "Matching can only be run against a vendor_proposal document",
            error_code="INVALID_DOCUMENT_TYPE",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    requirement_repo = RequirementRepository(db)
    specification_repo = SpecificationRepository(db)
    requirements = await requirement_repo.list_by_project(project_id)
    specifications = await specification_repo.list_by_document(document_id)

    outcomes = match_requirements(requirements, specifications)
    entries = [
        ComplianceMatrixEntry(
            org_id=current_user.org_id,
            project_id=project_id,
            requirement_id=outcome.requirement.id,
            vendor_document_id=document_id,
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
    await compliance_repo.replace_for_vendor_document(document_id, entries)

    rows: Sequence[Row] = await compliance_repo.list_by_project_with_details(project_id, document_id)
    return [_to_read_schema(row) for row in rows]


@router.get("/compliance-matrix", response_model=list[ComplianceMatrixEntryRead])
async def list_compliance_matrix(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComplianceMatrixEntryRead]:
    await _get_org_project(project_id, current_user.org_id, db)
    compliance_repo = ComplianceRepository(db)
    rows = await compliance_repo.list_by_project_with_details(project_id)
    return [_to_read_schema(row) for row in rows]


@router.get("/compliance-summary", response_model=list[VendorComplianceSummaryRead])
async def compliance_summary(
    project_id: uuid.UUID,
    vendor_document_id: uuid.UUID | None = None,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[VendorComplianceSummaryRead]:
    """Deterministic per-vendor compliance rollup computed from the persisted match rows."""
    await _get_org_project(project_id, current_user.org_id, db)
    compliance_repo = ComplianceRepository(db)
    rows = await compliance_repo.list_by_project_with_details(project_id, vendor_document_id)

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
