from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMExtractionResult:
    data: dict[str, Any]
    raw_response: dict[str, Any]


class LLMProvider(ABC):
    """Abstraction over the LLM used for structured extraction, so the provider (Claude, OpenAI, ...) can be swapped without touching extraction logic."""

    @abstractmethod
    async def extract_structured(
        self,
        *,
        system_prompt: str,
        document_text: str,
        json_schema: dict[str, Any],
        schema_name: str,
    ) -> LLMExtractionResult:
        """Run one extraction call over document_text, returning data conforming to json_schema plus the raw provider response."""
