"""Semantic structure analysis (LLM pre-pass).

Before requirement extraction, classify an RFP's sections as technical vs
non-technical so only technical-specification pages are extracted. The LLM is
used purely to *understand* document structure (transform unstructured layout
into a labelled section list) — it makes no compliance decision, so this stays
within CLAUDE.md's allowed AI role. All page selection below is deterministic.
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass, field

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

# How many leading non-empty lines of a page are considered when picking its
# representative "first line" for the digest.
_FIRST_LINE_CANDIDATES = 5
# A line repeated on at least this many pages (or 5% of pages, whichever is
# larger) is boilerplate — usually the document's running header — and carries
# no structural signal.
_BOILERPLATE_MIN_PAGES = 3


def _page_first_lines(pages: list[str]) -> list[tuple[int, str]]:
    """Pick one representative line per page, skipping boilerplate headers.

    Many RFPs repeat the same running header as the first line of every page;
    using it would both bloat the digest and hide the real headings. A line
    occurring on many pages is treated as boilerplate and the next distinct
    line is used instead.
    """
    candidates: list[list[str]] = []
    for page in pages:
        lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
        candidates.append(lines[:_FIRST_LINE_CANDIDATES])

    frequency: Counter[str] = Counter(line for lines in candidates for line in set(lines))
    threshold = max(_BOILERPLATE_MIN_PAGES, len(pages) // 20)

    first_lines: list[tuple[int, str]] = []
    for index, lines in enumerate(candidates):
        if not lines:
            continue
        chosen = next((line for line in lines if frequency[line] < threshold), lines[0])
        first_lines.append((index + 1, chosen))
    return first_lines


def build_structure_digest(parsed: ParsedDocument, max_chars: int) -> str:
    """Build a compact digest (TOC + headings + per-page first lines) for the LLM.

    Deliberately small — the classifier needs the document's skeleton, not its
    body — so a whole RFP fits in one call regardless of length.

    The digest must always cover the document's full page range: a blind tail
    truncation once hid an RFP's final 30 pages of technical annexures from the
    classifier, silently dropping their requirements. When over budget, the
    digest degrades gracefully (shorter snippets, then thinned page sampling,
    then no headings block) but always keeps the TOC and the first/last pages.
    """
    toc_lines = _extract_toc_lines(parsed.pages)
    toc_block = "TABLE OF CONTENTS:\n" + "\n".join(toc_lines) if toc_lines else None

    headings_block = None
    if parsed.outline:
        heading_lines = [f"p{h.page}: {h.text}" for h in parsed.outline]
        headings_block = "DETECTED HEADINGS:\n" + "\n".join(heading_lines)

    first_lines = _page_first_lines(parsed.pages)
    last_page = len(parsed.pages)

    def compose(snippet_width: int, step: int, include_headings: bool) -> str:
        page_lines = [
            f"p{number}: {line[:snippet_width]}"
            for position, (number, line) in enumerate(first_lines)
            if position % step == 0 or number in (1, last_page)
        ]
        blocks = [
            block
            for block in (
                toc_block,
                headings_block if include_headings else None,
                "PAGE STARTS:\n" + "\n".join(page_lines) if page_lines else None,
            )
            if block
        ]
        return "\n\n".join(blocks)

    for include_headings in (True, False):
        for snippet_width in (100, 60, 40):
            for step in (1, 2, 3):
                digest = compose(snippet_width, step, include_headings)
                if len(digest) <= max_chars:
                    return digest

    # Even the most aggressive degradation is over budget (e.g. an enormous
    # TOC). Hard-cap as a last resort — degraded, but never silent.
    digest = compose(40, 3, include_headings=False)
    logger.warning(
        "Structure digest still exceeds %d chars after degradation (%d); hard-truncating",
        max_chars,
        len(digest),
    )
    return digest[:max_chars]


def _extract_toc_lines(pages: list[str]) -> list[str]:
    lines: list[str] = []
    for page in pages[:_TOC_SCAN_PAGES]:
        for raw in page.splitlines():
            line = raw.strip()
            if line and _TOC_LINE.match(line):
                lines.append(line)
    return lines


@dataclass
class PageSelection:
    """Deterministic outcome of resolving classified sections into pages.

    ``pages`` is what extraction will consume. The counters make coverage
    auditable: only an explicit non-technical verdict may exclude a page —
    pages no section covers (classifier truncation, omitted ranges) are
    included, so a structure-analysis mistake costs tokens, never requirements.
    """

    pages: list[int] = field(default_factory=list)
    technical_pages: int = 0
    excluded_pages: int = 0
    uncovered_pages_included: int = 0


def _section_pages(section: DocumentSection, page_count: int) -> range:
    start = max(1, min(section.start_page, section.end_page))
    end = min(page_count, max(section.start_page, section.end_page))
    return range(start, end + 1)


def select_technical_pages(
    result: StructureAnalysisResult, page_count: int
) -> PageSelection | None:
    """Deterministically resolve the classified sections into pages to extract.

    Returns ``None`` when no technical section was found (the caller then falls
    back to extracting all pages). Otherwise returns the technical pages PLUS
    any page not covered by any section at all — silence must never exclude.
    """
    technical: set[int] = set()
    non_technical: set[int] = set()
    for section in result.sections:
        target = technical if section.is_technical else non_technical
        target.update(_section_pages(section, page_count))
    if not technical:
        return None

    all_pages = set(range(1, page_count + 1))
    uncovered = all_pages - technical - non_technical
    excluded = non_technical - technical
    selected = all_pages - excluded
    return PageSelection(
        pages=sorted(selected),
        technical_pages=len(technical),
        excluded_pages=len(excluded),
        uncovered_pages_included=len(uncovered),
    )


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
