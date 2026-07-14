import uuid
from datetime import datetime

from pydantic import BaseModel


# --------------------------------------------------------------------------- #
# Structure analysis (LLM semantic pre-pass)
#
# Before extracting requirements, a single LLM call classifies the document's
# sections as technical-specification vs non-technical so administrative,
# commercial, legal, eligibility, SLA, payment and contractual content is
# skipped. Classification is by meaning, not fixed section titles.
# --------------------------------------------------------------------------- #
class DocumentSection(BaseModel):
    title: str
    start_page: int
    end_page: int
    is_technical: bool
    reason: str | None = None


class StructureAnalysisResult(BaseModel):
    sections: list[DocumentSection]


STRUCTURE_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_page": {"type": "integer"},
                    "end_page": {"type": "integer"},
                    "is_technical": {"type": "boolean"},
                    "reason": {"type": ["string", "null"]},
                },
                "required": ["title", "start_page", "end_page", "is_technical"],
            },
        }
    },
    "required": ["sections"],
}


# --------------------------------------------------------------------------- #
# Requirement extraction (RFP side) — hierarchical
#
# A Requirement is one equipment/item. Each Requirement carries a list of
# Parameters, and every Parameter states a Minimum Required Specification
# (expected_value / unit / operator + mandatory flag).
# --------------------------------------------------------------------------- #
class ParameterExtractionItem(BaseModel):
    parameter_key: str
    parameter_label: str
    parameter_text: str
    expected_value: str | None = None
    unit: str | None = None
    operator: str | None = None
    is_mandatory: bool = True
    source_page: int | None = None


class RequirementExtractionItem(BaseModel):
    # requirement_key / requirement_label identify the equipment/item this
    # requirement is about; they map to the parent Requirement row's
    # equipment_key / equipment_label columns.
    requirement_key: str = "general"
    requirement_label: str = "General"
    category: str | None = None
    source_page: int | None = None
    parameters: list[ParameterExtractionItem] = []


class RequirementExtractionResult(BaseModel):
    requirements: list[RequirementExtractionItem]


REQUIREMENT_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "requirement_key": {"type": "string"},
                    "requirement_label": {"type": "string"},
                    "category": {"type": ["string", "null"]},
                    "source_page": {"type": ["integer", "null"]},
                    "parameters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "parameter_key": {"type": "string"},
                                "parameter_label": {"type": "string"},
                                "parameter_text": {"type": "string"},
                                "expected_value": {"type": ["string", "null"]},
                                "unit": {"type": ["string", "null"]},
                                "operator": {"type": ["string", "null"]},
                                "is_mandatory": {"type": "boolean"},
                                "source_page": {"type": ["integer", "null"]},
                            },
                            "required": [
                                "parameter_key",
                                "parameter_label",
                                "parameter_text",
                                "is_mandatory",
                            ],
                        },
                    },
                },
                "required": ["requirement_key", "requirement_label", "parameters"],
            },
        }
    },
    "required": ["requirements"],
}


# --------------------------------------------------------------------------- #
# Specification extraction (vendor side) — unchanged, flat by equipment
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Read models (API responses) — hierarchical Requirement -> Parameters
# --------------------------------------------------------------------------- #
class ParameterRead(BaseModel):
    id: uuid.UUID
    requirement_id: uuid.UUID
    parameter_key: str
    parameter_label: str
    parameter_text: str
    expected_value: str | None
    unit: str | None
    operator: str | None
    is_mandatory: bool
    source_page: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequirementRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    project_id: uuid.UUID
    equipment_key: str
    equipment_label: str
    category: str | None
    source_page: int | None
    created_at: datetime
    parameters: list[ParameterRead]

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
