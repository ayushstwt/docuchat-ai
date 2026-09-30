from enum import Enum
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class Settings(BaseSettings):
    # Docker injects env vars (.env is not packaged in image); locally .env is read.
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = AppEnv.LOCAL
    log_level: str = "INFO"
    log_format: str = "text"  # "text" | "json"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/docuchat_db"
    db_pool_size: int = 5
    db_max_overflow: int = 5

    jwt_secret: str = "replace_with_a_secure_random_jwt_secret_key_minimum_32_chars"
    jwt_access_minutes: int = 30
    jwt_refresh_days: int = 7

    azure_openai_endpoint: str = "https://your-resource-name.openai.azure.com/"
    azure_openai_api_key: str = "your_azure_openai_api_key"
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    upload_dir: str = "./uploads"
    max_upload_mb: int = 20
    cors_origins: str = ""
    enable_docs: bool = True
    rate_limit_storage_url: str = "memory://"

    @field_validator("app_env", mode="before")
    @classmethod
    def parse_app_env(cls, v: Union[str, AppEnv]) -> AppEnv:
        if isinstance(v, AppEnv):
            return v
        if isinstance(v, str):
            val = v.lower().strip()
            if val in ("development", "dev"):
                return AppEnv.DEV
            if val in ("test", "testing", "local"):
                return AppEnv.LOCAL
            if val in ("stage", "staging"):
                return AppEnv.STAGING
            if val in ("production", "prod"):
                return AppEnv.PROD
            try:
                return AppEnv(val)
            except ValueError:
                pass
        return AppEnv.LOCAL

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        raw = self.cors_origins.strip()
        if raw.startswith("[") and raw.endswith("]"):
            import json
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def is_deployed(self) -> bool:
        return self.app_env in (AppEnv.STAGING, AppEnv.PROD)

    @model_validator(mode="after")
    def validate_for_environment(self) -> "Settings":
        """In Staging/Prod, unsafe or weak configurations fail startup immediately."""
        if not self.is_deployed:
            return self
        problems: list[str] = []
        if len(self.jwt_secret) < 32 or "change" in self.jwt_secret.lower():
            problems.append("JWT_SECRET must be a random string of 32+ characters")
        if "*" in self.cors_origins:
            problems.append("CORS_ORIGINS must not contain '*'")
        if self.app_env == AppEnv.PROD and self.enable_docs:
            problems.append("ENABLE_DOCS must be false in prod")
        if self.app_env == AppEnv.PROD and self.rate_limit_storage_url.startswith("memory://"):
            problems.append("RATE_LIMIT_STORAGE_URL must point to Redis in prod")
        if problems:
            raise ValueError("Invalid configuration: " + "; ".join(problems))
        return self

    # Compatibility properties for uppercase access with setters
    @property
    def APP_ENV(self) -> str:
        return self.app_env.value if isinstance(self.app_env, AppEnv) else str(self.app_env)

    @APP_ENV.setter
    def APP_ENV(self, value: Union[str, AppEnv]) -> None:
        self.app_env = self.parse_app_env(value)

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @DATABASE_URL.setter
    def DATABASE_URL(self, value: str) -> None:
        self.database_url = value

    @property
    def JWT_SECRET(self) -> str:
        return self.jwt_secret

    @JWT_SECRET.setter
    def JWT_SECRET(self, value: str) -> None:
        self.jwt_secret = value

    @property
    def JWT_ACCESS_MINUTES(self) -> int:
        return self.jwt_access_minutes

    @JWT_ACCESS_MINUTES.setter
    def JWT_ACCESS_MINUTES(self, value: int) -> None:
        self.jwt_access_minutes = value

    @property
    def JWT_REFRESH_DAYS(self) -> int:
        return self.jwt_refresh_days

    @JWT_REFRESH_DAYS.setter
    def JWT_REFRESH_DAYS(self, value: int) -> None:
        self.jwt_refresh_days = value

    @property
    def AZURE_OPENAI_ENDPOINT(self) -> str:
        return self.azure_openai_endpoint

    @AZURE_OPENAI_ENDPOINT.setter
    def AZURE_OPENAI_ENDPOINT(self, value: str) -> None:
        self.azure_openai_endpoint = value

    @property
    def AZURE_OPENAI_API_KEY(self) -> str:
        return self.azure_openai_api_key

    @AZURE_OPENAI_API_KEY.setter
    def AZURE_OPENAI_API_KEY(self, value: str) -> None:
        self.azure_openai_api_key = value

    @property
    def AZURE_OPENAI_API_VERSION(self) -> str:
        return self.azure_openai_api_version

    @AZURE_OPENAI_API_VERSION.setter
    def AZURE_OPENAI_API_VERSION(self, value: str) -> None:
        self.azure_openai_api_version = value

    @property
    def AZURE_OPENAI_CHAT_DEPLOYMENT(self) -> str:
        return self.azure_openai_chat_deployment

    @AZURE_OPENAI_CHAT_DEPLOYMENT.setter
    def AZURE_OPENAI_CHAT_DEPLOYMENT(self, value: str) -> None:
        self.azure_openai_chat_deployment = value

    @property
    def AZURE_OPENAI_EMBEDDING_DEPLOYMENT(self) -> str:
        return self.azure_openai_embedding_deployment

    @AZURE_OPENAI_EMBEDDING_DEPLOYMENT.setter
    def AZURE_OPENAI_EMBEDDING_DEPLOYMENT(self, value: str) -> None:
        self.azure_openai_embedding_deployment = value

    @property
    def EMBEDDING_DIMENSIONS(self) -> int:
        return self.embedding_dimensions

    @EMBEDDING_DIMENSIONS.setter
    def EMBEDDING_DIMENSIONS(self, value: int) -> None:
        self.embedding_dimensions = value

    @property
    def UPLOAD_DIR(self) -> str:
        return self.upload_dir

    @UPLOAD_DIR.setter
    def UPLOAD_DIR(self, value: str) -> None:
        self.upload_dir = value

    @property
    def MAX_UPLOAD_MB(self) -> int:
        return self.max_upload_mb

    @MAX_UPLOAD_MB.setter
    def MAX_UPLOAD_MB(self, value: int) -> None:
        self.max_upload_mb = value

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return self.cors_origin_list


@lru_cache
def get_settings() -> Settings:
    return Settings()
