from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / '.env'),  # load project-root .env reliably during tests
        case_sensitive=False,  # typical for envs
        extra='ignore',  # ignore unknown env vars
    )

    env: Literal['development', 'production', 'testing'] = 'production'
    app_name: str = 'Accentra'
    debug: bool | None = None
    version: str = '0.1.0'
    admin_email: str = 'support@riskary.de'

    # Accept several common environment variable names for DB/Redis URLs
    postgres_url: SecretStr = Field(validation_alias=AliasChoices('POSTGRES_URL', 'DATABASE_URL', 'POSTGRESQL_URL'))
    redis_url: SecretStr = Field(validation_alias=AliasChoices('REDIS_URL', 'REDIS_URI'))

    # JWT/Auth configuration
    jwt_secret_key: SecretStr = SecretStr('dev-secret-key')
    jwt_algorithm: Literal['HS256'] = 'HS256'
    jwt_access_token_ttl_minutes: int = 60
    jwt_issuer: str | None = None
    jwt_audience: str | None = None

    log_level: Literal['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'] = 'INFO'
    otlp_endpoint: str | None = None
    otlp_headers: str | None = None
    otel_logs_enabled: bool = False
    otel_traces_enabled: bool = True
    otel_metrics_enabled: bool = True
    internal_auth_token: SecretStr = SecretStr('dev-internal-token')

    @property
    def pg_vector_url(self) -> SecretStr:
        """Returns the PostgreSQL database URL for PGVector.
        Converts 'postgres://' to 'postgresql://' if needed.
        """
        url = self.postgres_url.get_secret_value()
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return SecretStr(url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[missing-argument]
