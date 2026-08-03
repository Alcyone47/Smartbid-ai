from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, get_current_org_user
from app.repositories.org_repository import OrgRepository
from app.schemas.org import OrgMeRead

router = APIRouter(prefix="/org", tags=["org"])


@router.get("/me", response_model=OrgMeRead)
async def get_my_org(
    current_user: CurrentUser = Depends(get_current_org_user),
    db: AsyncSession = Depends(get_db),
) -> OrgMeRead:
    repo = OrgRepository(db)
    org = await repo.get_by_id(current_user.org_id)
    membership = await repo.get_membership(current_user.org_id, current_user.user_id)
    if org is None or membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    member_count = await repo.count_members(current_user.org_id)
    return OrgMeRead(
        org_id=org.id,
        org_name=org.name,
        org_created_at=org.created_at,
        member_count=member_count,
        role=membership.role,
        member_since=membership.created_at,
    )
