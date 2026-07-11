from dataclasses import dataclass
from typing import Awaitable, Callable

from pydantic import ValidationError

from app.config import settings
from app.core.exceptions import ExtractionValidationError
from app.core.llm.base import LLMProvider
from app.schemas.extraction import (
    REQUIREMENT_EXTRACTION_JSON_SCHEMA,
    SPECIFICATION_EXTRACTION_JSON_SCHEMA,
    RequirementExtractionResult,
    SpecificationExtractionResult,
)
from app.services.parsing.document_parser import DocumentParser, ParsedDocument
from app.services.parsing.text_cleaner import TextCleaner

# Called after each extraction batch with (completed_batches, total_batches).
ProgressCallback = Callable[[int, int], Awaitable[None]]

REQUIREMENT_SYSTEM_PROMPT = """You are extracting structured technical requirements from an RFP (Request for Proposal) document.
For every distinct requirement, produce one item with:
- requirement_key: a short stable slug (snake_case)
- requirement_label: a short human-readable name
- category: a grouping label if apparent (e.g. "Power", "Networking"), else null
- requirement_text: the requirement as stated in the document
- expected_value / unit / operator: if the requirement specifies a measurable threshold (e.g. ">= 20 Mbps"), split into expected_value="20", unit="Mbps", operator=">=". Use operator values from: ">=", "<=", "==", ">", "<". If not measurable, leave all three null.
- is_mandatory: true unless the document explicitly marks the requirement as optional/preferred/nice-to-have
- source_page: the page number (as marked by "--- page N ---") the requirement text was found on

Do not compare, score, or judge requirements. Only extract what is stated."""

SPECIFICATION_SYSTEM_PROMPT = """You are extracting structured technical specifications from a vendor's proposal/datasheet document.
For every distinct specification, produce one item with:
- spec_key: a short stable slug (snake_case)
- spec_label: a short human-readable name
- spec_text: the specification as stated in the document
- value / unit: if the specification states a measurable value (e.g. "20 Mbps"), split into value="20", unit="Mbps". If not measurable, leave both null.
- source_page: the page number (as marked by "--- page N ---") the specification text was found on

Do not compare, score, or judge specifications. Only extract what is stated."""


# A page-tagged fragment of source text: (true 1-based page number, text). Page
# numbers stay global across batches so extracted source_page attribution is correct.
PageSegment = tuple[int, str]


def _segment_pages(pages: list[str], max_chars: int) -> list[PageSegment]:
    """Split pages into segments, further slicing any single page longer than max_chars so no segment alone can exceed the budget."""
    segments: list[PageSegment] = []
    for index, page in enumerate(pages):
        page_number = index + 1
        if len(page) <= max_chars:
            segments.append((page_number, page))
        else:
            for start in range(0, len(page), max_chars):
                segments.append((page_number, page[start : start + max_chars]))
    return segments


def _batch_segments(segments: list[PageSegment], max_chars: int) -> list[list[PageSegment]]:
    """Greedily pack page segments into batches whose combined length stays under max_chars."""
    batches: list[list[PageSegment]] = []
    current: list[PageSegment] = []
    current_len = 0
    for page_number, text in segments:
        if current and current_len + len(text) > max_chars:
            batches.append(current)
            current, current_len = [], 0
        current.append((page_number, text))
        current_len += len(text)
    if current:
        batches.append(current)
    return batches


def _build_paginated_text(segments: list[PageSegment]) -> str:
    return "\n\n".join(f"--- page {page_number} ---\n{text}" for page_number, text in segments)


def _batch_document(pages: list[str], max_chars: int) -> list[str]:
    """Turn parsed pages into a list of paginated-text blocks, each small enough for a single LLM call."""
    segments = _segment_pages(pages, max_chars)
    batches = _batch_segments(segments, max_chars)
    return [_build_paginated_text(batch) for batch in batches] or [""]


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
    ) -> None:
        self._llm_provider = llm_provider
        self._document_parser = document_parser or DocumentParser()
        self._text_cleaner = text_cleaner or TextCleaner()

    def _parse_and_clean(self, content: bytes, mime_type: str) -> ParsedDocument:
        parsed = self._document_parser.parse(content, mime_type)
        cleaned_pages = self._text_cleaner.clean_pages(parsed.pages)
        return ParsedDocument(pages=cleaned_pages, page_count=parsed.page_count)

    async def extract_requirements(self, content: bytes, mime_type: str) -> RequirementExtractionOutcome:
        parsed = self._parse_and_clean(content, mime_type)
        batches = _batch_document(parsed.pages, settings.extraction_max_chars_per_batch)

        requirements: list = []
        raw_responses: list[dict] = []
        for document_text in batches:
            llm_result = await self._llm_provider.extract_structured(
                system_prompt=REQUIREMENT_SYSTEM_PROMPT,
                document_text=document_text,
                json_schema=REQUIREMENT_EXTRACTION_JSON_SCHEMA,
                schema_name="extract_requirements",
            )
            try:
                batch_result = RequirementExtractionResult.model_validate(llm_result.data)
            except ValidationError as exc:
                raise ExtractionValidationError(
                    f"Requirement extraction output failed validation: {exc}"
                ) from exc
            requirements.extend(batch_result.requirements)
            raw_responses.append(llm_result.raw_response)

        return RequirementExtractionOutcome(
            result=RequirementExtractionResult(requirements=requirements),
            raw_response={"batches": raw_responses},
            page_count=parsed.page_count,
        )

    async def extract_specifications(self, content: bytes, mime_type: str) -> SpecificationExtractionOutcome:
        parsed = self._parse_and_clean(content, mime_type)
        batches = _batch_document(parsed.pages, settings.extraction_max_chars_per_batch)

        specifications: list = []
        raw_responses: list[dict] = []
        for document_text in batches:
            llm_result = await self._llm_provider.extract_structured(
                system_prompt=SPECIFICATION_SYSTEM_PROMPT,
                document_text=document_text,
                json_schema=SPECIFICATION_EXTRACTION_JSON_SCHEMA,
                schema_name="extract_specifications",
            )
            try:
                batch_result = SpecificationExtractionResult.model_validate(llm_result.data)
            except ValidationError as exc:
                raise ExtractionValidationError(
                    f"Specification extraction output failed validation: {exc}"
                ) from exc
            specifications.extend(batch_result.specifications)
            raw_responses.append(llm_result.raw_response)

        return SpecificationExtractionOutcome(
            result=SpecificationExtractionResult(specifications=specifications),
            raw_response={"batches": raw_responses},
            page_count=parsed.page_count,
        )
