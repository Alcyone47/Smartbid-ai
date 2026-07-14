import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, selectinload

from app.models.extraction import Requirement, RequirementParameter

# Heavy columns never read on the request path (matching/serialization). Skipping
# them keeps reads small — the audit blob `raw_llm_response` can be megabytes,
# which otherwise blows past the DB statement timeout. It now lives on the parent
# requirement; the embedding/span vectors live on each parameter.
_DEFERRED_PARENT_COLUMNS = (defer(Requirement.raw_llm_response),)
_PARAMETER_LOAD = selectinload(Requirement.parameters).options(
    defer(RequirementParameter.embedding),
    defer(RequirementParameter.source_span),
)


class RequirementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, requirements: list[Requirement]) -> None:
        """Persist parent requirements together with their child parameters
        (the ``parameters`` relationship cascades the inserts)."""
        self._db.add_all(requirements)
        await self._db.commit()

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Clear a document's requirements so re-extraction is idempotent. Child
        parameters are removed by the FK ``ON DELETE CASCADE``."""
        await self._db.execute(
            delete(Requirement).where(Requirement.document_id == document_id)
        )
        await self._db.commit()

    async def list_by_document(self, document_id: uuid.UUID) -> list[Requirement]:
        result = await self._db.execute(
            select(Requirement)
            .where(Requirement.document_id == document_id)
            .options(*_DEFERRED_PARENT_COLUMNS, _PARAMETER_LOAD)
            .order_by(Requirement.created_at)
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: uuid.UUID) -> list[Requirement]:
        result = await self._db.execute(
            select(Requirement)
            .where(Requirement.project_id == project_id)
            .options(*_DEFERRED_PARENT_COLUMNS, _PARAMETER_LOAD)
            .order_by(Requirement.created_at)
        )
        return list(result.scalars().all())
