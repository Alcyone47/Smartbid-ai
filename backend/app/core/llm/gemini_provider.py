import json
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.core.exceptions import LLMProviderError
from app.core.llm.base import LLMExtractionResult, LLMProvider


class GeminiProvider(LLMProvider):
    """Google AI Studio (Gemini) provider — free-tier friendly.

    Uses JSON output mode with the target schema described in the prompt rather than
    Gemini's native ``response_schema`` (which uses an OpenAPI schema dialect that
    rejects the ``["type", "null"]`` unions in our JSON Schema). Output shape is
    enforced downstream by Pydantic validation in the extraction service.
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
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=document_text,
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    response_mime_type="application/json",
                ),
            )
        except APIError as exc:
            raise LLMProviderError(f"Gemini extraction call failed: {exc}") from exc

        text = response.text
        if not text:
            raise LLMProviderError("Gemini response did not include any text output")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Gemini output was not valid JSON: {exc}") from exc

        return LLMExtractionResult(data=data, raw_response=response.model_dump(mode="json"))
