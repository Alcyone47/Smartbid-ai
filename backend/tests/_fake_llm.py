"""A deterministic in-memory LLM provider for extraction/structure tests.

Returns canned JSON payloads keyed by ``schema_name`` so the structure-analysis
and requirement-extraction logic can be exercised without any network call.
"""

from typing import Any

from app.core.llm.base import LLMExtractionResult, LLMProvider


class FakeLLMProvider(LLMProvider):
    def __init__(self, responses_by_schema: dict[str, list[dict[str, Any]]]) -> None:
        # schema_name -> queue of payloads (one popped per call, last repeats).
        self._responses = {name: list(payloads) for name, payloads in responses_by_schema.items()}
        self.calls: list[dict[str, Any]] = []

    async def extract_structured(
        self,
        *,
        system_prompt: str,
        document_text: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> LLMExtractionResult:
        self.calls.append({"schema_name": schema_name, "document_text": document_text})
        queue = self._responses.get(schema_name, [{}])
        payload = queue.pop(0) if len(queue) > 1 else (queue[0] if queue else {})
        return LLMExtractionResult(data=payload, raw_response={"fake": True, "schema": schema_name})

    async def summarize(self, *, system_prompt: str, document_text: str) -> str:
        self.calls.append({"schema_name": "summarize", "document_text": document_text})
        return "fake summary"
