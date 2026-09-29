import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel

from app.core.config import Settings
from app.models.document import Document
from app.schemas.activity_log import ActivityLogResponse
from app.schemas.auth import TokenResponse, UserResponse
from app.schemas.conversation import ConversationResponse
from app.schemas.document import DocumentResponse
from app.schemas.message import MessageResponse


@pytest_asyncio.fixture
async def setup_two_users(client):
    # User A
    await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "Password123", "fullName": "User A"},
    )
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "Password123"},
    )
    token_a = login_a.json()["data"]["accessToken"]

    # User B
    await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "Password123", "fullName": "User B"},
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.com", "password": "Password123"},
    )
    token_b = login_b.json()["data"]["accessToken"]

    return {"token_a": token_a, "token_b": token_b}


def test_no_sensitive_fields_in_schemas():
    """
    Ensure is_active, is_deleted, password_hash, and file_path never exist on response DTOs.
    """
    forbidden_fields = {"is_active", "isActive", "is_deleted", "isDeleted", "password_hash", "passwordHash", "file_path", "filePath"}

    schema_classes = [
        UserResponse,
        TokenResponse,
        DocumentResponse,
        ConversationResponse,
        MessageResponse,
        ActivityLogResponse,
    ]

    for cls in schema_classes:
        fields = set(cls.model_fields.keys())
        for f in fields:
            assert f not in forbidden_fields, f"Forbidden field '{f}' found on schema {cls.__name__}"


def test_config_validation():
    """
    Test that invalid configuration (missing database url or short JWT secret in prod) raises ValueError.
    """
    # 1. Missing DATABASE_URL
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(DATABASE_URL="")

    # 2. Short secret in production
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="short_secret",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/docuchat",
            AZURE_OPENAI_ENDPOINT="https://res.openai.azure.com/",
            AZURE_OPENAI_API_KEY="key",
        )


@pytest.mark.asyncio
async def test_security_headers_and_request_id(client, setup_two_users):
    token_a = setup_two_users["token_a"]
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_a}", "X-Request-ID": "custom-req-id-123"},
    )
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == "custom-req-id-123"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"


def create_valid_pdf_bytes(text: str = "User A valid document text.") -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 300 144]/Parent 2 0 R/Resources<<\n"
        b"/Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length " + str(len(text) + 40).encode() + b">>\n"
        b"stream\n"
        b"BT\n/F1 12 Tf\n10 100 Td\n(" + text.encode() + b") Tj\nET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000056 00000 n \n"
        b"0000000111 00000 n \n0000000212 00000 n \n"
        b"0000000287 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n400\n%%EOF\n"
    )


@pytest.mark.asyncio
async def test_cross_user_isolation(client, setup_two_users):
    token_a = setup_two_users["token_a"]
    token_b = setup_two_users["token_b"]

    # 1. User A uploads a document
    pdf_bytes = create_valid_pdf_bytes("User A valid document text.")
    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1] * 1536]
        upload_res = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"file": ("user_a.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload_res.status_code == 201
        doc_a_id = upload_res.json()["data"]["id"]

        from app.services.document_service import process_document
        await process_document(doc_a_id)

    # User B cannot get User A's document
    res = await client.get(f"/api/v1/documents/{doc_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404
    assert res.json()["errorCode"] == "E003"

    # User B cannot get User A's document file
    res = await client.get(f"/api/v1/documents/{doc_a_id}/file", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404

    # User B cannot delete User A's document
    res = await client.delete(f"/api/v1/documents/{doc_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404

    # 2. User A creates a conversation
    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"documentIds": [doc_a_id], "title": "User A Chat"},
    )
    assert conv_res.status_code == 201
    conv_a_id = conv_res.json()["data"]["id"]

    # User B cannot get User A's conversation
    res = await client.get(f"/api/v1/conversations/{conv_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404
    assert res.json()["errorCode"] == "E004"

    # User B cannot list messages of User A's conversation
    res = await client.get(f"/api/v1/conversations/{conv_a_id}/messages", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404

    # User B cannot rename User A's conversation
    res = await client.patch(
        f"/api/v1/conversations/{conv_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Hacked Title"},
    )
    assert res.status_code == 404

    # User B cannot delete User A's conversation
    res = await client.delete(f"/api/v1/conversations/{conv_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404

    # 3. User B activity logs only show User B actions
    logs_b_res = await client.get("/api/v1/activity-logs", headers={"Authorization": f"Bearer {token_b}"})
    assert logs_b_res.status_code == 200
    logs_b = logs_b_res.json()["data"]
    # User B only registered and logged in, should not have DOCUMENT_UPLOAD
    actions_b = [l["action"] for l in logs_b]
    assert "DOCUMENT_UPLOAD" not in actions_b
    assert "CONVERSATION_CREATE" not in actions_b
