from typing import Any

from anthropic import AsyncAnthropic

from app.config import settings
from app.core.exceptions import LLMProviderError
from app.core.llm.base import LLMExtractionResult, LLMProvider


class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_extraction_model

    async def extract_structured(
        self,
        *,
        system_prompt: str,
        document_text: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> LLMExtractionResult:
        tool = {
            "name": schema_name,
            "description": f"Return {schema_name} extracted from the document.",
            "input_schema": json_schema,
        }
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=8192,
                system=system_prompt,
                tools=[tool],
                tool_choice={"type": "tool", "name": schema_name},
                messages=[{"role": "user", "content": document_text}],
            )
        except Exception as exc:
            raise LLMProviderError(f"Claude extraction call failed: {exc}") from exc

        tool_use_block = next((block for block in response.content if block.type == "tool_use"), None)
        if tool_use_block is None:
            raise LLMProviderError("Claude response did not include a tool_use block")

        return LLMExtractionResult(data=tool_use_block.input, raw_response=response.model_dump())

    async def summarize(self, *, system_prompt: str, document_text: str) -> str:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=settings.summary_max_output_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": document_text}],
            )
        except Exception as exc:
            raise LLMProviderError(f"Claude summarize call failed: {exc}") from exc

        text_block = next((block for block in response.content if block.type == "text"), None)
        if text_block is None:
            raise LLMProviderError("Claude response did not include a text block")
        return text_block.text
