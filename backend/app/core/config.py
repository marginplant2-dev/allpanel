"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    app_name: str = "SportX"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "sportx"

    # Security / JWT
    jwt_secret_key: str = "change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Providers
    sports_provider: str = "mock"
    games_provider: str = "mock"
    sports_api_key: str = ""

    # proexch exchange feed: access is granted per IP/domain, not per key, so the
    # outbound call must leave from the whitelisted server and carry the approved
    # domain in Origin/Referer.
    proexch_base_url: str = "https://apidata.proexch.in"
    proexch_origin: str = ""

    # Rate limiting (per client IP, applied to the API prefix)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 300
    rate_limit_window_seconds: int = 60

    # Bootstrap super admin
    superadmin_username: str = "superadmin"
    superadmin_password: str = "ChangeMe123!"
    superadmin_fullname: str = "Platform Owner"
    superadmin_initial_credits: int = 1_000_000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [o.strip() for o in value.split(",") if o.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
