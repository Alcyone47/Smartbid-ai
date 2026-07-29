import json
from typing import Any

from groq import AsyncGroq

from app.config import settings
from app.core.exceptions import LLMProviderError
from app.core.llm.base import LLMExtractionResult, LLMProvider


class GroqProvider(LLMProvider):
    """Free-tier provider (OpenAI-compatible tool calling) for testing without an Anthropic key."""

    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    async def extract_structured(
        self,
        *,
        system_prompt: str,
        document_text: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> LLMExtractionResult:
        tool = {
            "type": "function",
            "function": {
                "name": schema_name,
                "description": f"Return {schema_name} extracted from the document.",
                "parameters": json_schema,
            },
        }
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": document_text},
                ],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": schema_name}},
                max_completion_tokens=settings.extraction_max_output_tokens,
            )
        except Exception as exc:
            raise LLMProviderError(f"Groq extraction call failed: {exc}") from exc

        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        if not tool_calls:
            raise LLMProviderError("Groq response did not include a tool call")

        try:
            data = json.loads(tool_calls[0].function.arguments)
        except json.JSONDecodeError as exc:
            raise LLMProviderError(f"Groq tool call arguments were not valid JSON: {exc}") from exc

        return LLMExtractionResult(data=data, raw_response=response.model_dump())

    async def summarize(self, *, system_prompt: str, document_text: str) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": document_text},
                ],
                max_completion_tokens=settings.summary_max_output_tokens,
            )
        except Exception as exc:
            raise LLMProviderError(f"Groq summarize call failed: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMProviderError("Groq response did not include content")
        return content
