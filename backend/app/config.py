from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    backend_cors_origins: str = "http://localhost:5173"

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    supabase_storage_bucket: str = "project-documents"
    supabase_exports_bucket: str = "exports"

    database_url: str

    anthropic_api_key: str | None = None
    anthropic_extraction_model: str = "claude-haiku-4-5"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"

    voyage_api_key: str | None = None
    voyage_embedding_model: str = "voyage-3"

    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "claude"

    # Extraction is chunked into page groups so a single LLM call covers 5–10 pages
    # (not one call per page) while staying under the model's context window. A batch
    # closes at whichever limit hits first: extraction_pages_per_batch distinct pages,
    # or extraction_max_chars_per_batch characters of source text (~4 chars/token).
    extraction_pages_per_batch: int = 8
    extraction_max_chars_per_batch: int = 48000
    extraction_max_output_tokens: int = 4000

    # Before extracting requirements, a semantic LLM "structure analysis" pass
    # classifies each RFP section as technical vs non-technical so only technical
    # specification pages are extracted. structure_analysis_max_chars caps the
    # compact structure digest (TOC + headings + page/table hints) sent to that
    # single classify call — not the full document body. If disabled or the pass
    # finds no technical sections, extraction falls back to all pages.
    structure_analysis_enabled: bool = True
    structure_analysis_max_chars: int = 12000

    # Rate-limit (HTTP 429) handling: exponential backoff with jitter, capped, honoring
    # the server's suggested retryDelay/Retry-After when larger. Used both for in-call
    # provider retries and the Celery task's automatic re-queue.
    extraction_max_retries: int = 5
    extraction_retry_base_delay: float = 2.0
    extraction_retry_max_delay: float = 60.0

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]


settings = Settings()
