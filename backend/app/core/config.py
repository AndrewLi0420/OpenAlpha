from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import (
    AnyHttpUrl,
    ConfigDict,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    field_validator,
)
from pydantic_settings import BaseSettings

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass


class Environment(StrEnum):
    dev = "dev"
    prod = "prod"

class Paths:
    # my_fastapi_project
    ROOT_DIR: Path = Path(__file__).parent.parent.parent
    BASE_DIR: Path = ROOT_DIR / "app"
    EMAIL_TEMPLATES_DIR: Path = BASE_DIR / "emails"
    LOGIN_PATH: str = "/auth/login"


class Settings(BaseSettings):
    @property
    def PATHS(self) -> Paths:
        return Paths()

    ENVIRONMENT: Environment = "dev"
    SECRET_KEY: str
    DEBUG: bool = False
    AUTH_TOKEN_LIFETIME_SECONDS: int = 3600
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"  # type:ignore
    SENTRY_DSN: HttpUrl | None = None
    PAGINATION_PER_PAGE: int = 20

    REDIS_URL: RedisDsn

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    DATABASE_URI: PostgresDsn
    

    SES_ACCESS_KEY: str | None = None
    SES_SECRET_KEY: str | None = None
    SES_REGION: str | None = None
    RESEND_API_KEY: str | None = None
    DEFAULT_FROM_EMAIL: EmailStr
    DEFAULT_FROM_NAME: str | None = None
    EMAILS_ENABLED: bool = False
    
    # Financial API Configuration
    ALPHA_VANTAGE_API_KEY: str | None = None

    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # Scraping configuration
    SCRAPE_USER_AGENT: str = "OpenAlpha-Bot/1.0"
    SCRAPE_MIN_DELAY_SECONDS: float = 2.0

    model_config = ConfigDict(env_file=".env")


settings = Settings()
