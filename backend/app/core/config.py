from functools import lru_cache
import os
from typing import List


class Settings:
    def __init__(self) -> None:
        self.database_url = self._database_url()
        self.openai_default_model = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4.1-mini")
        self.app_base_url = os.getenv("APP_BASE_URL", "http://localhost:5173")
        self.session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "wt_session")
        self.session_secret = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
        self.max_image_bytes = int(os.getenv("MAX_IMAGE_BYTES", "10485760"))
        self.cors_allowed_origins = self._cors_origins()
        self.cookie_secure = os.getenv("ENVIRONMENT", "").lower() in {"prod", "production"}

    @staticmethod
    def _database_url() -> str:
        url = os.getenv("DATABASE_URL")
        if not url:
            return "sqlite:///./walkitalki.db"
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://") and "+psycopg" not in url:
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @staticmethod
    def _cors_origins() -> List[str]:
        raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
