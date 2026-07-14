import asyncio
import json
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.core.exceptions import LLMProviderError, LLMRateLimitError
from app.core.llm.backoff import compute_backoff, parse_retry_delay_seconds
from app.core.llm.base import LLMExtractionResult, LLMProvider


def _is_rate_limit(exc: APIError) -> bool:
    """True when the error is an HTTP 429 / RESOURCE_EXHAUSTED (rate limit)."""
    code = getattr(exc, "code", None)
    status_str = str(getattr(exc, "status", "") or "").upper()
    return code == 429 or status_str == "RESOURCE_EXHAUSTED"


def _retry_delay_from_error(exc: APIError) -> float | None:
    """Extract the server-suggested wait (RetryInfo.retryDelay) from a Gemini error, if present."""
    details = getattr(exc, "details", None)
    candidates: list = []
    if isinstance(details, dict):
        error = details.get("error", details)
        if isinstance(error, dict):
            candidates = error.get("details", []) or []
    elif isinstance(details, list):
        candidates = details
    for detail in candidates:
        if isinstance(detail, dict) and "RetryInfo" in str(detail.get("@type", "")):
            delay = parse_retry_delay_seconds(detail.get("retryDelay"))
            if delay is not None:
                return delay
    return None


class GeminiProvider(LLMProvider):
    """Google AI Studio (Gemini) provider — free-tier friendly.

    Uses JSON output mode with the target schema described in the prompt rather than
    Gemini's native ``response_schema`` (which uses an OpenAPI schema dialect that
    rejects the ``["type", "null"]`` unions in our JSON Schema). Output shape is
    enforced downstream by Pydantic validation in the extraction service.

    Rate limits (429) are retried in-call with exponential backoff + jitter, honoring
    the server's ``retryDelay``; once in-call retries are exhausted it raises
    ``LLMRateLimitError`` so the Celery task can re-queue the job (status "retrying").
    """

    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def extract_structured(
        self,
        *,
        system_prompt: str,
        document_text: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> LLMExtractionResult:
        instruction = (
            f"{system_prompt}\n\n"
            "Return ONLY a JSON object that conforms to this JSON Schema. "
            "Do not wrap it in markdown fences or add any prose:\n"
            f"{json.dumps(json_schema)}"
        )

        response = await self._generate_with_retry(instruction, document_text)

        text = response.text
        if not text:
            raise LLMProviderError("Gemini response did not include any text output")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Gemini output was not valid JSON: {exc}") from exc

        return LLMExtractionResult(data=data, raw_response=response.model_dump(mode="json"))

    async def _generate_with_retry(self, instruction: str, document_text: str):
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            response_mime_type="application/json",
        )
        for attempt in range(settings.extraction_max_retries + 1):
            try:
                return await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=document_text,
                    config=config,
                )
            except APIError as exc:
                if not _is_rate_limit(exc):
                    raise LLMProviderError(f"Gemini extraction call failed: {exc}") from exc
                server_delay = _retry_delay_from_error(exc)
                if attempt >= settings.extraction_max_retries:
                    raise LLMRateLimitError(
                        f"Gemini rate limit persisted after {attempt + 1} attempts: {exc}",
                        retry_after=server_delay,
                    ) from exc
                delay = compute_backoff(
                    attempt,
                    settings.extraction_retry_base_delay,
                    settings.extraction_retry_max_delay,
                    server_delay,
                )
                await asyncio.sleep(delay)
        # Unreachable: the loop either returns or raises.
        raise LLMProviderError("Gemini extraction failed unexpectedly")
