import uuid
from datetime import datetime

from pydantic import BaseModel


class RequirementExtractionItem(BaseModel):
    equipment_key: str = "general"
    equipment_label: str = "General"
    requirement_key: str
    requirement_label: str
    category: str | None = None
    requirement_text: str
    expected_value: str | None = None
    unit: str | None = None
    operator: str | None = None
    is_mandatory: bool = True
    source_page: int | None = None


class RequirementExtractionResult(BaseModel):
    requirements: list[RequirementExtractionItem]


class SpecificationExtractionItem(BaseModel):
    equipment_key: str = "general"
    equipment_label: str = "General"
    spec_key: str
    spec_label: str
    spec_text: str
    value: str | None = None
    unit: str | None = None
    source_page: int | None = None


class SpecificationExtractionResult(BaseModel):
    specifications: list[SpecificationExtractionItem]


REQUIREMENT_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "equipment_key": {"type": "string"},
                    "equipment_label": {"type": "string"},
                    "requirement_key": {"type": "string"},
                    "requirement_label": {"type": "string"},
                    "category": {"type": ["string", "null"]},
                    "requirement_text": {"type": "string"},
                    "expected_value": {"type": ["string", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "operator": {"type": ["string", "null"]},
                    "is_mandatory": {"type": "boolean"},
                    "source_page": {"type": ["integer", "null"]},
                },
                "required": [
                    "equipment_key",
                    "equipment_label",
                    "requirement_key",
                    "requirement_label",
                    "requirement_text",
                    "is_mandatory",
                ],
            },
        }
    },
    "required": ["requirements"],
}

SPECIFICATION_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "specifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "equipment_key": {"type": "string"},
                    "equipment_label": {"type": "string"},
                    "spec_key": {"type": "string"},
                    "spec_label": {"type": "string"},
                    "spec_text": {"type": "string"},
                    "value": {"type": ["string", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "source_page": {"type": ["integer", "null"]},
                },
                "required": ["equipment_key", "equipment_label", "spec_key", "spec_label", "spec_text"],
            },
        }
    },
    "required": ["specifications"],
}


class ExtractedRequirementRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    project_id: uuid.UUID
    equipment_key: str
    equipment_label: str
    requirement_key: str
    requirement_label: str
    category: str | None
    requirement_text: str
    expected_value: str | None
    unit: str | None
    operator: str | None
    is_mandatory: bool
    source_page: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractedSpecificationRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    project_id: uuid.UUID
    vendor_name: str
    equipment_key: str
    equipment_label: str
    spec_key: str
    spec_label: str
    spec_text: str
    value: str | None
    unit: str | None
    source_page: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
