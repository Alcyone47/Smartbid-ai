import uuid
from datetime import datetime

from pydantic import BaseModel


class VendorCreate(BaseModel):
    name: str


class VendorRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    document_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
