from functools import lru_cache
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://internal_link:CHANGE_ME_LOCAL_PASSWORD@localhost:5432/internal_link_mvp"
    app_env: str = "local"
    default_tenant_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    enable_llm: bool = False
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
