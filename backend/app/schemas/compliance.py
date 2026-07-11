import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ComplianceMatrixEntryRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    requirement_id: uuid.UUID
    vendor_document_id: uuid.UUID
    matched_specification_id: uuid.UUID | None
    vendor_name: str
    requirement_label: str
    requirement_text: str
    expected_value: str | None
    unit: str | None
    operator: str | None
    is_mandatory: bool
    vendor_value: str | None
    source_page: int | None
    status: str
    match_score: Decimal | None
    rationale: str
    computed_at: datetime
