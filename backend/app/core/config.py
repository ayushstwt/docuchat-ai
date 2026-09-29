from functools import lru_cache
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/docuchat_db"

    JWT_SECRET: str = "replace_with_a_secure_random_jwt_secret_key_minimum_32_chars"
    JWT_ACCESS_MINUTES: int = 60
    JWT_REFRESH_DAYS: int = 7

    AZURE_OPENAI_ENDPOINT: str = "https://your-resource-name.openai.azure.com/"
    AZURE_OPENAI_API_KEY: str = "your_azure_openai_api_key"
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 20

    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_required_settings(self) -> "Settings":
        # Check required fields
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required.")
        if not self.JWT_SECRET:
            raise ValueError("JWT_SECRET environment variable is required.")
        if not self.AZURE_OPENAI_ENDPOINT or not self.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required.")

        # In non-development environment, enforce min length of 32 for JWT_SECRET
        if self.APP_ENV != "development" and len(self.JWT_SECRET) < 32:
            raise ValueError(
                f"JWT_SECRET must be at least 32 characters in non-development environment (APP_ENV={self.APP_ENV})."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
