from datetime import datetime, timedelta, timezone
import logging
from typing import AsyncGenerator
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import request_id_ctx_var, setup_logging
from app.exceptions.handlers import register_exception_handlers
from app.repositories.document_repo import DocumentRepository
from app.routers import activity_logs, auth, conversations, documents, health

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityAndTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate X-Request-ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx_var.set(req_id)

        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)

        # Attach request ID header
        response.headers["X-Request-ID"] = req_id

        # Attach security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


async def recover_stuck_documents() -> None:
    """Finds documents stuck in PROCESSING for more than 15 minutes and marks them FAILED."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        async with AsyncSessionLocal() as session:
            repo = DocumentRepository(session)
            stale_ids = await repo.mark_stale_processing_as_failed(cutoff, error_code="E999")
            await session.commit()
            if stale_ids:
                logger.warning(
                    f"Startup recovery: marked {len(stale_ids)} stuck processing documents as FAILED: {stale_ids}"
                )
    except Exception as exc:
        logger.warning(f"Startup recovery encountered error: {exc}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    await recover_stuck_documents()
    yield


app = FastAPI(
    title="DocuChat AI",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    lifespan=lifespan,
)

# Custom security & tracing middleware
app.add_middleware(SecurityAndTracingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(activity_logs.router, prefix="/api/v1")
