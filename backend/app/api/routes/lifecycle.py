import logging
from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.lifecycle_email_service import run_lifecycle_cycle

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_lifecycle():
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            stats = await run_lifecycle_cycle(db)
            logger.info("[lifecycle] cycle complete %s", stats)
        except Exception as e:
            logger.error("[lifecycle] FATAL ERROR: %s", e, exc_info=True)


@router.post("/internal/lifecycle-emails/run", status_code=202)
async def run_lifecycle_emails(
    background_tasks: BackgroundTasks,
    x_lifecycle_cron_secret: str = Header(..., alias="X-Lifecycle-Cron-Secret"),
):
    if x_lifecycle_cron_secret != settings.LIFECYCLE_CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    background_tasks.add_task(_run_lifecycle)
    return JSONResponse({"status": "accepted"}, status_code=202)


@router.get("/internal/lifecycle-emails/preview")
async def preview_lifecycle_emails(
    x_lifecycle_cron_secret: str = Header(..., alias="X-Lifecycle-Cron-Secret"),
    db: AsyncSession = Depends(get_db),
):
    """Preview candidates without sending. Useful for manual testing."""
    if x_lifecycle_cron_secret != settings.LIFECYCLE_CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    from app.services.lifecycle_email_service import get_trigger_a_candidates, get_trigger_b_candidates
    a = await get_trigger_a_candidates(db)
    b = await get_trigger_b_candidates(db)
    return {
        "trigger_a_candidates": len(a),
        "trigger_b_candidates": len(b),
        "trigger_a_sample": [{"id": str(x["id"]), "email": x["email"][:3] + "***"} for x in a[:3]],
        "trigger_b_sample": [{"id": str(x["id"]), "email": x["email"][:3] + "***"} for x in b[:3]],
    }
