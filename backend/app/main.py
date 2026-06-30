from datetime import datetime, timezone
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.limiter import limiter

from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

if os.getenv("RENDER") and not os.getenv("ENVIRONMENT"):
    logger.critical(
        "ENVIRONMENT is unset on what appears to be a Render.com deploy. "
        "Set ENVIRONMENT=production in Render dashboard. Refusing to start "
        "with insecure defaults."
    )
    raise SystemExit(1)

app = FastAPI(title="Naxely API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

def _resolve_origins() -> list[str]:
    raw = [o.strip() for o in settings.resolved_allowed_origins.split(",")]
    expanded: list[str] = []
    for origin in raw:
        expanded.append(origin)
        if origin == "https://naxely.com":
            expanded.append("https://www.naxely.com")
        elif origin == "http://localhost:5173":
            expanded.append("http://localhost:3000")
    return expanded


app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' fonts.gstatic.com; "
        "connect-src 'self' https://*.supabase.co wss://*.supabase.co; "
        "img-src 'self' data: blob: https://*.supabase.co; "
        "frame-src 'self' https://*.supabase.co; "
        "form-action 'self' https://accounts.google.com; "
        "object-src 'none'"
    )
    return response


app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

from app.api.routes import auth, reports, settings as settings_router, payments, health, templates, v1 as v1_router  # noqa: E402
from app.api.routes.scheduled_reports import router as scheduled_reports_router  # noqa: E402

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(reports.router, tags=["reports"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(templates.router, tags=["templates"])
app.include_router(scheduled_reports_router, tags=["scheduled_reports"])
app.include_router(v1_router.router)


@app.on_event("startup")
async def startup_migrations():
    try:
        from app.utils.encryption import get_master_key
        get_master_key()
    except (ImportError, ValueError):
        logger.error(
            "MASTER_ENCRYPTION_KEY is missing or invalid — "
            "BYOK key saving will fail with 500 errors until this is fixed"
        )

    migrations = [
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS trend_pct FLOAT",
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS ai_skipped BOOLEAN DEFAULT FALSE",
    ]
    async with AsyncSessionLocal() as db:
        for sql in migrations:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception as e:
                logger.warning("[startup] migration skipped: %s", e)

    onboarding_sql = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS has_completed_onboarding BOOLEAN DEFAULT FALSE",
    ]
    async with AsyncSessionLocal() as db:
        for sql in onboarding_sql:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception as e:
                logger.warning("[startup] migration skipped: %s", e)

    if settings.ENVIRONMENT == "development" and os.getenv("RENDER"):
        logger.warning(
            "ENVIRONMENT is 'development' on Render — this should be 'production'. "
            "Verify your Render env vars."
        )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
