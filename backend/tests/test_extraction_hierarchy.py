"""End-to-end extraction-service tests with a fake LLM (no network).

Verify that the structure pre-pass restricts extraction to technical pages and
that the output is the hierarchical Requirement -> Parameters -> Min Spec shape.
"""

import pytest

from app.config import settings
from app.services.extraction_service import ExtractionService, _merge_requirements
from app.schemas.extraction import ParameterExtractionItem, RequirementExtractionItem
from app.services.parsing.document_parser import ParsedDocument
from app.services.parsing.outline import HeadingHint
from tests._fake_llm import FakeLLMProvider

PDF_MIME = "application/pdf"


class _StubParser:
    def __init__(self, parsed: ParsedDocument) -> None:
        self._parsed = parsed

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        return self._parsed


def _four_page_doc() -> ParsedDocument:
    pages = [
        "Instructions to Bidders. Submit before the deadline.",  # p1 admin
        "Core Switch. Throughput requirement stated here.",       # p2 technical
        "Core Switch continued. Port count requirement.",         # p3 technical
        "Payment Terms. 30 percent advance.",                     # p4 commercial
    ]
    outline = [HeadingHint(text="Technical Specifications", page=2, is_bold=True)]
    return ParsedDocument(pages=pages, page_count=4, outline=outline)


def _structure_response() -> dict:
    return {
        "sections": [
            {"title": "Instructions", "start_page": 1, "end_page": 1, "is_technical": False},
            {"title": "Technical Specifications", "start_page": 2, "end_page": 3, "is_technical": True},
            {"title": "Payment Terms", "start_page": 4, "end_page": 4, "is_technical": False},
        ]
    }


async def test_extraction_uses_only_technical_pages_and_builds_hierarchy(monkeypatch):
    # Force one page per batch so pages 2 and 3 become two separate extraction calls.
    monkeypatch.setattr(settings, "extraction_pages_per_batch", 1)

    fake = FakeLLMProvider(
        {
            "analyze_structure": [_structure_response()],
            "extract_requirements": [
                {
                    "requirements": [
                        {
                            "requirement_key": "core_switch",
                            "requirement_label": "Core Switch",
                            "parameters": [
                                {
                                    "parameter_key": "throughput",
                                    "parameter_label": "Throughput",
                                    "parameter_text": ">= 20 Mbps",
                                    "expected_value": "20",
                                    "unit": "Mbps",
                                    "operator": ">=",
                                    "is_mandatory": True,
                                    "source_page": 2,
                                }
                            ],
                        }
                    ]
                },
                {
                    "requirements": [
                        {
                            "requirement_key": "core_switch",
                            "requirement_label": "Core Switch",
                            "parameters": [
                                {
                                    "parameter_key": "ports",
                                    "parameter_label": "Ports",
                                    "parameter_text": ">= 24 ports",
                                    "expected_value": "24",
                                    "unit": None,
                                    "operator": ">=",
                                    "is_mandatory": True,
                                    "source_page": 3,
                                }
                            ],
                        }
                    ]
                },
            ],
        }
    )

    service = ExtractionService(llm_provider=fake, document_parser=_StubParser(_four_page_doc()))
    outcome = await service.extract_requirements(b"", PDF_MIME)

    # Summary call ran first, then the structure pass, then two extraction calls
    # (one per technical page).
    schema_calls = [c["schema_name"] for c in fake.calls]
    assert schema_calls == ["summarize", "analyze_structure", "extract_requirements", "extract_requirements"]

    # Only technical pages 2 and 3 were sent; admin/commercial pages were skipped.
    extraction_text = "\n".join(c["document_text"] for c in fake.calls if c["schema_name"] == "extract_requirements")
    assert "--- page 2 ---" in extraction_text
    assert "--- page 3 ---" in extraction_text
    assert "--- page 1 ---" not in extraction_text
    assert "--- page 4 ---" not in extraction_text

    # Parameters from both batches merged under the one Core Switch requirement.
    requirements = outcome.result.requirements
    assert len(requirements) == 1
    assert requirements[0].requirement_key == "core_switch"
    assert [p.parameter_key for p in requirements[0].parameters] == ["throughput", "ports"]
    assert outcome.page_count == 4


async def test_extraction_falls_back_to_all_pages_when_no_technical_section():
    fake = FakeLLMProvider(
        {
            "analyze_structure": [{"sections": [
                {"title": "All Admin", "start_page": 1, "end_page": 4, "is_technical": False},
            ]}],
            "extract_requirements": [{"requirements": []}],
        }
    )
    service = ExtractionService(llm_provider=fake, document_parser=_StubParser(_four_page_doc()))
    await service.extract_requirements(b"", PDF_MIME)

    extraction_text = "\n".join(c["document_text"] for c in fake.calls if c["schema_name"] == "extract_requirements")
    # No technical section -> fall back to extracting every page.
    for page in range(1, 5):
        assert f"--- page {page} ---" in extraction_text


async def test_extraction_skips_structure_pass_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "structure_analysis_enabled", False)
    fake = FakeLLMProvider({"extract_requirements": [{"requirements": []}]})
    service = ExtractionService(llm_provider=fake, document_parser=_StubParser(_four_page_doc()))
    await service.extract_requirements(b"", PDF_MIME)
    assert "analyze_structure" not in [c["schema_name"] for c in fake.calls]


def test_merge_requirements_folds_by_equipment_key():
    items = [
        RequirementExtractionItem(
            requirement_key="ups", requirement_label="UPS",
            parameters=[ParameterExtractionItem(parameter_key="cap", parameter_label="Capacity", parameter_text="20 KVA")],
        ),
        RequirementExtractionItem(
            requirement_key="ups", requirement_label="UPS",
            parameters=[ParameterExtractionItem(parameter_key="runtime", parameter_label="Runtime", parameter_text="30 min")],
        ),
        RequirementExtractionItem(
            requirement_key="switch", requirement_label="Switch",
            parameters=[ParameterExtractionItem(parameter_key="ports", parameter_label="Ports", parameter_text="24")],
        ),
    ]
    merged = _merge_requirements(items)
    assert [r.requirement_key for r in merged] == ["ups", "switch"]
    assert [p.parameter_key for p in merged[0].parameters] == ["cap", "runtime"]


def test_merge_requirements_keeps_distinct_labels_sharing_a_slug_apart():
    items = [
        RequirementExtractionItem(
            requirement_key="camera", requirement_label="Camera Type A (ANPR)",
            parameters=[ParameterExtractionItem(parameter_key="mp", parameter_label="MP", parameter_text="2 MP")],
        ),
        RequirementExtractionItem(
            requirement_key="camera", requirement_label="Camera Type B (Surveillance)",
            parameters=[ParameterExtractionItem(parameter_key="mp", parameter_label="MP", parameter_text="8 MP")],
        ),
    ]
    merged = _merge_requirements(items)
    assert len(merged) == 2
    # The second distinct equipment gets a disambiguated slug.
    assert [r.requirement_key for r in merged] == ["camera", "camera_2"]


def test_merge_requirements_merges_same_label_ignoring_case_and_punctuation():
    items = [
        RequirementExtractionItem(
            requirement_key="ups", requirement_label="Online UPS",
            parameters=[ParameterExtractionItem(parameter_key="cap", parameter_label="Capacity", parameter_text="20 KVA")],
        ),
        RequirementExtractionItem(
            requirement_key="ups", requirement_label="online-ups",
            parameters=[ParameterExtractionItem(parameter_key="runtime", parameter_label="Runtime", parameter_text="30 min")],
        ),
    ]
    merged = _merge_requirements(items)
    assert len(merged) == 1
    assert [p.parameter_key for p in merged[0].parameters] == ["cap", "runtime"]


def test_parse_requirement_items_salvages_valid_parameters():
    """One malformed parameter must drop only itself — not its equipment item
    and the sibling parameters (that once wiped whole equipment rows)."""
    from app.services.extraction_service import _parse_requirement_items

    data = {
        "requirements": [
            {
                "requirement_key": "switch",
                "requirement_label": "Switch",
                "parameters": [
                    {"parameter_key": "ports", "parameter_label": "Ports", "parameter_text": "24"},
                    {"parameter_key": "throughput"},  # malformed: missing required fields
                    {"parameter_key": "capacity", "parameter_label": "Capacity", "parameter_text": "8 Gbps"},
                ],
            },
            "not-a-dict",  # malformed item
        ]
    }
    items, skipped_items, skipped_parameters = _parse_requirement_items(data)
    assert len(items) == 1
    assert [p.parameter_key for p in items[0].parameters] == ["ports", "capacity"]
    assert skipped_items == 1
    assert skipped_parameters == 1
