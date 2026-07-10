from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.org import OrgMember

bearer_scheme = HTTPBearer()


@dataclass
class CurrentUser:
    user_id: UUID
    org_id: UUID
    role: str


async def get_current_org_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = UUID(payload["sub"])

    result = await db.execute(select(OrgMember).where(OrgMember.user_id == user_id))
    membership = result.scalars().first()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no organization")

    return CurrentUser(user_id=user_id, org_id=membership.org_id, role=membership.role)
