import uuid
from typing import Sequence

from sqlalchemy import Row, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.models.compliance import EquipmentMatch
from app.models.extraction import Requirement
from app.models.vendor import Vendor


class EquipmentMatchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def replace_for_vendor(self, vendor_id: uuid.UUID, matches: list[EquipmentMatch]) -> None:
        await self._db.execute(delete(EquipmentMatch).where(EquipmentMatch.vendor_id == vendor_id))
        self._db.add_all(matches)
        await self._db.commit()

    async def list_by_project_with_details(
        self, project_id: uuid.UUID, vendor_id: uuid.UUID | None = None
    ) -> Sequence[Row]:
        """(EquipmentMatch, Requirement, Vendor.name) rows — the source of equipment
        groups for the compliance matrix, including equipment Stage 1 marked
        unmatched (which have zero ComplianceMatrixEntry rows and would otherwise
        be invisible to a spec-row-driven query)."""
        stmt = (
            select(EquipmentMatch, Requirement, Vendor.name)
            .join(Requirement, EquipmentMatch.requirement_id == Requirement.id)
            .join(Vendor, EquipmentMatch.vendor_id == Vendor.id)
            .where(EquipmentMatch.project_id == project_id)
            .options(defer(Requirement.raw_llm_response))
            .order_by(Requirement.created_at)
        )
        if vendor_id is not None:
            stmt = stmt.where(EquipmentMatch.vendor_id == vendor_id)
        result = await self._db.execute(stmt)
        return result.all()
