import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os

from app.constants.error_codes import ErrorCode
from app.exceptions.base import ServiceException
from app.services.embedding_service import EmbeddingService, _is_retryable_error
from app.services.pdf_service import PdfService
from app.core.security import hash_password, verify_password


def test_is_retryable_error():
    class Err429(Exception):
        status_code = 429

    class Err500(Exception):
        status_code = 500

    class Err400(Exception):
        status_code = 400

    class TimeoutErr(Exception):
        pass

    assert _is_retryable_error(Err429()) is True
    assert _is_retryable_error(Err500()) is True
    assert _is_retryable_error(Err400()) is False
    assert _is_retryable_error(TimeoutErr()) is True
    assert _is_retryable_error(ValueError("invalid value")) is False


@pytest.mark.asyncio
async def test_embedding_service_empty_text():
    service = EmbeddingService()
    res = await service.embed_texts([])
    assert res == []


@pytest.mark.asyncio
async def test_embedding_service_batching():
    service = EmbeddingService()

    async def mock_create(input, model):
        return MagicMock(data=[MagicMock(embedding=[0.1, 0.2]) for _ in input])

    with patch.object(service.client.embeddings, "create", side_effect=mock_create) as mock_fn:
        texts = [f"Text chunk {i}" for i in range(5)]
        embeddings = await service.embed_texts(texts, batch_size=2)

        assert len(embeddings) == 5
        # With batch_size=2 and 5 items, create should be called 3 times (2 + 2 + 1)
        assert mock_fn.call_count == 3


@pytest.mark.asyncio
async def test_embedding_service_failure_raises_service_exception():
    service = EmbeddingService()

    with patch.object(service.client.embeddings, "create", side_effect=Exception("Permanent API Error")):
        with pytest.raises(ServiceException) as exc_info:
            await service.embed_texts(["hello"])
        assert exc_info.value.error == ErrorCode.AI_SERVICE_UNAVAILABLE


def test_pdf_service_chunk_pages_token_bounds():
    pdf_service = PdfService()
    # Create pages
    pages = [
        (1, "This is page one with some sample content that explains the system."),
        (2, "This is page two containing additional important context for testing."),
    ]
    chunks = pdf_service.chunk_pages(pages, target_chunk_tokens=50, overlap_tokens=10)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert "chunk_index" in chunk
        assert "page_number" in chunk
        assert "content" in chunk
        assert "token_count" in chunk
        assert chunk["token_count"] > 0


def test_pdf_service_empty_pages_raises_exception():
    pdf_service = PdfService()
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
        # Write empty minimal pdf without text
        tmp.write(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 300 144]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n180\n%%EOF\n"
        )
    
    try:
        with pytest.raises(ServiceException) as exc_info:
            pdf_service.extract_pages(tmp_path)
        assert exc_info.value.error == ErrorCode.PDF_NO_TEXT
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_password_hashing():
    hashed = hash_password("MySecurePass123!")
    assert hashed != "MySecurePass123!"
    assert verify_password("MySecurePass123!", hashed) is True
    assert verify_password("WrongPassword", hashed) is False
