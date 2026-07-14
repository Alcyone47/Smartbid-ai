import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.models.extraction import ExtractedRequirement

# Heavy columns never read on the request path (matching/serialization). Skipping
# them keeps reads small — the audit blob `raw_llm_response` is duplicated onto every
# row and can be megabytes, which otherwise blows past the DB statement timeout.
_DEFERRED_COLUMNS = (
    defer(ExtractedRequirement.embedding),
    defer(ExtractedRequirement.raw_llm_response),
    defer(ExtractedRequirement.source_span),
)


class RequirementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, requirements: list[ExtractedRequirement]) -> None:
        self._db.add_all(requirements)
        await self._db.commit()

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Clear a document's requirements so re-extraction is idempotent (no duplicates)."""
        await self._db.execute(
            delete(ExtractedRequirement).where(ExtractedRequirement.document_id == document_id)
        )
        await self._db.commit()

    async def list_by_document(self, document_id: uuid.UUID) -> list[ExtractedRequirement]:
        result = await self._db.execute(
            select(ExtractedRequirement)
            .where(ExtractedRequirement.document_id == document_id)
            .options(*_DEFERRED_COLUMNS)
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: uuid.UUID) -> list[ExtractedRequirement]:
        result = await self._db.execute(
            select(ExtractedRequirement)
            .where(ExtractedRequirement.project_id == project_id)
            .options(*_DEFERRED_COLUMNS)
        )
        return list(result.scalars().all())
