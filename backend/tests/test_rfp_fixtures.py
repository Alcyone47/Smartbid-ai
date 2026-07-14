"""Fixture-backed tests over real sample RFP PDFs.

Skipped automatically when no PDFs have been dropped into tests/fixtures/rfps/.
Parsing is deterministic; the LLM classification is stubbed so CI never makes a
network call — the manifest supplies the expected section labels and the fake
provider echoes them back, proving the deterministic page-selection wiring.
"""

from pathlib import Path

import pytest

from app.services.parsing.pdf import extract_pdf_document
from app.services.parsing.document_parser import ParsedDocument
from app.services.structure_service import StructureAnalyzer, select_technical_pages
from tests._fake_llm import FakeLLMProvider
from tests.fixtures.manifest import RFP_FIXTURES

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "rfps"


def _available_fixtures():
    return [f for f in RFP_FIXTURES if (FIXTURES_DIR / f.filename).exists()]


pytestmark = pytest.mark.skipif(
    not _available_fixtures(),
    reason="No sample RFP PDFs registered in tests/fixtures/rfps/ + manifest.py",
)


@pytest.mark.parametrize("fixture", _available_fixtures(), ids=lambda f: f.filename)
def test_parser_detects_headings(fixture):
    content = (FIXTURES_DIR / fixture.filename).read_bytes()
    pages, outline = extract_pdf_document(content)
    assert pages, "parser produced no pages"
    # A real RFP should expose at least some heading-like lines via font metrics.
    assert outline, f"no candidate headings detected in {fixture.filename}"


@pytest.mark.parametrize("fixture", _available_fixtures(), ids=lambda f: f.filename)
async def test_technical_sections_selected_over_non_technical(fixture):
    content = (FIXTURES_DIR / fixture.filename).read_bytes()
    pages, outline = extract_pdf_document(content)
    parsed = ParsedDocument(pages=pages, page_count=len(pages), outline=outline)

    # Stub the classifier: mark the manifest's technical sections technical and the
    # rest non-technical, spread across the document's real page count. This checks
    # the deterministic selection wiring, not the model's judgment.
    page_count = len(pages)
    sections = []
    for i, title in enumerate(fixture.technical_sections):
        sections.append({"title": title, "start_page": min(i + 1, page_count),
                         "end_page": min(i + 1, page_count), "is_technical": True})
    for j, title in enumerate(fixture.non_technical_sections):
        page = min(len(fixture.technical_sections) + j + 1, page_count)
        sections.append({"title": title, "start_page": page, "end_page": page, "is_technical": False})

    fake = FakeLLMProvider({"analyze_structure": [{"sections": sections}]})
    result = await StructureAnalyzer(fake).analyze(parsed)

    technical_titles = {s.title for s in result.sections if s.is_technical}
    assert technical_titles == set(fixture.technical_sections)
    # At least one technical page is selected when technical sections exist.
    if fixture.technical_sections:
        assert select_technical_pages(result, page_count) is not None
