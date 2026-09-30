import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.constants.enums import DocumentStatus
from app.core.config import get_settings
from app.models.document import Document
from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService

settings = get_settings()


@pytest_asyncio.fixture
async def user_session(client):
    # Register user 1
    await client.post(
        "/api/v1/auth/register",
        json={"email": "chatuser@example.com", "password": "Password123", "fullName": "Chat User"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "chatuser@example.com", "password": "Password123"},
    )
    token = login_res.json()["data"]["accessToken"]

    # Register user 2
    await client.post(
        "/api/v1/auth/register",
        json={"email": "otheruser@example.com", "password": "Password123", "fullName": "Other User"},
    )
    login_res2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "otheruser@example.com", "password": "Password123"},
    )
    other_token = login_res2.json()["data"]["accessToken"]

    return {"token": token, "other_token": other_token}


def create_minimal_pdf_bytes(text: str = "Test document content") -> bytes:
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
async def test_create_conversation_non_ready_document_yields_409(client, user_session):
    token = user_session["token"]

    # Upload document with processing mocked so it stays in UPLOADED/PROCESSING state
    pdf_bytes = create_minimal_pdf_bytes("Doc for test")
    with patch("app.routers.documents.process_document", new_callable=AsyncMock):
        upload_res = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("unprocessed.pdf", pdf_bytes, "application/pdf")},
        )
    doc_id = upload_res.json()["data"]["id"]

    # Attempt to create conversation before document is READY
    create_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"documentIds": [doc_id], "title": "Test Chat"},
    )
    assert create_res.status_code == 409
    data = create_res.json()
    assert data["errorCode"] == "E013"


@pytest.mark.asyncio
async def test_create_conversation_foreign_or_missing_document_yields_404(client, user_session):
    token = user_session["token"]

    # Missing document
    create_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"documentIds": [9999], "title": "Missing Doc Chat"},
    )
    assert create_res.status_code == 404
    assert create_res.json()["errorCode"] == "E003"


@pytest.mark.asyncio
async def test_access_foreign_conversation_yields_404(client, user_session):
    token = user_session["token"]
    other_token = user_session["other_token"]

    # Upload and ready doc for user 1
    pdf_bytes = create_minimal_pdf_bytes("Ready document content")
    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1] * 1536]
        upload_res = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("ready.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_res.json()["data"]["id"]

        from app.services.document_service import process_document
        await process_document(doc_id)

    # Create conversation for user 1
    create_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"documentIds": [doc_id], "title": "User 1 Chat"},
    )
    assert create_res.status_code == 201
    conv_id = create_res.json()["data"]["id"]

    # User 2 tries to GET conversation
    get_res = await client.get(
        f"/api/v1/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert get_res.status_code == 404
    assert get_res.json()["errorCode"] == "E004"

    # User 2 tries to send message to user 1's conversation
    msg_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"content": "Hello!"},
    )
    assert msg_res.status_code == 404
    assert msg_res.json()["errorCode"] == "E004"


@pytest.mark.asyncio
async def test_sse_message_stream_flow(client, user_session):
    token = user_session["token"]

    # Upload and ready document
    pdf_bytes = create_minimal_pdf_bytes("DocuChat AI is great.")
    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1] * 1536]
        upload_res = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("docuchat.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_res.json()["data"]["id"]

        from app.services.document_service import process_document
        await process_document(doc_id)

    # Create conversation
    create_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"documentIds": [doc_id], "title": "DocuChat Conversation"},
    )
    conv_id = create_res.json()["data"]["id"]

    # Mock Azure OpenAI Chat stream & retrieval
    mock_chunks = [{
        "chunk_id": 1,
        "document_id": doc_id,
        "document_title": "docuchat",
        "page_number": 1,
        "content": "DocuChat AI is great.",
        "token_count": 5,
        "similarity": 0.95,
    }]

    class MockChoice:
        def __init__(self, t):
            self.delta = type("Delta", (), {"content": t})()

    class MockChunk:
        def __init__(self, t, usage=None):
            self.choices = [MockChoice(t)] if t is not None else []
            self.usage = usage

    async def mock_stream_gen():
        yield MockChunk("DocuChat ")
        yield MockChunk("is helpful [1].", usage=type("Usage", (), {"prompt_tokens": 50, "completion_tokens": 10})())

    with patch("app.services.embedding_service.EmbeddingService.embed_query", new_callable=AsyncMock) as mock_emb_query, \
         patch("app.services.retrieval_service.RetrievalService.search", new_callable=AsyncMock) as mock_search, \
         patch.object(ChatService, "_initiate_stream", new_callable=AsyncMock) as mock_chat_stream:

        mock_emb_query.return_value = [0.1] * 1536
        mock_search.return_value = mock_chunks
        mock_chat_stream.return_value = mock_stream_gen()

        # Send message via SSE endpoint
        response = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "What is DocuChat?"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        body_text = response.text
        # Verify event order: sources -> token -> done
        assert "event: sources" in body_text
        assert "event: token" in body_text
        assert "event: done" in body_text

        # Verify sources JSON
        sources_idx = body_text.find("event: sources")
        token_idx = body_text.find("event: token")
        done_idx = body_text.find("event: done")
        assert sources_idx < token_idx < done_idx

        # Check messages list
        list_msg_res = await client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_msg_res.status_code == 200
        messages_data = list_msg_res.json()["data"]
        assert len(messages_data) == 2
        assert messages_data[0]["role"] == "USER"
        assert messages_data[1]["role"] == "ASSISTANT"
        assert messages_data[1]["content"] == "DocuChat is helpful [1]."


@pytest.mark.asyncio
async def test_sse_stream_error_handling(client, user_session):
    token = user_session["token"]

    # Upload and ready doc
    pdf_bytes = create_minimal_pdf_bytes("Error test doc")
    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1] * 1536]
        upload_res = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("error_doc.pdf", pdf_bytes, "application/pdf")},
        )
        doc_id = upload_res.json()["data"]["id"]

        from app.services.document_service import process_document
        await process_document(doc_id)

    create_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={"documentIds": [doc_id], "title": "Error Conversation"},
    )
    conv_id = create_res.json()["data"]["id"]

    # Force an error during embedding retrieval
    with patch("app.services.embedding_service.EmbeddingService.embed_query", side_effect=Exception("Embedding Azure failure")):
        response = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "Trigger failure"},
        )
        assert response.status_code == 200
        body_text = response.text
        assert "event: error" in body_text
        assert "E999" in body_text
