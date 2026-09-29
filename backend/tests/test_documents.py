import io
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from pypdf import PdfWriter

from app.core.config import get_settings
from app.services.document_service import process_document

settings = get_settings()


def create_sample_pdf(text: str = "This is a test document content for testing ingestion.") -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    # Write a minimal PDF containing text stream so pypdf can extract it
    pdf_content = (
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
    return pdf_content


@pytest_asyncio.fixture
async def auth_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "docuser@example.com", "password": "Password123", "fullName": "Doc User"},
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "docuser@example.com", "password": "Password123"},
    )
    return login_res.json()["data"]["accessToken"]


@pytest.mark.asyncio
async def test_upload_non_pdf(client, auth_token):
    # 1. Invalid content-type / non-PDF
    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("test.txt", b"Hello world text", "text/plain")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["status"] == "error"
    assert data["errorCode"] == "E010"


@pytest.mark.asyncio
async def test_upload_fake_pdf_magic_bytes(client, auth_token):
    # content-type application/pdf but wrong magic bytes
    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("fake.pdf", b"NOT_A_PDF_CONTENT", "application/pdf")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["errorCode"] == "E010"


@pytest.mark.asyncio
async def test_upload_oversize_pdf(client, auth_token, monkeypatch):
    # Set MAX_UPLOAD_MB to 0 so even small files exceed
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 0)

    pdf_bytes = b"%PDF-1.4 simulated pdf data"
    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("large.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 413
    data = response.json()
    assert data["errorCode"] == "E011"


@pytest.mark.asyncio
async def test_valid_pdf_flow_ready_and_crud(client, auth_token):
    pdf_bytes = create_sample_pdf("Hello this is a valid extractable PDF content for testing docuchat.")

    with patch("app.services.embedding_service.EmbeddingService.embed_texts", new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [[0.1] * 1536]

        response = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("report.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 201
        assert "Location" in response.headers
        doc_data = response.json()["data"]
        doc_id = doc_data["id"]
        assert doc_data["title"] == "report"
        assert doc_data["originalFilename"] == "report.pdf"
        assert doc_data["status"] == "UPLOADED"

        # Explicitly run process_document to simulate the background worker in test environment
        await process_document(doc_id)

        # GET document
        get_res = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_res.status_code == 200
        data = get_res.json()["data"]
        assert data["status"] == "READY"
        assert data["pageCount"] >= 1

        # GET document file
        file_res = await client.get(
            f"/api/v1/documents/{doc_id}/file",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert file_res.status_code == 200
        assert file_res.headers["content-type"] == "application/pdf"

        # List documents
        list_res = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert list_res.status_code == 200
        assert len(list_res.json()["data"]) >= 1
        assert list_res.json()["metadata"]["totalItems"] >= 1


@pytest.mark.asyncio
async def test_user_cannot_access_other_user_document(client, auth_token):
    # Register user 2
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user2@example.com", "password": "Password123", "fullName": "User Two"},
    )
    login_res2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "user2@example.com", "password": "Password123"},
    )
    token2 = login_res2.json()["data"]["accessToken"]

    # Upload document with user 1
    pdf_bytes = create_sample_pdf("User 1 document content.")
    upload_res = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("user1_doc.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_res.json()["data"]["id"]

    # Try to access doc with user 2
    response = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 404
    assert response.json()["errorCode"] == "E003"


@pytest.mark.asyncio
async def test_delete_document_flow(client, auth_token):
    # Upload document
    pdf_bytes = create_sample_pdf("Document to be deleted.")
    upload_res = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {auth_token}"},
        files={"file": ("to_delete.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_res.json()["data"]["id"]

    # Delete doc
    del_res = await client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert del_res.status_code == 204

    # GET doc again -> 404 E003
    get_res = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_res.status_code == 404
    assert get_res.json()["errorCode"] == "E003"
