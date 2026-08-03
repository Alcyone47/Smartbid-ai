import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self, *, org_id: uuid.UUID, type: str, title: str, message: str, project_id: uuid.UUID | None = None
    ) -> Notification:
        notification = Notification(org_id=org_id, project_id=project_id, type=type, title=title, message=message)
        self._db.add(notification)
        await self._db.commit()
        await self._db.refresh(notification)
        return notification

    async def list_by_org(self, org_id: uuid.UUID, limit: int = 20, offset: int = 0) -> list[Notification]:
        result = await self._db.execute(
            select(Notification)
            .where(Notification.org_id == org_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_unread(self, org_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.org_id == org_id, Notification.is_read.is_(False))
        )
        return result.scalar_one()

    async def get_by_id(self, notification_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None:
        result = await self._db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.org_id == org_id)
        )
        return result.scalars().first()

    async def mark_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        await self._db.commit()
        await self._db.refresh(notification)
        return notification

    async def mark_all_read(self, org_id: uuid.UUID) -> int:
        result = await self._db.execute(
            update(Notification)
            .where(Notification.org_id == org_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        await self._db.commit()
        return result.rowcount or 0
