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

    # Extraction is chunked so a single LLM call never exceeds the provider's
    # context window / per-minute token budget. Budget is measured in characters of
    # source text per call (~4 chars/token). Defaults keep a single Groq request
    # (input + reserved output) under the free-tier 12k tokens-per-minute limit.
    extraction_max_chars_per_batch: int = 24000
    extraction_max_output_tokens: int = 4000

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]


settings = Settings()
