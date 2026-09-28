import pytest
from httpx import AsyncClient
from pydantic import BaseModel, Field

from app.constants.error_codes import ErrorCode
from app.exceptions.base import NotFoundException
from app.main import app
from app.schemas.common import ApiResponse, respond


class DummyBody(BaseModel):
    name: str = Field(..., min_length=3)
    count: int = Field(..., gt=0)


@app.get("/api/v1/test/secret-error")
async def trigger_secret_error():
    raise RuntimeError("sensitive_database_password_or_token")


@app.get("/api/v1/test/custom-not-found")
async def trigger_custom_not_found():
    raise NotFoundException(ErrorCode.DOCUMENT_NOT_FOUND, 123)


@app.post("/api/v1/test/validate")
async def trigger_validation(body: DummyBody):
    return respond(ApiResponse.success(message="Validated successfully", data={"name": body.name}))


@pytest.mark.asyncio
async def test_health_check_shape(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["message"] == "System status"
    assert "data" in json_data
    assert json_data["data"]["app"] == "DocuChat AI"
    assert json_data["timestamp"].endswith("Z")
    assert "errorCode" not in json_data
    assert "errors" not in json_data


@pytest.mark.asyncio
async def test_404_unknown_route(client: AsyncClient):
    response = await client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E001"
    assert json_data["data"] is None
    assert json_data["path"] == "/api/v1/non-existent-endpoint"
    assert json_data["timestamp"].endswith("Z")


@pytest.mark.asyncio
async def test_validation_error_envelope(client: AsyncClient):
    response = await client.post("/api/v1/test/validate", json={"name": "a", "count": -1})
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E005"
    assert json_data["data"] is None
    assert isinstance(json_data["errors"], list)
    assert len(json_data["errors"]) >= 2
    fields = [err["field"] for err in json_data["errors"]]
    assert "name" in fields
    assert "count" in fields


@pytest.mark.asyncio
async def test_app_exception_envelope(client: AsyncClient):
    response = await client.get("/api/v1/test/custom-not-found")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E003"
    assert "Document with id 123 not found" in json_data["message"]
    assert json_data["path"] == "/api/v1/test/custom-not-found"
    assert json_data["data"] is None


@pytest.mark.asyncio
async def test_catch_all_exception_does_not_leak_message(client: AsyncClient):
    response = await client.get("/api/v1/test/secret-error")
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["status"] == "error"
    assert json_data["errorCode"] == "E999"
    assert json_data["message"] == "An unexpected error occurred. Please try again later"
    assert "sensitive_database_password" not in response.text
    assert json_data["data"] is None
    assert json_data["path"] == "/api/v1/test/secret-error"
