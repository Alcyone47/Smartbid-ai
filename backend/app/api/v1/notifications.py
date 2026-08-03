import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import MarkAllReadResult, NotificationRead, UnreadCountRead

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    limit: int = 20,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationRead]:
    repo = NotificationRepository(db)
    notifications = await repo.list_by_org(current_user.org_id, limit=limit, offset=offset)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/unread-count", response_model=UnreadCountRead)
async def unread_count(
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountRead:
    repo = NotificationRepository(db)
    count = await repo.count_unread(current_user.org_id)
    return UnreadCountRead(count=count)


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(notification_id, current_user.org_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification = await repo.mark_read(notification)
    return NotificationRead.model_validate(notification)


@router.post("/read-all", response_model=MarkAllReadResult)
async def mark_all_read(
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadResult:
    repo = NotificationRepository(db)
    marked = await repo.mark_all_read(current_user.org_id)
    return MarkAllReadResult(marked=marked)
