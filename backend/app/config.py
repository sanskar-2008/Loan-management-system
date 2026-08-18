from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Loan Management System"
    secret_key: str = "change-me-in-production-lms-secret-key-2024"
    access_token_expire_minutes: int = 60 * 12
    algorithm: str = "HS256"
    database_url: str = f"sqlite:///{DATA_DIR / 'loan_management.db'}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    admin_full_name: str = "System Admin"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
