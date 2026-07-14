import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.models.compliance import ComplianceMatrixEntry
from app.models.document import Document
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.project_status import derive_project_status

router = APIRouter(prefix="/projects", tags=["projects"])

_EXTRACTED = "extracted"


async def _get_org_project(project_id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id, Project.org_id == org_id))
    project = result.scalars().first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _apply_derived_status(db: AsyncSession, projects: list[Project]) -> None:
    """Overwrite each project's ``status`` with a value derived from its documents and
    compliance state. Mutation is in-memory only (never committed) — status is a
    read-time projection, not stored state.
    """
    project_ids = [p.id for p in projects]
    if not project_ids:
        return

    doc_rows = (
        await db.execute(
            select(Document.project_id, Document.doc_type, Document.status).where(
                Document.project_id.in_(project_ids)
            )
        )
    ).all()
    matrix_ids = set(
        (
            await db.execute(
                select(distinct(ComplianceMatrixEntry.project_id)).where(
                    ComplianceMatrixEntry.project_id.in_(project_ids)
                )
            )
        )
        .scalars()
        .all()
    )

    has_docs: dict[uuid.UUID, bool] = {}
    rfp_extracted: dict[uuid.UUID, bool] = {}
    vendor_extracted: dict[uuid.UUID, bool] = {}
    for pid, doc_type, doc_status in doc_rows:
        has_docs[pid] = True
        if doc_status == _EXTRACTED and doc_type == "rfp":
            rfp_extracted[pid] = True
        if doc_status == _EXTRACTED and doc_type == "vendor_proposal":
            vendor_extracted[pid] = True

    for project in projects:
        # A manual override wins; otherwise fall back to the derived status.
        project.status = project.status_override or derive_project_status(
            has_documents=has_docs.get(project.id, False),
            rfp_extracted=rfp_extracted.get(project.id, False),
            vendor_extracted=vendor_extracted.get(project.id, False),
            has_matrix=project.id in matrix_ids,
        )


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    result = await db.execute(
        select(Project).where(Project.org_id == current_user.org_id).order_by(Project.created_at.desc())
    )
    projects = list(result.scalars().all())
    await _apply_derived_status(db, projects)
    return projects


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = Project(
        org_id=current_user.org_id,
        name=payload.name,
        client_name=payload.client_name,
        created_by=current_user.user_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await _get_org_project(project_id, current_user.org_id, db)
    await _apply_derived_status(db, [project])
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await _get_org_project(project_id, current_user.org_id, db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    await _apply_derived_status(db, [project])
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    project = await _get_org_project(project_id, current_user.org_id, db)
    await db.delete(project)
    await db.commit()
