import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID | None
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountRead(BaseModel):
    count: int


class MarkAllReadResult(BaseModel):
    marked: int
