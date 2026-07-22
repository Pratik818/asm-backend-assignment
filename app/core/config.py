from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "ASM Asset Discovery Service"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Single source of truth for Postgres credentials — reused by both the
    # docker-compose "db" service and this connection string, so there is
    # nothing left to keep in sync manually. postgres_host/postgres_port
    # default to the values correct *inside* the docker-compose network;
    # override them (e.g. POSTGRES_HOST=localhost) only when running the API
    # directly on the host against the dockerized Postgres.
    postgres_user: str = "postgres"
    postgres_password: str = "asm@postgres"
    postgres_db: str = "asm_db"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Same reasoning for Redis/Celery.
    redis_host: str = "redis"
    redis_port: int = 6379

    jwt_secret_key: str = "change-me-in-production-this-default-is-not-secret-at-all"
    jwt_algorithm: str = "HS256"
    jwt_expire_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def celery_result_backend(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
