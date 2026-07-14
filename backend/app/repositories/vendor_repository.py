import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.vendor import Vendor


class VendorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, vendor_id: uuid.UUID, project_id: uuid.UUID) -> Vendor | None:
        result = await self._db.execute(
            select(Vendor).where(Vendor.id == vendor_id, Vendor.project_id == project_id)
        )
        return result.scalars().first()

    async def get_by_name(self, project_id: uuid.UUID, name: str) -> Vendor | None:
        result = await self._db.execute(
            select(Vendor).where(Vendor.project_id == project_id, Vendor.name == name)
        )
        return result.scalars().first()

    async def get_or_create(self, org_id: uuid.UUID, project_id: uuid.UUID, name: str) -> Vendor:
        """Return the project's vendor with this name, creating it if absent.

        Vendor identity within a project is the name, so uploading another PDF for
        an existing vendor name attaches it to the same vendor.
        """
        existing = await self.get_by_name(project_id, name)
        if existing is not None:
            return existing
        vendor = Vendor(org_id=org_id, project_id=project_id, name=name)
        self._db.add(vendor)
        await self._db.commit()
        await self._db.refresh(vendor)
        return vendor

    async def list_by_project(self, project_id: uuid.UUID) -> list[tuple[Vendor, int]]:
        """Vendors for a project, each with its document (PDF) count."""
        result = await self._db.execute(
            select(Vendor, func.count(Document.id))
            .outerjoin(Document, Document.vendor_id == Vendor.id)
            .where(Vendor.project_id == project_id)
            .group_by(Vendor.id)
            .order_by(Vendor.created_at.asc())
        )
        return [(vendor, count) for vendor, count in result.all()]
