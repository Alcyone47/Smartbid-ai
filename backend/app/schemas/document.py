import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

DocType = Literal["rfp", "vendor_proposal"]


class DocumentRead(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    project_id: uuid.UUID
    doc_type: str
    vendor_name: str | None
    storage_path: str
    original_filename: str
    mime_type: str
    page_count: int | None
    status: str
    error_message: str | None
    uploaded_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
