from app.schemas.extraction import DocumentSection, StructureAnalysisResult
from app.services.parsing.document_parser import ParsedDocument
from app.services.parsing.outline import HeadingHint
from app.services.structure_service import (
    StructureAnalyzer,
    build_structure_digest,
    select_technical_pages,
)
from tests._fake_llm import FakeLLMProvider


def _parsed() -> ParsedDocument:
    pages = [
        "Instructions to Bidders\nSubmit your bid before the deadline.",
        "Technical Specifications\nCore Switch throughput >= 20 Mbps",
        "Payment Terms\n30% advance, 70% on delivery.",
    ]
    outline = [
        HeadingHint(text="Instructions to Bidders", page=1, is_bold=True),
        HeadingHint(text="Technical Specifications", page=2, is_bold=True),
        HeadingHint(text="Payment Terms", page=3, is_bold=True),
    ]
    return ParsedDocument(pages=pages, page_count=3, outline=outline)


def test_build_structure_digest_includes_headings_and_page_starts():
    digest = build_structure_digest(_parsed(), max_chars=10_000)
    assert "DETECTED HEADINGS:" in digest
    assert "p2: Technical Specifications" in digest
    assert "PAGE STARTS:" in digest
    # The body text of pages should NOT be dumped wholesale into the digest.
    assert "30% advance" not in digest


def test_build_structure_digest_respects_max_chars():
    digest = build_structure_digest(_parsed(), max_chars=20)
    assert len(digest) <= 20


def test_select_technical_pages_returns_only_technical():
    result = StructureAnalysisResult(
        sections=[
            DocumentSection(title="Instructions", start_page=1, end_page=1, is_technical=False),
            DocumentSection(title="Technical Specifications", start_page=2, end_page=2, is_technical=True),
            DocumentSection(title="Payment Terms", start_page=3, end_page=3, is_technical=False),
        ]
    )
    assert select_technical_pages(result, page_count=3) == [2]


def test_select_technical_pages_none_when_no_technical():
    result = StructureAnalysisResult(
        sections=[DocumentSection(title="Legal", start_page=1, end_page=3, is_technical=False)]
    )
    assert select_technical_pages(result, page_count=3) is None


def test_select_technical_pages_clamps_ranges():
    result = StructureAnalysisResult(
        sections=[DocumentSection(title="Specs", start_page=2, end_page=99, is_technical=True)]
    )
    assert select_technical_pages(result, page_count=3) == [2, 3]


async def test_analyzer_parses_fake_sections():
    fake = FakeLLMProvider(
        {
            "analyze_structure": [
                {
                    "sections": [
                        {"title": "Technical Specifications", "start_page": 2, "end_page": 2, "is_technical": True},
                        {"title": "Payment Terms", "start_page": 3, "end_page": 3, "is_technical": False},
                    ]
                }
            ]
        }
    )
    analyzer = StructureAnalyzer(fake)
    result = await analyzer.analyze(_parsed())
    assert [s.is_technical for s in result.sections] == [True, False]
    assert fake.calls[0]["schema_name"] == "analyze_structure"
