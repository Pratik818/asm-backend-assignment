from functools import lru_cache
from typing import Any, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    APP_NAME: str = "ASM Asset Discovery Service"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "asm@postgres"
    POSTGRES_DB: str = "asm_db"
    # "localhost" is correct for running the API directly or running pytest,
    # both always on the host machine. docker-compose.yml sets POSTGRES_HOST
    # explicitly to "db" for the api/worker containers, overriding this.
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Dedicated database for the pytest suite (tests/conftest.py) — always
    # this name, on the same Postgres server, regardless of POSTGRES_DB
    # above. Keeps test runs isolated from real data without needing an
    # env var override.
    POSTGRES_TEST_DB: str = "asm_db_test"

    # Same reasoning as POSTGRES_HOST — docker-compose.yml overrides this to
    # "redis" for the api/worker containers.
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    JWT_SECRET_KEY: str = "change-me-in-production-this-default-is-not-secret-at-all"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_SECONDS: int = 3600

    DNS_RESOLVE_TIMEOUT: float = 3.0
    DNS_RESOLVE_RETRIES: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _blank_values_use_defaults(cls, data: Any) -> Any:
        # docker-compose's `env_file:` (unlike its `${VAR:-default}` syntax)
        # passes an empty value through as a real empty string, not "unset" —
        # so an untouched .env.example line like `POSTGRES_USER=` would
        # otherwise override this field's default with "". Treat blank the
        # same as absent for every field, matching Compose's own semantics.
        if isinstance(data, dict):
            return {key: value for key, value in data.items() if value != ""}
        return data

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def celery_result_backend(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
