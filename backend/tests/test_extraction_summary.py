import pytest

from app.core.exceptions import LLMRateLimitError
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


class _StubSummaryProvider(LLMProvider):
    """Returns an empty requirement extraction; summarize() behavior is injected."""

    def __init__(self, summarize_fn) -> None:
        self._summarize_fn = summarize_fn
        self.summarize_calls: list[str] = []

    async def extract_structured(self, *, system_prompt, document_text, json_schema, schema_name):
        return LLMExtractionResult(data={"requirements": []}, raw_response={})

    async def summarize(self, *, system_prompt, document_text):
        self.summarize_calls.append(document_text)
        return self._summarize_fn()


def _service(pages: list[str], summarize_fn) -> ExtractionService:
    return ExtractionService(
        llm_provider=_StubSummaryProvider(summarize_fn),
        document_parser=_FakeParser(pages),
        text_cleaner=_PassthroughCleaner(),
    )


@pytest.mark.asyncio
async def test_summary_populated_from_provider():
    service = _service(["page one text"], lambda: "  A concise gist.  ")
    outcome = await service.extract_requirements(b"x", "application/pdf")
    assert outcome.summary == "A concise gist."


@pytest.mark.asyncio
async def test_summary_failure_degrades_gracefully():
    def _raise():
        raise RuntimeError("provider exploded")

    service = _service(["page one text"], _raise)
    outcome = await service.extract_requirements(b"x", "application/pdf")
    assert outcome.summary is None
    assert outcome.result.requirements == []  # extraction itself is unaffected


@pytest.mark.asyncio
async def test_summary_rate_limit_propagates():
    def _raise():
        raise LLMRateLimitError("rate limited")

    service = _service(["page one text"], _raise)
    with pytest.raises(LLMRateLimitError):
        await service.extract_requirements(b"x", "application/pdf")


@pytest.mark.asyncio
async def test_summary_input_is_truncated(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "summary_max_chars", 10)
    provider = _StubSummaryProvider(lambda: "gist")
    service = ExtractionService(
        llm_provider=provider, document_parser=_FakeParser(["A" * 50]), text_cleaner=_PassthroughCleaner()
    )
    await service.extract_requirements(b"x", "application/pdf")
    assert len(provider.summarize_calls[0]) == 10


@pytest.mark.asyncio
async def test_summary_disabled_skips_provider_call(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "summary_enabled", False)
    provider = _StubSummaryProvider(lambda: "gist")
    service = ExtractionService(
        llm_provider=provider, document_parser=_FakeParser(["page text"]), text_cleaner=_PassthroughCleaner()
    )
    outcome = await service.extract_requirements(b"x", "application/pdf")
    assert outcome.summary is None
    assert provider.summarize_calls == []
