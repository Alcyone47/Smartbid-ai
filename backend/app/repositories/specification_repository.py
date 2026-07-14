import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.models.extraction import ExtractedSpecification

# See RequirementRepository: skip heavy columns unused on the request path.
_DEFERRED_COLUMNS = (
    defer(ExtractedSpecification.embedding),
    defer(ExtractedSpecification.raw_llm_response),
    defer(ExtractedSpecification.source_span),
)


class SpecificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, specifications: list[ExtractedSpecification]) -> None:
        self._db.add_all(specifications)
        await self._db.commit()

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Clear a document's specifications so re-extraction is idempotent (no duplicates)."""
        await self._db.execute(
            delete(ExtractedSpecification).where(ExtractedSpecification.document_id == document_id)
        )
        await self._db.commit()

    async def list_by_document(self, document_id: uuid.UUID) -> list[ExtractedSpecification]:
        result = await self._db.execute(
            select(ExtractedSpecification)
            .where(ExtractedSpecification.document_id == document_id)
            .options(*_DEFERRED_COLUMNS)
        )
        return list(result.scalars().all())

    async def list_by_vendor(self, vendor_id: uuid.UUID) -> list[ExtractedSpecification]:
        """All specs across every document belonging to a vendor — the combined pool
        matched against the RFP for that vendor."""
        result = await self._db.execute(
            select(ExtractedSpecification)
            .where(ExtractedSpecification.vendor_id == vendor_id)
            .options(*_DEFERRED_COLUMNS)
        )
        return list(result.scalars().all())
