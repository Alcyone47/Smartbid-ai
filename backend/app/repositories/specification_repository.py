import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extraction import ExtractedSpecification


class SpecificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, specifications: list[ExtractedSpecification]) -> None:
        self._db.add_all(specifications)
        await self._db.commit()

    async def list_by_document(self, document_id: uuid.UUID) -> list[ExtractedSpecification]:
        result = await self._db.execute(
            select(ExtractedSpecification).where(ExtractedSpecification.document_id == document_id)
        )
        return list(result.scalars().all())
