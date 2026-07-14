import uuid
from typing import Sequence

from sqlalchemy import Row, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.models.compliance import ComplianceMatrixEntry
from app.models.extraction import ExtractedSpecification, RequirementParameter
from app.models.vendor import Vendor

# Heavy columns (embedding vector + audit blob) that no request-path consumer
# reads. Deferring them keeps the matrix/summary/report joins from timing out.
_DEFERRED_COLUMNS = (
    defer(RequirementParameter.embedding),
    defer(RequirementParameter.source_span),
    defer(ExtractedSpecification.embedding),
    defer(ExtractedSpecification.raw_llm_response),
    defer(ExtractedSpecification.source_span),
)


class ComplianceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def replace_for_vendor(
        self, vendor_id: uuid.UUID, entries: list[ComplianceMatrixEntry]
    ) -> None:
        await self._db.execute(
            delete(ComplianceMatrixEntry).where(ComplianceMatrixEntry.vendor_id == vendor_id)
        )
        self._db.add_all(entries)
        await self._db.commit()

    async def list_by_project_with_details(
        self, project_id: uuid.UUID, vendor_id: uuid.UUID | None = None
    ) -> Sequence[Row]:
        stmt = (
            select(ComplianceMatrixEntry, RequirementParameter, ExtractedSpecification, Vendor.name)
            .join(RequirementParameter, ComplianceMatrixEntry.parameter_id == RequirementParameter.id)
            .outerjoin(
                ExtractedSpecification,
                ComplianceMatrixEntry.matched_specification_id == ExtractedSpecification.id,
            )
            .join(Vendor, ComplianceMatrixEntry.vendor_id == Vendor.id)
            .where(ComplianceMatrixEntry.project_id == project_id)
            .options(*_DEFERRED_COLUMNS)
        )
        if vendor_id is not None:
            stmt = stmt.where(ComplianceMatrixEntry.vendor_id == vendor_id)
        result = await self._db.execute(stmt)
        return result.all()
