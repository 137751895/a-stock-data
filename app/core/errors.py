from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500, provider: str | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.provider = provider
        super().__init__(message)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=400)


class UpstreamHTTPError(AppError):
    def __init__(self, message: str, provider: str):
        super().__init__(code="UPSTREAM_HTTP_ERROR", message=message, status_code=502, provider=provider)


class UpstreamSchemaError(AppError):
    def __init__(self, message: str, provider: str):
        super().__init__(code="UPSTREAM_SCHEMA_ERROR", message=message, status_code=502, provider=provider)


class ProviderAuthError(AppError):
    def __init__(self, message: str, provider: str):
        super().__init__(code="PROVIDER_AUTH_ERROR", message=message, status_code=403, provider=provider)


def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    from app.schemas.common import error_response
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            provider=exc.provider,
        ),
    )
