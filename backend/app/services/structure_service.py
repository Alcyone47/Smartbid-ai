"""Semantic structure analysis (LLM pre-pass).

Before requirement extraction, classify an RFP's sections as technical vs
non-technical so only technical-specification pages are extracted. The LLM is
used purely to *understand* document structure (transform unstructured layout
into a labelled section list) — it makes no compliance decision, so this stays
within CLAUDE.md's allowed AI role. All page selection below is deterministic.
"""

import logging
import re

from app.config import settings
from app.core.llm.base import LLMProvider
from app.schemas.extraction import (
    STRUCTURE_ANALYSIS_JSON_SCHEMA,
    DocumentSection,
    StructureAnalysisResult,
)
from app.services.parsing.document_parser import ParsedDocument

logger = logging.getLogger(__name__)

STRUCTURE_SYSTEM_PROMPT = """You are analyzing the structure of an RFP (Request for Proposal) / tender document to locate the sections that contain TECHNICAL equipment or software specifications.

You are given a structure digest: a table of contents (if present), detected headings, and the first lines and table headers of each page, each tagged with its page number.

Classify every distinct section as technical or non-technical BY MEANING — never by matching fixed titles.
- TECHNICAL (is_technical = true): sections stating the required specifications of equipment/software/items — e.g. technical specifications, scope of supply, schedule of requirements, bill of materials / BOQ technical parameters, datasheets, make & model / configuration tables, performance/capacity/interface requirements.
- NON-TECHNICAL (is_technical = false): administrative, commercial, pricing/financial, legal, eligibility/qualification, bid/tender process, instructions to bidders, SLA, payment terms, warranty/contractual, general/company information.

For each section return: title, start_page, end_page (inclusive page range covering the section, using the page numbers in the digest), is_technical, and a short reason.
Cover the whole document with non-overlapping page ranges. Do not extract requirements — only classify structure."""

# A table-of-contents entry: a title followed by dot leaders / spaces and a page
# number, e.g. "3.2 Technical Specifications ......... 24".
_TOC_LINE = re.compile(r"^.{3,}?[.\s]{2,}\d{1,4}\s*$")
_TOC_SCAN_PAGES = 6


def build_structure_digest(parsed: ParsedDocument, max_chars: int) -> str:
    """Build a compact digest (TOC + headings + per-page first lines) for the LLM.

    Deliberately small — the classifier needs the document's skeleton, not its
    body — so a whole RFP fits in one call regardless of length.
    """
    blocks: list[str] = []

    toc_lines = _extract_toc_lines(parsed.pages)
    if toc_lines:
        blocks.append("TABLE OF CONTENTS:\n" + "\n".join(toc_lines))

    if parsed.outline:
        heading_lines = [f"p{h.page}: {h.text}" for h in parsed.outline]
        blocks.append("DETECTED HEADINGS:\n" + "\n".join(heading_lines))

    page_lines: list[str] = []
    for index, page in enumerate(parsed.pages):
        first_line = next((ln.strip() for ln in page.splitlines() if ln.strip()), "")
        if first_line:
            page_lines.append(f"p{index + 1}: {first_line[:160]}")
    if page_lines:
        blocks.append("PAGE STARTS:\n" + "\n".join(page_lines))

    digest = "\n\n".join(blocks)
    if len(digest) > max_chars:
        digest = digest[:max_chars]
    return digest


def _extract_toc_lines(pages: list[str]) -> list[str]:
    lines: list[str] = []
    for page in pages[:_TOC_SCAN_PAGES]:
        for raw in page.splitlines():
            line = raw.strip()
            if line and _TOC_LINE.match(line):
                lines.append(line)
    return lines


def select_technical_pages(
    result: StructureAnalysisResult, page_count: int
) -> list[int] | None:
    """Deterministically resolve the classified sections into technical page numbers.

    Returns a sorted list of 1-based page numbers, or ``None`` when no technical
    section was found (the caller then falls back to extracting all pages).
    """
    pages: set[int] = set()
    for section in result.sections:
        if not section.is_technical:
            continue
        start = max(1, min(section.start_page, section.end_page))
        end = min(page_count, max(section.start_page, section.end_page))
        for page in range(start, end + 1):
            pages.add(page)
    if not pages:
        return None
    return sorted(pages)


class StructureAnalyzer:
    """Runs one LLM classify call over a document's structure digest."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider

    async def analyze(self, parsed: ParsedDocument) -> StructureAnalysisResult:
        digest = build_structure_digest(parsed, settings.structure_analysis_max_chars)
        if not digest.strip():
            return StructureAnalysisResult(sections=[])

        llm_result = await self._llm_provider.extract_structured(
            system_prompt=STRUCTURE_SYSTEM_PROMPT,
            document_text=digest,
            json_schema=STRUCTURE_ANALYSIS_JSON_SCHEMA,
            schema_name="analyze_structure",
        )
        data = llm_result.data if isinstance(llm_result.data, dict) else {}
        raw_sections = data.get("sections", []) if isinstance(data, dict) else []
        sections: list[DocumentSection] = []
        for raw in raw_sections if isinstance(raw_sections, list) else []:
            try:
                sections.append(DocumentSection.model_validate(raw))
            except Exception:
                continue
        return StructureAnalysisResult(sections=sections)
