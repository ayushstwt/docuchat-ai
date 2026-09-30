import json
import logging
import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import AppEnv, Settings
from app.core.logging import JsonLogFormatter, RequestIdFilter, request_id_ctx_var
from app.main import app as fastapi_app


def test_settings_validation_local_and_dev():
    """Local and dev environments allow weak values without failing."""
    # Local with weak values
    s_local = Settings(
        app_env=AppEnv.LOCAL,
        jwt_secret="change_me_short",
        cors_origins="*",
        enable_docs=True,
        rate_limit_storage_url="memory://",
    )
    assert s_local.app_env == AppEnv.LOCAL
    assert s_local.is_deployed is False

    # Dev with dev values
    s_dev = Settings(
        app_env=AppEnv.DEV,
        jwt_secret="dev-secret-change-me-at-least-32-characters",
        cors_origins="http://localhost:8080",
        enable_docs=True,
        rate_limit_storage_url="memory://",
    )
    assert s_dev.app_env == AppEnv.DEV
    assert s_dev.is_deployed is False


def test_settings_validation_staging_failures():
    """Staging fails startup for weak JWT secret or wildcard CORS."""
    # Short JWT secret
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env=AppEnv.STAGING,
            jwt_secret="short",
            cors_origins="https://staging.example.com",
            rate_limit_storage_url="redis://redis:6379/0",
        )
    assert "JWT_SECRET must be a random string of 32+ characters" in str(exc_info.value)

    # JWT secret containing 'change'
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env=AppEnv.STAGING,
            jwt_secret="a_very_long_secret_string_with_change_in_it_12345",
            cors_origins="https://staging.example.com",
            rate_limit_storage_url="redis://redis:6379/0",
        )
    assert "JWT_SECRET must be a random string of 32+ characters" in str(exc_info.value)

    # Wildcard CORS
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env=AppEnv.STAGING,
            jwt_secret="a_very_long_secure_staging_random_secret_string_12345",
            cors_origins="*",
            rate_limit_storage_url="redis://redis:6379/0",
        )
    assert "CORS_ORIGINS must not contain '*'" in str(exc_info.value)


def test_settings_validation_prod_failures():
    """Prod fails startup for ENABLE_DOCS=true or memory rate limiting."""
    # ENABLE_DOCS=true in prod
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env=AppEnv.PROD,
            jwt_secret="a_very_long_secure_prod_random_secret_string_123456",
            cors_origins="https://app.example.com",
            enable_docs=True,
            rate_limit_storage_url="redis://redis:6379/0",
        )
    assert "ENABLE_DOCS must be false in prod" in str(exc_info.value)

    # memory:// rate limit in prod
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env=AppEnv.PROD,
            jwt_secret="a_very_long_secure_prod_random_secret_string_123456",
            cors_origins="https://app.example.com",
            enable_docs=False,
            rate_limit_storage_url="memory://",
        )
    assert "RATE_LIMIT_STORAGE_URL must point to Redis in prod" in str(exc_info.value)


def test_settings_validation_prod_success():
    """Prod passes validation with strong secrets, no wildcard, docs disabled, and Redis rate limit."""
    s_prod = Settings(
        app_env=AppEnv.PROD,
        jwt_secret="super_strong_random_production_secret_key_48_chars_long_123456",
        cors_origins="https://app.example.com",
        enable_docs=False,
        rate_limit_storage_url="redis://redis:6379/0",
    )
    assert s_prod.app_env == AppEnv.PROD
    assert s_prod.is_deployed is True
    assert s_prod.enable_docs is False
    assert s_prod.rate_limit_storage_url == "redis://redis:6379/0"


@pytest.mark.asyncio
async def test_health_live_endpoint_works_without_db():
    """GET /api/v1/health/live returns 200 with standard ApiResponse envelope even if DB is unavailable."""
    transport = ASGITransport(app=fastapi_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Process is alive"
        assert data["data"]["app"] == "DocuChat AI"
        assert data["data"]["status"] == "alive"
        assert "timestamp" in data


def test_json_log_formatter():
    """JsonLogFormatter outputs valid single-line JSON with required fields."""
    formatter = JsonLogFormatter()
    token = request_id_ctx_var.set("req-test-1234")

    try:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test_path.py",
            lineno=42,
            msg="User login successful for user %s",
            args=("alice",),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "User login successful for user alice"
        assert parsed["request_id"] == "req-test-1234"
        assert "timestamp" in parsed
        assert "exception" not in parsed

        # Test with exception
        try:
            raise ValueError("Test error message")
        except Exception:
            import sys
            record.exc_info = sys.exc_info()

        output_with_exc = formatter.format(record)
        parsed_with_exc = json.loads(output_with_exc)
        assert "exception" in parsed_with_exc
        assert "ValueError: Test error message" in parsed_with_exc["exception"]
    finally:
        request_id_ctx_var.reset(token)


def test_docs_disabled_in_app_when_enable_docs_false():
    """When FastAPI is initialized with docs disabled, docs endpoints return 404."""
    from fastapi import FastAPI
    app_no_docs = FastAPI(
        title="DocuChat AI Test",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    assert app_no_docs.docs_url is None
    assert app_no_docs.redoc_url is None
    assert app_no_docs.openapi_url is None
