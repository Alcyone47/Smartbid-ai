from app.config import settings
from app.core.exceptions import AppException
from app.core.llm.base import LLMProvider
from app.core.llm.claude_provider import ClaudeProvider
from app.core.llm.gemini_provider import GeminiProvider
from app.core.llm.groq_provider import GroqProvider


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "claude":
        return ClaudeProvider()
    if settings.llm_provider == "groq":
        return GroqProvider()
    if settings.llm_provider == "gemini":
        return GeminiProvider()
    raise AppException(
        f"Unsupported LLM provider: {settings.llm_provider}",
        error_code="UNSUPPORTED_LLM_PROVIDER",
    )
