import re
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.core.exceptions import AppException
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.repositories.compliance_repository import ComplianceRepository
from app.services.matching import ScoredEntry, compute_compliance_summary
from app.services.reports import (
    build_report_rows,
    generate_matrix_csv,
    generate_matrix_xlsx,
    generate_summary_pdf,
)

router = APIRouter(prefix="/projects/{project_id}", tags=["reports"])

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower() or "project"


def _attachment(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _load_report_data(project_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession):
    project = await _get_org_project(project_id, current_user.org_id, db)
    rows = await ComplianceRepository(db).list_by_project_with_details(project_id)
    if not rows:
        raise AppException(
            "No compliance results for this project yet. Run matching first.",
            error_code="NO_COMPLIANCE_RESULTS",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    report_rows = build_report_rows(rows)
    scored = [
        ScoredEntry(vendor_name=vendor_name, status=entry.status, match_score=entry.match_score, is_mandatory=req.is_mandatory)
        for entry, req, _spec, vendor_name in rows
    ]
    summaries = compute_compliance_summary(scored)
    return project, report_rows, summaries


@router.get("/reports/matrix.xlsx")
async def download_matrix_xlsx(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    project, rows, summaries = await _load_report_data(project_id, current_user, db)
    content = generate_matrix_xlsx(project, rows, summaries)
    return _attachment(content, _XLSX_MIME, f"{_slug(project.name)}-compliance-{date.today().isoformat()}.xlsx")


@router.get("/reports/matrix.csv")
async def download_matrix_csv(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    project, rows, _summaries = await _load_report_data(project_id, current_user, db)
    content = generate_matrix_csv(rows)
    return _attachment(content, "text/csv", f"{_slug(project.name)}-compliance-{date.today().isoformat()}.csv")


@router.get("/reports/summary.pdf")
async def download_summary_pdf(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    project, rows, summaries = await _load_report_data(project_id, current_user, db)
    content = generate_summary_pdf(project, summaries, rows)
    return _attachment(content, "application/pdf", f"{_slug(project.name)}-compliance-{date.today().isoformat()}.pdf")
