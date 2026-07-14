import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# The manual-override values a user may pin a project to. ``None`` clears the
# override and returns the project to auto-derived status.
StatusOverride = Literal["draft", "in_progress", "in_review", "completed"]


class ProjectCreate(BaseModel):
    name: str
    client_name: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    client_name: str | None = None
    status_override: StatusOverride | None = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    client_name: str | None
    status: str
    status_override: str | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
