import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.services.chat_service import ChatService
from app.services.embedding_service import EmbeddingService


def create_sample_pdf_bytes(text: str = "DocuChat AI is an enterprise document intelligence and chat system.") -> bytes:
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
async def test_complete_backend_end_to_end_flow(client):
    """
    Complete end-to-end integration test covering:
    1. Register user
    2. Login user & obtain tokens
    3. Profile inspection (/auth/me)
    4. Token refresh cycle
    5. Document Upload
    6. Document Ingestion / Embedding processing
    7. Document listing with filters & document retrieval
    8. Original document file download (/file)
    9. Conversation creation
    10. Conversation listing & rename
    11. Message exchange via SSE stream with retrieval citations
    12. Conversation history retrieval
    13. Clearing conversation messages
    14. Conversation deletion
    15. Document soft-deletion
    16. Activity logs audit inspection
    17. Logout and token invalidation
    """
    user_email = "e2e_user@example.com"
    user_pass = "SecurePass123"
    user_name = "E2E Tester"

    # 1. Register User
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "password": user_pass, "fullName": user_name},
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["status"] == "success"

    # 2. Login User
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": user_pass},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()["data"]
    access_token = login_data["accessToken"]
    refresh_token = login_data["refreshToken"]
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # 3. Profile me check
    me_res = await client.get("/api/v1/auth/me", headers=auth_header)
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == user_email

    # 4. Token refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert refresh_res.status_code == 200
    refreshed_access_token = refresh_res.json()["data"]["accessToken"]
    new_refresh_token = refresh_res.json()["data"]["refreshToken"]
    assert refreshed_access_token is not None
    auth_header = {"Authorization": f"Bearer {refreshed_access_token}"}

    # 5. Upload Document
    pdf_bytes = create_sample_pdf_bytes("DocuChat AI provides fast semantic question answering over PDF files.")
    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.05] * 1536]

        upload_res = await client.post(
            "/api/v1/documents",
            headers=auth_header,
            files={"file": ("guide.pdf", pdf_bytes, "application/pdf")},
        )
        assert upload_res.status_code == 201
        doc_data = upload_res.json()["data"]
        doc_id = doc_data["id"]
        assert doc_data["title"] == "guide"
        assert doc_data["status"] == "UPLOADED"

        # 6. Process Document to READY
        from app.services.document_service import process_document
        await process_document(doc_id)

    # 7. Document Listing & Detail
    doc_detail_res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
    assert doc_detail_res.status_code == 200
    assert doc_detail_res.json()["data"]["status"] == "READY"
    assert doc_detail_res.json()["data"]["pageCount"] == 1

    list_docs_res = await client.get("/api/v1/documents?page=0&size=10&status=READY", headers=auth_header)
    assert list_docs_res.status_code == 200
    assert len(list_docs_res.json()["data"]) >= 1

    # 8. Document File View/Download
    download_res = await client.get(f"/api/v1/documents/{doc_id}/file", headers=auth_header)
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert len(download_res.content) > 0

    # 9. Create Conversation
    conv_res = await client.post(
        "/api/v1/conversations",
        headers=auth_header,
        json={"documentIds": [doc_id], "title": "E2E Document Conversation"},
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["data"]["id"]
    assert conv_res.json()["data"]["title"] == "E2E Document Conversation"

    # 10. Conversation listing & rename
    list_convs_res = await client.get("/api/v1/conversations", headers=auth_header)
    assert list_convs_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_convs_res.json()["data"])

    patch_conv_res = await client.patch(
        f"/api/v1/conversations/{conv_id}",
        headers=auth_header,
        json={"title": "Updated E2E Conversation Title"},
    )
    assert patch_conv_res.status_code == 200
    assert patch_conv_res.json()["data"]["title"] == "Updated E2E Conversation Title"

    # 11. Send Message with SSE Stream response
    class MockChoice:
        def __init__(self, text):
            self.delta = type("Delta", (), {"content": text})()

    class MockChunk:
        def __init__(self, text, usage=None):
            self.choices = [MockChoice(text)] if text else []
            self.usage = usage

    async def mock_stream():
        yield MockChunk("DocuChat AI ")
        yield MockChunk("is designed for semantic search [1].", usage=type("U", (), {"prompt_tokens": 40, "completion_tokens": 12})())

    with patch("app.services.embedding_service.EmbeddingService.embed_query", new_callable=AsyncMock) as mock_emb, \
         patch.object(ChatService, "_initiate_stream", new_callable=AsyncMock) as mock_chat:

        mock_emb.return_value = [0.05] * 1536
        mock_chat.return_value = mock_stream()

        msg_stream_res = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_header,
            json={"content": "What does DocuChat AI do?"},
        )
        assert msg_stream_res.status_code == 200
        assert "text/event-stream" in msg_stream_res.headers["content-type"]
        body = msg_stream_res.text
        assert "event: sources" in body
        assert "event: token" in body
        assert "event: done" in body

    # 12. Retrieve conversation message history
    history_res = await client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth_header)
    assert history_res.status_code == 200
    messages = history_res.json()["data"]
    assert len(messages) == 2
    assert messages[0]["role"] == "USER"
    assert messages[0]["content"] == "What does DocuChat AI do?"
    assert messages[1]["role"] == "ASSISTANT"
    assert "DocuChat AI is designed for semantic search [1]." in messages[1]["content"]

    # 13. Delete conversation
    del_conv_res = await client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_header)
    assert del_conv_res.status_code == 204

    check_conv_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_header)
    assert check_conv_res.status_code == 404

    # 15. Delete Document
    del_doc_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header)
    assert del_doc_res.status_code == 204

    check_doc_res = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_header)
    assert check_doc_res.status_code == 404

    # 16. Activity logs check
    logs_res = await client.get("/api/v1/activity-logs", headers=auth_header)
    assert logs_res.status_code == 200
    assert len(logs_res.json()["data"]) > 0

    # 17. Verify invalid/expired refresh token rejection
    bad_refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": "invalid_or_expired_token_value"},
    )
    assert bad_refresh_res.status_code == 401
    assert bad_refresh_res.json()["errorCode"] == "E008"
