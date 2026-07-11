from dataclasses import dataclass

from pydantic import ValidationError

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


def _build_paginated_text(pages: list[str]) -> str:
    return "\n\n".join(f"--- page {index + 1} ---\n{page}" for index, page in enumerate(pages))


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
        document_text = _build_paginated_text(parsed.pages)
        llm_result = await self._llm_provider.extract_structured(
            system_prompt=REQUIREMENT_SYSTEM_PROMPT,
            document_text=document_text,
            json_schema=REQUIREMENT_EXTRACTION_JSON_SCHEMA,
            schema_name="extract_requirements",
        )
        try:
            result = RequirementExtractionResult.model_validate(llm_result.data)
        except ValidationError as exc:
            raise ExtractionValidationError(f"Requirement extraction output failed validation: {exc}") from exc
        return RequirementExtractionOutcome(
            result=result, raw_response=llm_result.raw_response, page_count=parsed.page_count
        )

    async def extract_specifications(self, content: bytes, mime_type: str) -> SpecificationExtractionOutcome:
        parsed = self._parse_and_clean(content, mime_type)
        document_text = _build_paginated_text(parsed.pages)
        llm_result = await self._llm_provider.extract_structured(
            system_prompt=SPECIFICATION_SYSTEM_PROMPT,
            document_text=document_text,
            json_schema=SPECIFICATION_EXTRACTION_JSON_SCHEMA,
            schema_name="extract_specifications",
        )
        try:
            result = SpecificationExtractionResult.model_validate(llm_result.data)
        except ValidationError as exc:
            raise ExtractionValidationError(f"Specification extraction output failed validation: {exc}") from exc
        return SpecificationExtractionOutcome(
            result=result, raw_response=llm_result.raw_response, page_count=parsed.page_count
        )
