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


def _parsed_with_boilerplate(page_count: int = 200) -> ParsedDocument:
    """A long document whose every page starts with the same running header —
    the shape that once bloated the digest past its budget and truncated it."""
    header = "RFP - Selection of Implementation Agency for a Very Important Surveillance Project"
    pages = [f"{header}\nSection {n}: content for page {n}\nbody text" for n in range(1, page_count + 1)]
    return ParsedDocument(pages=pages, page_count=page_count, outline=[])


def test_build_structure_digest_skips_repeated_boilerplate_first_lines():
    digest = build_structure_digest(_parsed_with_boilerplate(), max_chars=100_000)
    # The running header must not be the per-page line; the real heading is.
    assert "p5: Section 5: content for page 5" in digest
    assert "p5: RFP - Selection" not in digest


def test_build_structure_digest_covers_full_page_range_when_over_budget():
    parsed = _parsed_with_boilerplate(200)
    digest = build_structure_digest(parsed, max_chars=4000)
    assert len(digest) <= 4000
    # Degradation may thin pages, but first and last pages always survive.
    assert "p1:" in digest
    assert "p200:" in digest


def test_select_technical_pages_excludes_explicit_non_technical():
    result = StructureAnalysisResult(
        sections=[
            DocumentSection(title="Instructions", start_page=1, end_page=1, is_technical=False),
            DocumentSection(title="Technical Specifications", start_page=2, end_page=2, is_technical=True),
            DocumentSection(title="Payment Terms", start_page=3, end_page=3, is_technical=False),
        ]
    )
    selection = select_technical_pages(result, page_count=3)
    assert selection.pages == [2]
    assert selection.technical_pages == 1
    assert selection.excluded_pages == 2
    assert selection.uncovered_pages_included == 0


def test_select_technical_pages_none_when_no_technical():
    result = StructureAnalysisResult(
        sections=[DocumentSection(title="Legal", start_page=1, end_page=3, is_technical=False)]
    )
    assert select_technical_pages(result, page_count=3) is None


def test_select_technical_pages_clamps_ranges():
    result = StructureAnalysisResult(
        sections=[DocumentSection(title="Specs", start_page=2, end_page=99, is_technical=True)]
    )
    selection = select_technical_pages(result, page_count=3)
    # The 2..99 range clamps to 2..3; page 1 is covered by no section, so the
    # uncovered-page safety net includes it as well.
    assert selection.pages == [1, 2, 3]
    assert selection.technical_pages == 2
    assert selection.uncovered_pages_included == 1


def test_select_technical_pages_includes_pages_no_section_covers():
    """Silence must never exclude: pages outside every classified section are
    extracted (a truncated/incomplete classification once hid an RFP's final
    technical annexures)."""
    result = StructureAnalysisResult(
        sections=[
            DocumentSection(title="Instructions", start_page=1, end_page=2, is_technical=False),
            DocumentSection(title="Specs", start_page=3, end_page=4, is_technical=True),
            # Pages 5-10 are covered by no section at all.
        ]
    )
    selection = select_technical_pages(result, page_count=10)
    assert selection.pages == [3, 4, 5, 6, 7, 8, 9, 10]
    assert selection.uncovered_pages_included == 6
    assert selection.excluded_pages == 2


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
