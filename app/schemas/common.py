from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    provider: str | None = None


class ApiResponse(BaseModel):
    success: bool = True
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    data: Any = None
    source: list[str] = Field(default_factory=list)
    cached: bool = False
    warnings: list[str] = Field(default_factory=list)
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: ErrorDetail | None = None


def success_response(data: Any, source: list[str] | None = None, warnings: list[str] | None = None,
                     cached: bool = False) -> dict:
    return ApiResponse(
        success=True,
        data=data,
        source=source or [],
        cached=cached,
        warnings=warnings or [],
    ).model_dump()


def error_response(code: str, message: str, provider: str | None = None, warnings: list[str] | None = None) -> dict:
    return ApiResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, provider=provider),
        warnings=warnings or [],
    ).model_dump()
