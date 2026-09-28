import math
from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from fastapi import Query, status as http_status
from fastapi.responses import JSONResponse
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiError(CamelModel):
    field: Optional[str] = None
    message: str


class PageMetadata(CamelModel):
    current_page: int
    page_size: int
    total_pages: int
    total_items: int

    @classmethod
    def of(cls, page: int, size: int, total_items: int) -> "PageMetadata":
        total_pages = math.ceil(total_items / size) if size > 0 else 0
        return cls(
            current_page=page,
            page_size=size,
            total_pages=total_pages,
            total_items=total_items,
        )


class ApiResponse(CamelModel, Generic[T]):
    status: str
    message: str
    error_code: Optional[str] = None
    data: Optional[T] = None
    metadata: Optional[PageMetadata] = None
    errors: Optional[List[ApiError]] = None
    path: Optional[str] = None
    timestamp: str

    @classmethod
    def success(
        cls,
        message: str,
        data: Optional[T] = None,
        metadata: Optional[PageMetadata] = None,
    ) -> "ApiResponse[T]":
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(
            status="success",
            message=message,
            data=data,
            metadata=metadata,
            timestamp=now_utc,
        )

    @classmethod
    def error(
        cls,
        error_code: str,
        message: str,
        path: str,
        errors: Optional[List[ApiError]] = None,
    ) -> "ApiResponse[None]":
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return cls(
            status="error",
            message=message,
            error_code=error_code,
            data=None,
            errors=errors,
            path=path,
            timestamp=now_utc,
        )


def respond(
    response: ApiResponse[Any],
    status_code: int = http_status.HTTP_200_OK,
    headers: Optional[dict] = None,
) -> JSONResponse:
    # Always include data, omit null optional fields
    data_dict = response.model_dump(by_alias=True, exclude_none=True)
    if "data" not in data_dict:
        data_dict["data"] = None
    return JSONResponse(
        content=data_dict,
        status_code=status_code,
        headers=headers,
    )


class PageParams:
    def __init__(
        self,
        page: int = Query(0, ge=0, description="Zero-based page index"),
        size: int = Query(10, ge=1, le=100, description="Page size (1-100)"),
    ):
        self.page = page
        self.size = size
