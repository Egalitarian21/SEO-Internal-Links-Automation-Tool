from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Internal Linking Tool Demo API"
    cors_origins: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_prefix="ILT_", env_file=".env", extra="ignore")


settings = Settings()

