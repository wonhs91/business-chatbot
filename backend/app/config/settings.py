from functools import lru_cache
from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Business Chatbot Backend"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    cors_origins: list[AnyHttpUrl] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS",
    )
    
    model_config = SettingsConfigDict(
        env_file='.env', 
        case_sensitive=False,
        env_file_encoding = "utf-8",
        extra="allow"
    )

    # LLM configuration
    openai_api_key: SecretStr | None = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    # Vector store configuration
    chroma_persist_directory: str | None = Field(
        default="./data/chroma",
        env="CHROMA_PERSIST_DIRECTORY",
    )
    chroma_collection_name: str = Field(
        default="business_docs",
        env="CHROMA_COLLECTION_NAME",
    )

    # Discord integration
    discord_webhook_url: AnyHttpUrl | None = Field(
        default=None,
        env="DISCORD_WEBHOOK_URL",
    )

    # Scheduling integration
    calendly_api_token: SecretStr | None = Field(
        default=None,
        env="CALENDLY_API_TOKEN",
    )
    calendly_user_uri: AnyHttpUrl | None = Field(
        default=None,
        env="CALENDLY_USER_URI",
    )
    fallback_meeting_link: AnyHttpUrl | None = Field(
        default=None,
        env="FALLBACK_MEETING_LINK",
    )

    # LangSmith tracing configuration
    langsmith_tracing: bool = Field(
        default=False,
        env="LANGSMITH_TRACING",
    )
    langsmith_endpoint: AnyHttpUrl | None = Field(
        default=None,
        env="LANGSMITH_ENDPOINT",
    )
    langsmith_api_key: SecretStr | None = Field(
        default=None,
        env="LANGSMITH_API_KEY",
    )
    langsmith_project: str | None = Field(
        default=None,
        env="LANGSMITH_PROJECT",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
