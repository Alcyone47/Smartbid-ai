import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extraction import ExtractedRequirement


class RequirementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, requirements: list[ExtractedRequirement]) -> None:
        self._db.add_all(requirements)
        await self._db.commit()

    async def list_by_document(self, document_id: uuid.UUID) -> list[ExtractedRequirement]:
        result = await self._db.execute(
            select(ExtractedRequirement).where(ExtractedRequirement.document_id == document_id)
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: uuid.UUID) -> list[ExtractedRequirement]:
        result = await self._db.execute(
            select(ExtractedRequirement).where(ExtractedRequirement.project_id == project_id)
        )
        return list(result.scalars().all())
