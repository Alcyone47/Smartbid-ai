import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotFoundError
from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, document_id: uuid.UUID, org_id: uuid.UUID) -> Document:
        result = await self._db.execute(
            select(Document).where(Document.id == document_id, Document.org_id == org_id)
        )
        document = result.scalars().first()
        if document is None:
            raise DocumentNotFoundError()
        return document

    async def get_by_id_unscoped(self, document_id: uuid.UUID) -> Document:
        """Used by the background worker, which has no request-scoped org context."""
        result = await self._db.execute(select(Document).where(Document.id == document_id))
        document = result.scalars().first()
        if document is None:
            raise DocumentNotFoundError()
        return document

    async def update_status(
        self, document: Document, status: str, error_message: str | None = None, progress: int | None = None
    ) -> None:
        document.status = status
        document.error_message = error_message
        if progress is not None:
            document.extraction_progress = progress
        await self._db.commit()

    async def update_progress(self, document: Document, progress: int) -> None:
        document.extraction_progress = progress
        await self._db.commit()

    async def update_page_count(self, document: Document, page_count: int) -> None:
        document.page_count = page_count
        await self._db.commit()
