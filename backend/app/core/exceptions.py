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


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."
    detail = None

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", code)
        message = exc.detail.get("message", message)
        detail = exc.detail.get("detail") or exc.detail.get("upgrade_url")
    elif isinstance(exc.detail, str):
        message = exc.detail

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
