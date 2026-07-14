import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.repositories.document_repository import DocumentRepository
from app.repositories.requirement_repository import RequirementRepository
from app.repositories.specification_repository import SpecificationRepository
from app.schemas.document import DocumentRead
from app.schemas.extraction import ExtractedSpecificationRead, RequirementRead
from app.workers.document_tasks import process_document

router = APIRouter(prefix="/projects/{project_id}/documents/{document_id}", tags=["extraction"])


@router.post("/extract", response_model=DocumentRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_extraction(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    await _get_org_project(project_id, current_user.org_id, db)
    document_repo = DocumentRepository(db)
    document = await document_repo.get_by_id(document_id, current_user.org_id)

    await document_repo.update_status(document, status="queued", progress=0)
    process_document.delay(str(document.id))
    return document


@router.get("/requirements", response_model=list[RequirementRead])
async def list_requirements(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[RequirementRead]:
    await _get_org_project(project_id, current_user.org_id, db)
    document_repo = DocumentRepository(db)
    await document_repo.get_by_id(document_id, current_user.org_id)
    requirement_repo = RequirementRepository(db)
    return await requirement_repo.list_by_document(document_id)


@router.get("/specifications", response_model=list[ExtractedSpecificationRead])
async def list_specifications(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[ExtractedSpecificationRead]:
    await _get_org_project(project_id, current_user.org_id, db)
    document_repo = DocumentRepository(db)
    await document_repo.get_by_id(document_id, current_user.org_id)
    specification_repo = SpecificationRepository(db)
    return await specification_repo.list_by_document(document_id)
