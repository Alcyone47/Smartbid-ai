from dataclasses import dataclass
from uuid import UUID

import anyio
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.org import Org, OrgMember

bearer_scheme = HTTPBearer()

# Supabase projects created after the "JWT Signing Keys" rollout sign user session
# tokens asymmetrically (ES256) and rotate keys, rather than a static shared HS256
# secret. Verifying via the project's JWKS endpoint works for both cases and follows
# key rotation automatically.
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json", cache_keys=True)
    return _jwks_client


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
        signing_key = await anyio.to_thread.run_sync(
            _get_jwks_client().get_signing_key_from_jwt, credentials.credentials
        )
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = UUID(payload["sub"])

    result = await db.execute(select(OrgMember).where(OrgMember.user_id == user_id))
    membership = result.scalars().first()

    if membership is None:
        # First authenticated request for this user: auto-provision a personal org.
        # There is no separate signup/onboarding flow that creates orgs, so this is
        # the only place a brand-new Supabase user ever gets one.
        email = payload.get("email")
        org = Org(name=f"{email}'s Organization" if email else "My Organization")
        db.add(org)
        await db.flush()
        membership = OrgMember(org_id=org.id, user_id=user_id, role="admin")
        db.add(membership)
        await db.commit()

    return CurrentUser(user_id=user_id, org_id=membership.org_id, role=membership.role)
