import pytest

from app.core.llm.base import LLMExtractionResult, LLMProvider
from app.services.extraction_service import ExtractionService
from app.services.parsing.document_parser import ParsedDocument


class _FakeParser:
    def __init__(self, pages: list[str]) -> None:
        self._pages = pages

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        return ParsedDocument(pages=self._pages, page_count=len(self._pages))


class _PassthroughCleaner:
    def clean_pages(self, pages: list[str]) -> list[str]:
        return pages


class _EmptyProvider(LLMProvider):
    """Returns a valid empty extraction for any schema."""

    async def extract_structured(self, *, system_prompt, document_text, json_schema, schema_name):
        key = "requirements" if "requirement" in schema_name else "specifications"
        return LLMExtractionResult(data={key: []}, raw_response={"schema": schema_name})

    async def summarize(self, *, system_prompt, document_text):
        return "stub summary"


def _service(pages: list[str]) -> ExtractionService:
    return ExtractionService(
        llm_provider=_EmptyProvider(),
        document_parser=_FakeParser(pages),
        text_cleaner=_PassthroughCleaner(),
    )


# Three 25k-char pages vs the 48k-char batch budget -> two pages can't share a batch,
# so this yields three separate batches (one progress report each).
_THREE_BATCH_PAGES = ["A" * 25000, "B" * 25000, "C" * 25000]


@pytest.mark.asyncio
async def test_requirements_progress_reports_each_batch():
    calls: list[tuple[int, int]] = []

    async def record(done: int, total: int) -> None:
        calls.append((done, total))

    outcome = await _service(_THREE_BATCH_PAGES).extract_requirements(
        b"x", "application/pdf", progress_callback=record
    )

    assert calls == [(0, 3), (1, 3), (2, 3), (3, 3)]
    assert calls[-1][0] == calls[-1][1]  # reaches 100%
    assert outcome.page_count == 3
    assert outcome.summary == "stub summary"  # summarization doesn't leak into batch progress


@pytest.mark.asyncio
async def test_specifications_progress_reports_each_batch():
    calls: list[tuple[int, int]] = []

    async def record(done: int, total: int) -> None:
        calls.append((done, total))

    await _service(_THREE_BATCH_PAGES).extract_specifications(b"x", "application/pdf", progress_callback=record)

    assert calls == [(0, 3), (1, 3), (2, 3), (3, 3)]


@pytest.mark.asyncio
async def test_no_callback_is_safe():
    outcome = await _service(_THREE_BATCH_PAGES).extract_requirements(b"x", "application/pdf")
    assert outcome.result.requirements == []
