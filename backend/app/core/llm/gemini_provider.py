import asyncio
import json
import logging
import re
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.core.exceptions import LLMProviderError, LLMRateLimitError
from app.core.llm.backoff import compute_backoff, parse_retry_delay_seconds
from app.core.llm.base import LLMExtractionResult, LLMProvider

logger = logging.getLogger(__name__)

# Below this size a truncated batch is not split further — halving a tiny text
# cannot reduce the output enough to matter, and infinite recursion must not
# be possible.
_MIN_SPLIT_CHARS = 2000


def _is_truncated(response: Any) -> bool:
    """True when generation stopped because the output-token cap was hit."""
    candidates = getattr(response, "candidates", None) or []
    finish_reason = getattr(candidates[0], "finish_reason", None) if candidates else None
    return finish_reason == types.FinishReason.MAX_TOKENS


def _split_document_text(document_text: str) -> tuple[str, str]:
    """Split a batch roughly in half, preferring a '--- page N ---' boundary,
    then a newline, so no page/table row is cut mid-line."""
    midpoint = len(document_text) // 2
    cut = document_text.rfind("\n--- page ", 0, midpoint)
    if cut <= 0:
        cut = document_text.rfind("\n", 0, midpoint)
    if cut <= 0:
        cut = midpoint
    return document_text[:cut], document_text[cut:]


def _parse_json_lenient(text: str) -> Any:
    """Parse the model's JSON output tolerantly.

    Despite ``response_mime_type="application/json"``, Gemini occasionally wraps
    the object in markdown fences or appends extra content after it ("Extra
    data"). Strip fences and, failing a strict parse, take the first complete
    JSON value — schema conformance is still enforced downstream by Pydantic.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        data, end = json.JSONDecoder().raw_decode(stripped)
        trailing = stripped[end:].strip()
        if trailing:
            logger.warning(
                "Gemini output had %d chars of extra data after the JSON object; using the first object",
                len(trailing),
            )
        return data


def _merge_list_payloads(left: dict, right: dict) -> dict:
    """Merge two schema-shaped payloads by concatenating their list values.

    Every extraction schema is a single object holding list(s) of items, so a
    split batch's halves recombine by list concatenation."""
    combined = dict(left)
    for key, value in right.items():
        if isinstance(value, list) and isinstance(combined.get(key), list):
            combined[key] = combined[key] + value
        elif key not in combined:
            combined[key] = value
    return combined


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
        return await self._extract(instruction, document_text, allow_split=True)

    async def _extract(
        self, instruction: str, document_text: str, *, allow_split: bool
    ) -> LLMExtractionResult:
        response = await self._generate_with_retry(instruction, document_text)

        # Output-token truncation would otherwise surface as invalid JSON and
        # fail the whole document; recover deterministically by splitting the
        # batch in half and extracting each half separately.
        if _is_truncated(response) and allow_split and len(document_text) > _MIN_SPLIT_CHARS:
            logger.warning(
                "Gemini output hit the token cap for a %d-char batch; splitting in half and retrying",
                len(document_text),
            )
            left_text, right_text = _split_document_text(document_text)
            left = await self._extract(instruction, left_text, allow_split=False)
            right = await self._extract(instruction, right_text, allow_split=False)
            merged = _merge_list_payloads(
                left.data if isinstance(left.data, dict) else {},
                right.data if isinstance(right.data, dict) else {},
            )
            return LLMExtractionResult(
                data=merged, raw_response={"split": [left.raw_response, right.raw_response]}
            )

        text = response.text
        if not text:
            raise LLMProviderError("Gemini response did not include any text output")

        try:
            data = _parse_json_lenient(text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Gemini output was not valid JSON: {exc}") from exc

        return LLMExtractionResult(data=data, raw_response=response.model_dump(mode="json"))

    async def _generate_with_retry(self, instruction: str, document_text: str):
        config = types.GenerateContentConfig(
            system_instruction=instruction,
            response_mime_type="application/json",
            max_output_tokens=settings.extraction_max_output_tokens,
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
