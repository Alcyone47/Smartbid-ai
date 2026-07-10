import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    status: str | None = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    client_name: str | None
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
