import uuid
from typing import Sequence

from sqlalchemy import Row, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance import ComplianceMatrixEntry
from app.models.document import Document
from app.models.extraction import ExtractedRequirement, ExtractedSpecification


class ComplianceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def replace_for_vendor_document(
        self, vendor_document_id: uuid.UUID, entries: list[ComplianceMatrixEntry]
    ) -> None:
        await self._db.execute(
            delete(ComplianceMatrixEntry).where(ComplianceMatrixEntry.vendor_document_id == vendor_document_id)
        )
        self._db.add_all(entries)
        await self._db.commit()

    async def list_by_project_with_details(
        self, project_id: uuid.UUID, vendor_document_id: uuid.UUID | None = None
    ) -> Sequence[Row]:
        stmt = (
            select(ComplianceMatrixEntry, ExtractedRequirement, ExtractedSpecification, Document.vendor_name)
            .join(ExtractedRequirement, ComplianceMatrixEntry.requirement_id == ExtractedRequirement.id)
            .outerjoin(
                ExtractedSpecification,
                ComplianceMatrixEntry.matched_specification_id == ExtractedSpecification.id,
            )
            .join(Document, ComplianceMatrixEntry.vendor_document_id == Document.id)
            .where(ComplianceMatrixEntry.project_id == project_id)
        )
        if vendor_document_id is not None:
            stmt = stmt.where(ComplianceMatrixEntry.vendor_document_id == vendor_document_id)
        result = await self._db.execute(stmt)
        return result.all()
