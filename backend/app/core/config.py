from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str | None = None
    cors_origins: list[str] = ["http://127.0.0.1:5173"]
    api_host: str = "127.0.0.1"
    api_port: int = 8001

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
