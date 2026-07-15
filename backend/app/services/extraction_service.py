import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import settings
from app.core.exceptions import LLMRateLimitError
from app.core.llm.base import LLMProvider
from app.schemas.extraction import (
    REQUIREMENT_EXTRACTION_JSON_SCHEMA,
    SPECIFICATION_EXTRACTION_JSON_SCHEMA,
    RequirementExtractionItem,
    RequirementExtractionResult,
    SpecificationExtractionItem,
    SpecificationExtractionResult,
)
from app.services.parsing.document_parser import DocumentParser, ParsedDocument
from app.services.parsing.text_cleaner import TextCleaner
from app.services.structure_service import StructureAnalyzer, select_technical_pages

logger = logging.getLogger(__name__)

# Called after each extraction batch with (completed_batches, total_batches).
ProgressCallback = Callable[[int, int], Awaitable[None]]

_ItemT = TypeVar("_ItemT", bound=BaseModel)


def _parse_batch_items(data: object, key: str, model: type[_ItemT]) -> tuple[list[_ItemT], int]:
    """Validate a batch's items individually, keeping the valid ones and counting the
    rest. A single malformed item (e.g. Gemini omitting a required field on one entry
    of a large batch) must not discard the whole document's extraction."""
    raw_list = data.get(key, []) if isinstance(data, dict) else []
    if not isinstance(raw_list, list):
        return [], 0
    items: list[_ItemT] = []
    skipped = 0
    for raw in raw_list:
        try:
            items.append(model.model_validate(raw))
        except ValidationError:
            skipped += 1
    return items, skipped

def _merge_requirements(items: list[RequirementExtractionItem]) -> list[RequirementExtractionItem]:
    """Merge requirement items sharing an equipment slug across batches.

    A single equipment/item can be described across several page batches; those
    partial requirement items are folded into one, concatenating their parameters
    while keeping the first-seen label/category/source_page.
    """
    merged: dict[str, RequirementExtractionItem] = {}
    order: list[str] = []
    for item in items:
        key = item.requirement_key
        existing = merged.get(key)
        if existing is None:
            merged[key] = item.model_copy(deep=True)
            order.append(key)
        else:
            existing.parameters.extend(item.parameters)
            if existing.category is None and item.category is not None:
                existing.category = item.category
            if existing.source_page is None and item.source_page is not None:
                existing.source_page = item.source_page
    return [merged[key] for key in order]


REQUIREMENT_SYSTEM_PROMPT = """You are extracting structured technical requirements from the technical-specification sections of an RFP (Request for Proposal) document.
An RFP asks for one or more distinct pieces of equipment/items (e.g. a network switch, a UPS, a server). Model each equipment/item as ONE requirement, and list its individual technical parameters underneath it. Each parameter states a Minimum Required Specification.

Only extract TECHNICAL parameters of equipment/software. Ignore any administrative, commercial, pricing, legal, eligibility, bid-process, SLA, payment, warranty or contractual text that may appear.

Produce one requirement item per distinct equipment/item, each with:
- requirement_key: a short stable slug (snake_case) identifying the equipment/item (e.g. "core_switch", "ups_unit"). If the document describes a single product or no grouping is apparent, use "general".
- requirement_label: a short human-readable name for the equipment/item (e.g. "Core Switch", "UPS Unit"). Use "General" when requirement_key is "general".
- category: a grouping label if apparent (e.g. "Power", "Networking"), else null
- source_page: the page number (as marked by "--- page N ---") where the equipment/item is introduced
- parameters: a list of that equipment's technical parameters. For every parameter produce:
  - parameter_key: a short stable slug (snake_case), e.g. "throughput", "input_voltage"
  - parameter_label: a short human-readable name, e.g. "Throughput", "Input Voltage"
  - parameter_text: the requirement for this parameter as stated in the document
  - expected_value / unit / operator: if the parameter specifies a measurable threshold (e.g. ">= 20 Mbps"), split into expected_value="20", unit="Mbps", operator=">=". Use operator values from: ">=", "<=", "==", ">", "<". If not measurable, leave all three null.
  - Whenever you produce a numeric expected_value, you MUST also produce its unit exactly as written in the document (e.g. "Mbps", "Hz", "nits", "cd/m²", "%", "ports"). Never guess, infer, or convert a unit that is not written. Leave unit null only when the document genuinely states a bare number with no unit or noun after it.
  - is_mandatory: true unless the parameter is explicitly marked optional/preferred/nice-to-have
  - source_page: the page number (as marked by "--- page N ---") the parameter text was found on

Do not compare, score, or judge requirements. Only extract what is stated."""

SPECIFICATION_SYSTEM_PROMPT = """You are extracting structured technical specifications from a vendor's proposal/datasheet document.
A vendor document usually describes one or more distinct pieces of equipment/items (e.g. a network switch, a UPS, a server). Assign every specification to the equipment/item it belongs to.
For every distinct specification, produce one item with:
- equipment_key: a short stable slug (snake_case) identifying the equipment/item this specification belongs to (e.g. "core_switch", "ups_unit"). Use the same naming convention you would for an RFP so equipment can be matched later. If the document describes a single product or no grouping is apparent, use "general".
- equipment_label: a short human-readable name for that equipment/item (e.g. "Core Switch", "UPS Unit"). Use "General" when equipment_key is "general".
- spec_key: a short stable slug (snake_case)
- spec_label: a short human-readable name
- spec_text: the specification as stated in the document
- value / unit: if the specification states a measurable value (e.g. "20 Mbps"), split into value="20", unit="Mbps". If not measurable, leave both null.
- Whenever you produce a numeric value, you MUST also produce its unit exactly as written in the document (e.g. "Mbps", "Hz", "nits", "cd/m²", "%", "ports"). Never guess, infer, or convert a unit that is not written. Leave unit null only when the document genuinely states a bare number with no unit or noun after it.
- source_page: the page number (as marked by "--- page N ---") the specification text was found on

Do not compare, score, or judge specifications. Only extract what is stated."""


# A page-tagged fragment of source text: (true 1-based page number, text). Page
# numbers stay global across batches so extracted source_page attribution is correct.
PageSegment = tuple[int, str]


def _segment_numbered_pages(numbered_pages: list[PageSegment], max_chars: int) -> list[PageSegment]:
    """Split numbered pages into segments, slicing any single page longer than
    max_chars. Page numbers are taken from the input (not the position), so a
    filtered subset of pages keeps its true global page numbers."""
    segments: list[PageSegment] = []
    for page_number, page in numbered_pages:
        if len(page) <= max_chars:
            segments.append((page_number, page))
        else:
            for start in range(0, len(page), max_chars):
                segments.append((page_number, page[start : start + max_chars]))
    return segments


def _segment_pages(pages: list[str], max_chars: int) -> list[PageSegment]:
    """Split pages into segments, further slicing any single page longer than max_chars so no segment alone can exceed the budget."""
    return _segment_numbered_pages([(index + 1, page) for index, page in enumerate(pages)], max_chars)


def _batch_segments(segments: list[PageSegment], max_chars: int, max_pages: int) -> list[list[PageSegment]]:
    """Group consecutive page segments into batches of up to ``max_pages`` distinct
    pages, kept under ``max_chars``. Whichever limit is hit first closes the batch, so
    a batch is a 5–10 page group rather than a single page (fewer LLM calls)."""
    batches: list[list[PageSegment]] = []
    current: list[PageSegment] = []
    current_len = 0
    current_pages: set[int] = set()
    for page_number, text in segments:
        adds_new_page = page_number not in current_pages
        over_chars = current_len + len(text) > max_chars
        over_pages = adds_new_page and len(current_pages) >= max_pages
        if current and (over_chars or over_pages):
            batches.append(current)
            current, current_len, current_pages = [], 0, set()
        current.append((page_number, text))
        current_len += len(text)
        current_pages.add(page_number)
    if current:
        batches.append(current)
    return batches


def _build_paginated_text(segments: list[PageSegment]) -> str:
    return "\n\n".join(f"--- page {page_number} ---\n{text}" for page_number, text in segments)


def _batch_document(pages: list[str], max_chars: int, max_pages: int) -> list[str]:
    """Turn parsed pages into a list of paginated-text blocks, each a group of up to
    ``max_pages`` pages under ``max_chars`` — a single LLM call per block."""
    return _batch_numbered_pages(
        [(index + 1, page) for index, page in enumerate(pages)], max_chars, max_pages
    )


def _batch_numbered_pages(numbered_pages: list[PageSegment], max_chars: int, max_pages: int) -> list[str]:
    """Batch an explicit list of (page_number, text) pairs into paginated-text
    blocks. Used to extract only the technical page subset while preserving each
    page's true global number for source_page attribution."""
    segments = _segment_numbered_pages(numbered_pages, max_chars)
    batches = _batch_segments(segments, max_chars, max_pages)
    return [_build_paginated_text(batch) for batch in batches] or [""]


async def _report_progress(callback: ProgressCallback | None, completed: int, total: int) -> None:
    if callback is not None:
        await callback(completed, total)


@dataclass
class RequirementExtractionOutcome:
    result: RequirementExtractionResult
    raw_response: dict
    page_count: int


@dataclass
class SpecificationExtractionOutcome:
    result: SpecificationExtractionResult
    raw_response: dict
    page_count: int


class ExtractionService:
    """Orchestrates parsing -> cleaning -> LLM extraction -> validation. No DB or task-queue coupling, so each stage stays independently replaceable per CLAUDE.md."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        document_parser: DocumentParser | None = None,
        text_cleaner: TextCleaner | None = None,
        structure_analyzer: StructureAnalyzer | None = None,
    ) -> None:
        self._llm_provider = llm_provider
        self._document_parser = document_parser or DocumentParser()
        self._text_cleaner = text_cleaner or TextCleaner()
        self._structure_analyzer = structure_analyzer or StructureAnalyzer(llm_provider)

    def _parse_and_clean(self, content: bytes, mime_type: str) -> ParsedDocument:
        parsed = self._document_parser.parse(content, mime_type)
        cleaned_pages = self._text_cleaner.clean_pages(parsed.pages)
        return ParsedDocument(pages=cleaned_pages, page_count=parsed.page_count, outline=parsed.outline)

    async def _select_technical_pages(self, parsed: ParsedDocument) -> list[PageSegment]:
        """Run the semantic structure pass and return the technical pages as
        (page_number, text) pairs. Falls back to all pages when disabled, when no
        technical section is found, or when the structure call fails (rate limits
        still propagate so the task can retry)."""
        all_pages: list[PageSegment] = [(index + 1, page) for index, page in enumerate(parsed.pages)]
        if not settings.structure_analysis_enabled:
            return all_pages
        try:
            result = await self._structure_analyzer.analyze(parsed)
        except LLMRateLimitError:
            raise
        except Exception:  # noqa: BLE001 - structure analysis is best-effort
            logger.warning("Structure analysis failed; extracting all pages", exc_info=True)
            return all_pages

        technical = select_technical_pages(result, parsed.page_count)
        if technical is None:
            logger.info("Structure analysis found no technical sections; extracting all pages")
            return all_pages
        technical_set = set(technical)
        selected = [(number, text) for number, text in all_pages if number in technical_set]
        logger.info("Structure analysis selected %d of %d pages as technical", len(selected), parsed.page_count)
        return selected or all_pages

    async def extract_requirements(
        self, content: bytes, mime_type: str, progress_callback: ProgressCallback | None = None
    ) -> RequirementExtractionOutcome:
        parsed = self._parse_and_clean(content, mime_type)
        technical_pages = await self._select_technical_pages(parsed)
        batches = _batch_numbered_pages(
            technical_pages, settings.extraction_max_chars_per_batch, settings.extraction_pages_per_batch
        )

        requirements: list[RequirementExtractionItem] = []
        raw_responses: list[dict] = []
        await _report_progress(progress_callback, 0, len(batches))
        for index, document_text in enumerate(batches):
            llm_result = await self._llm_provider.extract_structured(
                system_prompt=REQUIREMENT_SYSTEM_PROMPT,
                document_text=document_text,
                json_schema=REQUIREMENT_EXTRACTION_JSON_SCHEMA,
                schema_name="extract_requirements",
            )
            batch_items, skipped = _parse_batch_items(
                llm_result.data, "requirements", RequirementExtractionItem
            )
            if skipped:
                logger.warning("Skipped %d malformed requirement item(s) in batch %d", skipped, index + 1)
            requirements.extend(batch_items)
            raw_responses.append(llm_result.raw_response)
            await _report_progress(progress_callback, index + 1, len(batches))

        return RequirementExtractionOutcome(
            result=RequirementExtractionResult(requirements=_merge_requirements(requirements)),
            raw_response={"batches": raw_responses},
            page_count=parsed.page_count,
        )

    async def extract_specifications(
        self, content: bytes, mime_type: str, progress_callback: ProgressCallback | None = None
    ) -> SpecificationExtractionOutcome:
        parsed = self._parse_and_clean(content, mime_type)
        batches = _batch_document(parsed.pages, settings.extraction_max_chars_per_batch, settings.extraction_pages_per_batch)

        specifications: list = []
        raw_responses: list[dict] = []
        await _report_progress(progress_callback, 0, len(batches))
        for index, document_text in enumerate(batches):
            llm_result = await self._llm_provider.extract_structured(
                system_prompt=SPECIFICATION_SYSTEM_PROMPT,
                document_text=document_text,
                json_schema=SPECIFICATION_EXTRACTION_JSON_SCHEMA,
                schema_name="extract_specifications",
            )
            batch_items, skipped = _parse_batch_items(
                llm_result.data, "specifications", SpecificationExtractionItem
            )
            if skipped:
                logger.warning("Skipped %d malformed specification item(s) in batch %d", skipped, index + 1)
            specifications.extend(batch_items)
            raw_responses.append(llm_result.raw_response)
            await _report_progress(progress_callback, index + 1, len(batches))

        return SpecificationExtractionOutcome(
            result=SpecificationExtractionResult(specifications=specifications),
            raw_response={"batches": raw_responses},
            page_count=parsed.page_count,
        )
