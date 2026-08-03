import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org import Org, OrgMember


class OrgRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Org | None:
        result = await self._db.execute(select(Org).where(Org.id == org_id))
        return result.scalars().first()

    async def get_membership(self, org_id: uuid.UUID, user_id: uuid.UUID) -> OrgMember | None:
        result = await self._db.execute(
            select(OrgMember).where(OrgMember.org_id == org_id, OrgMember.user_id == user_id)
        )
        return result.scalars().first()

    async def count_members(self, org_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(OrgMember).where(OrgMember.org_id == org_id)
        )
        return result.scalar_one()
