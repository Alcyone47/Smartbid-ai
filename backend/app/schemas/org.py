import uuid
from datetime import datetime

from pydantic import BaseModel


class OrgRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrgMeRead(BaseModel):
    """Read-only snapshot combining the org and the requesting user's membership in
    it — feeds both the Profile and Organization tabs of Settings from one call."""

    org_id: uuid.UUID
    org_name: str
    org_created_at: datetime
    member_count: int
    role: str
    member_since: datetime
