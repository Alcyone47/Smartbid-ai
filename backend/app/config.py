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
    anthropic_extraction_model: str = "claude-sonnet-4-5"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    voyage_api_key: str | None = None
    voyage_embedding_model: str = "voyage-3"

    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "claude"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]


settings = Settings()
