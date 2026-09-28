import logging
from typing import Any
from fastapi import FastAPI, Request, status as http_status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.constants.error_codes import ErrorCode
from app.exceptions.base import AppException
from app.schemas.common import ApiError, ApiResponse, respond

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> Any:
        status_code = exc.error.http_status
        if status_code >= 500:
            logger.error(
                f"AppException {exc.error.code} on {request.url.path}: {exc.message}",
                exc_info=True,
            )
        else:
            logger.warning(
                f"AppException {exc.error.code} on {request.url.path}: {exc.message}"
            )

        envelope = ApiResponse.error(
            error_code=exc.error.code,
            message=exc.message,
            path=request.url.path,
        )
        return respond(envelope, status_code=status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> Any:
        errors = []
        for err in exc.errors():
            loc = err.get("loc", [])
            field_name = str(loc[-1]) if loc else None
            msg = err.get("msg", "Validation error")
            errors.append(ApiError(field=field_name, message=msg))

        logger.warning(
            f"Validation error on {request.url.path}: {errors}"
        )

        envelope = ApiResponse.error(
            error_code=ErrorCode.VALIDATION_FAILED.code,
            message=ErrorCode.VALIDATION_FAILED.message_template,
            path=request.url.path,
            errors=errors,
        )
        return respond(envelope, status_code=http_status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> Any:
        logger.warning(
            f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
        )
        code = "E001" if exc.status_code == 404 else f"E{exc.status_code}"
        envelope = ApiResponse.error(
            error_code=code,
            message=str(exc.detail),
            path=request.url.path,
        )
        return respond(envelope, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> Any:
        logger.error(
            f"Unhandled exception on {request.url.path}: {exc}",
            exc_info=True,
        )
        envelope = ApiResponse.error(
            error_code=ErrorCode.INTERNAL_ERROR.code,
            message=ErrorCode.INTERNAL_ERROR.message_template,
            path=request.url.path,
        )
        return respond(
            envelope,
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
