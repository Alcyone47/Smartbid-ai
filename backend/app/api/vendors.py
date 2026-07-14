import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.projects import _get_org_project
from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.repositories.vendor_repository import VendorRepository
from app.schemas.vendor import VendorCreate, VendorRead

router = APIRouter(prefix="/projects/{project_id}/vendors", tags=["vendors"])


def _to_read(vendor, document_count: int) -> VendorRead:
    return VendorRead(
        id=vendor.id,
        project_id=vendor.project_id,
        name=vendor.name,
        document_count=document_count,
        created_at=vendor.created_at,
    )


@router.get("", response_model=list[VendorRead])
async def list_vendors(
    project_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[VendorRead]:
    await _get_org_project(project_id, current_user.org_id, db)
    vendors = await VendorRepository(db).list_by_project(project_id)
    return [_to_read(vendor, count) for vendor, count in vendors]


@router.post("", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    project_id: uuid.UUID,
    payload: VendorCreate,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> VendorRead:
    """Create (or return the existing) vendor with this name in the project."""
    await _get_org_project(project_id, current_user.org_id, db)
    vendor = await VendorRepository(db).get_or_create(current_user.org_id, project_id, payload.name.strip())
    return _to_read(vendor, 0)


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    project_id: uuid.UUID,
    vendor_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a vendor and everything under it — its uploaded PDFs, extracted specs,
    and compliance rows all cascade-delete via their vendor_id foreign keys."""
    await _get_org_project(project_id, current_user.org_id, db)
    repo = VendorRepository(db)
    vendor = await repo.get_by_id(vendor_id, project_id)
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    await db.delete(vendor)
    await db.commit()
