from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    data_root: str = Field(default="../Data", alias="DATA_ROOT")
    log_root: str = Field(default="./logs", alias="LOG_ROOT")

    llm_base_url: str = Field(default="http://localhost:8001/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="sk-xxx", alias="LLM_API_KEY")
    llm_model: str = Field(default="qwen3-32b-instruct", alias="LLM_MODEL")
    llm_max_tokens: int = Field(default=4096, alias="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=60, alias="LLM_TIMEOUT")
    llm_max_concurrency: int = Field(default=3, alias="LLM_MAX_CONCURRENCY")
    llm_use_mock: bool = Field(default=True, alias="LLM_USE_MOCK")

    crawler_timeout: int = Field(default=30, alias="CRAWLER_TIMEOUT")
    crawler_max_concurrency: int = Field(default=5, alias="CRAWLER_MAX_CONCURRENCY")
    crawler_user_agent: str = Field(default="InternalLinkBot/1.0", alias="CRAWLER_USER_AGENT")

    default_batch_size: int = Field(default=10, alias="DEFAULT_BATCH_SIZE")
    default_score_threshold: float = Field(default=0.6, alias="DEFAULT_SCORE_THRESHOLD")
    default_max_recommendations: int = Field(default=8, alias="DEFAULT_MAX_RECOMMENDATIONS")

    def resolve_path(self, value: str) -> Path:
        base = Path(__file__).resolve().parents[1]  # Code/
        path = Path(value)
        if path.is_absolute():
            return path
        return (base / path).resolve()

    @property
    def data_root_path(self) -> Path:
        return self.resolve_path(self.data_root)

    @property
    def log_root_path(self) -> Path:
        return self.resolve_path(self.log_root)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

