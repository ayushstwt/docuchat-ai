import logging
from typing import List
from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.constants.error_codes import ErrorCode
from app.core.config import get_settings
from app.exceptions.base import ServiceException

logger = logging.getLogger(__name__)
settings = get_settings()


def _is_retryable_error(exc: BaseException) -> bool:
    """
    Check if the exception from Azure OpenAI is retryable:
    429 (rate limit), 5xx (server error), or timeout/connection errors.
    """
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        if status_code == 429 or status_code >= 500:
            return True
    exc_name = exc.__class__.__name__.lower()
    if "timeout" in exc_name or "connection" in exc_name or "rate" in exc_name:
        return True
    return False


class EmbeddingService:
    def __init__(self) -> None:
        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self.deployment_name = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT

    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_retryable_error),
    )
    async def _call_embeddings_with_retry(self, texts: List[str]) -> List[List[float]]:
        # Never log API keys or full user text
        logger.debug(f"Calling Azure OpenAI embeddings for batch of size {len(texts)}")
        response = await self.client.embeddings.create(
            input=texts,
            model=self.deployment_name,
        )
        return [item.embedding for item in response.data]

    async def embed_texts(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """
        Embeds a list of texts in batches of max 16 items.
        Retries up to 4 attempts on 429/5xx/timeouts with exponential backoff.
        Converts final failures to ServiceException(ErrorCode.AI_SERVICE_UNAVAILABLE).
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []

        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                batch_embeddings = await self._call_embeddings_with_retry(batch)
                all_embeddings.extend(batch_embeddings)
            return all_embeddings
        except ServiceException:
            raise
        except Exception as e:
            logger.error(f"Embedding generation failed: {type(e).__name__}")
            raise ServiceException(ErrorCode.AI_SERVICE_UNAVAILABLE) from e

    async def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single query string.
        """
        embeddings = await self.embed_texts([text])
        if not embeddings:
            raise ServiceException(ErrorCode.AI_SERVICE_UNAVAILABLE)
        return embeddings[0]
