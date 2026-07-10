import uuid
from datetime import datetime

from pydantic import BaseModel


class OrgRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
