from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Internal Linking Tool Demo API"
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]
    database_url: str = "sqlite:///./data/internal_links.sqlite"
    knowledge_base_path: str = "./knowledge_base"
    crawler_user_agent: str = "InternalLinkBot/1.0"
    crawler_timeout: int = 30
    recommendation_limit_per_page: int = 8

    model_config = SettingsConfigDict(env_prefix="ILT_", env_file=".env", extra="ignore")


settings = Settings()
