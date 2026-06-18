from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def _error_response(code: str, message: str, status_code: int, detail=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "code": code,
            "message": message,
            "detail": detail,
        },
    )


_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = _STATUS_CODES.get(exc.status_code, "INTERNAL_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "An unexpected error occurred."
    detail = exc.detail if isinstance(exc.detail, dict) else None

    return _error_response(code, message, exc.status_code, detail)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        "VALIDATION_ERROR",
        "Request validation failed.",
        422,
        detail=exc.errors(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return _error_response(
        "INTERNAL_ERROR",
        "An unexpected error occurred.",
        500,
    )
