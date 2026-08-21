"""
Lifecycle email triggers. Each function returns users matching a condition
who have NOT already received that email_type (per email_log) and are not
suppressed.
"""

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.services.email_service import send_email_with_id
from app.core.config import settings

logger = logging.getLogger(__name__)

# Manual-outreach users — never send lifecycle automation to these exact emails
MANUAL_OUTREACH_EXCLUDE = "u.email NOT IN ('eminefe13@gmail.com', 'jash.c.shah@gmail.com', 'ravenabianca@gmail.com')"

TRIGGER_A_QUERY = f"""
SELECT u.id, u.email, u.full_name, u.created_at
FROM users u
LEFT JOIN reports r ON r.user_id = u.id
LEFT JOIN email_log el ON el.user_id = u.id AND el.email_type = 'lifecycle_no_report_3d'
WHERE u.deleted_at IS NULL
  AND COALESCE(u.email_suppressed, FALSE) = FALSE
  AND {MANUAL_OUTREACH_EXCLUDE}
  AND u.created_at <= NOW() - INTERVAL '3 days'
  AND el.id IS NULL
GROUP BY u.id
HAVING COUNT(r.id) = 0;
"""

TRIGGER_B_QUERY = f"""
SELECT u.id, u.email, u.full_name, u.onboarding_completed_at
FROM users u
LEFT JOIN reports r ON r.user_id = u.id AND r.deleted_at IS NULL
LEFT JOIN email_log el ON el.user_id = u.id AND el.email_type = 'lifecycle_onboarded_no_report_7d'
WHERE u.deleted_at IS NULL
  AND COALESCE(u.email_suppressed, FALSE) = FALSE
  AND {MANUAL_OUTREACH_EXCLUDE}
  AND u.has_completed_onboarding = TRUE
  AND u.onboarding_completed_at IS NOT NULL
  AND u.onboarding_completed_at <= NOW() - INTERVAL '7 days'
  AND el.id IS NULL
GROUP BY u.id
HAVING COUNT(r.id) = 0;
"""

# Plain-text-forward templates (transactional framing, no upsell)
# Trigger A: signed up 3+ days ago, 0 reports
TEMPLATE_A_SUBJECT = "Quick start: your first Naxely report in 2 minutes"

TEMPLATE_A_HTML = """<p>Hi {full_name},</p>
<p>You signed up for Naxely a few days ago — thanks for joining.</p>
<p>The fastest way to your first report: upload a CSV (or connect a Google Sheet), pick a template, and hit Generate. It takes about 2 minutes to get a branded PDF.</p>
<p><a href=\"{frontend_url}/reports/new\">Create your first report</a></p>
<p>If you hit any snags, just reply to this email — we read every reply.</p>
<p>— The Naxely team</p>
<p style=\"font-size:12px;color:#888\">You're receiving this because you signed up for Naxely. Reply and let us know if you'd rather not get these onboarding tips.</p>"""

TEMPLATE_A_TEXT = """Hi {full_name},

You signed up for Naxely a few days ago — thanks for joining.

The fastest way to your first report: upload a CSV (or connect a Google Sheet), pick a template, and hit Generate. It takes about 2 minutes to get a branded PDF.

Create your first report: {frontend_url}/reports/new

If you hit any snags, just reply to this email — we read every reply.

— The Naxely team

You're receiving this because you signed up for Naxely. Reply and let us know if you'd rather not get these onboarding tips."""

# Trigger B: onboarded, 7+ days, still 0 reports
TEMPLATE_B_SUBJECT = "Still stuck? Tell us what's blocking your first report"

TEMPLATE_B_HTML = """<p>Hi {full_name},</p>
<p>You completed onboarding a week ago — appreciate you giving Naxely a try.</p>
<p>We noticed you haven't generated a report yet. Is something blocking you — data format, template choice, or just timing?</p>
<p>Reply directly to this email and tell us what's in the way. We can point you to the right template or help with your CSV/Sheet in one reply.</p>
<p>Or jump back in when ready: <a href=\"{frontend_url}/reports/new\">Create a report</a></p>
<p>— The Naxely team</p>
<p style=\"font-size:12px;color:#888\">You're receiving this because you completed onboarding on Naxely. Reply and let us know if you'd rather not get these check-ins.</p>"""

TEMPLATE_B_TEXT = """Hi {full_name},

You completed onboarding a week ago — appreciate you giving Naxely a try.

We noticed you haven't generated a report yet. Is something blocking you — data format, template choice, or just timing?

Reply directly to this email and tell us what's in the way. We can point you to the right template or help with your CSV/Sheet in one reply.

Or jump back in when ready: {frontend_url}/reports/new

— The Naxely team

You're receiving this because you completed onboarding on Naxely. Reply and let us know if you'd rather not get these check-ins."""


async def get_trigger_a_candidates(db: AsyncSession) -> list[dict]:
    result = await db.execute(text(TRIGGER_A_QUERY))
    return [dict(r) for r in result.mappings().all()]


async def get_trigger_b_candidates(db: AsyncSession) -> list[dict]:
    result = await db.execute(text(TRIGGER_B_QUERY))
    return [dict(r) for r in result.mappings().all()]


async def _send_and_log(
    db: AsyncSession,
    user_id: str,
    email: str,
    email_type: str,
    subject: str,
    html: str,
    text_body: str,
) -> bool:
    """Send email and log it. Returns True if sent, False otherwise.
    Uses UNIQUE (user_id, email_type) to prevent duplicates even if called twice.
    Note: send and log are NOT atomically guaranteed — if process crashes between
    Resend send and DB insert, a retry could send a duplicate. The UNIQUE constraint
    prevents a second log row but cannot unsend the first email. This is flagged
    per spec; a transactional outbox would be needed for true atomicity.
    """
    success, resend_id = send_email_with_id(to=email, subject=subject, html=html, text=text_body)
    if not success:
        logger.warning("Lifecycle email %s failed for %s", email_type, email)
        return False
    try:
        await db.execute(
            text("""
                INSERT INTO email_log (id, user_id, email_type, resend_id, status, sent_at)
                VALUES (gen_random_uuid(), :uid, :etype, :rid, 'sent', NOW())
            """),
            {"uid": user_id, "etype": email_type, "rid": resend_id},
        )
        await db.commit()
        logger.info("Lifecycle email %s logged for %s resend_id=%s", email_type, email, resend_id)
        return True
    except IntegrityError:
        await db.rollback()
        # UNIQUE violation means another worker already sent this email_type to this user
        logger.info("Duplicate lifecycle email %s for %s suppressed by UNIQUE constraint", email_type, email)
        return False
    except Exception as e:
        await db.rollback()
        logger.error("Failed to log lifecycle email %s for %s: %s (email was sent, resend_id=%s)", email_type, email, e, resend_id)
        return False


async def send_trigger_a(db: AsyncSession, user: dict) -> bool:
    frontend_url = settings.FRONTEND_BASE_URL
    full_name = (user.get("full_name") or "").strip() or "there"
    html = TEMPLATE_A_HTML.format(frontend_url=frontend_url, full_name=full_name)
    text_body = TEMPLATE_A_TEXT.format(frontend_url=frontend_url, full_name=full_name)
    return await _send_and_log(db, str(user["id"]), user["email"], "lifecycle_no_report_3d", TEMPLATE_A_SUBJECT, html, text_body)


async def send_trigger_b(db: AsyncSession, user: dict) -> bool:
    frontend_url = settings.FRONTEND_BASE_URL
    full_name = (user.get("full_name") or "").strip() or "there"
    html = TEMPLATE_B_HTML.format(frontend_url=frontend_url, full_name=full_name)
    text_body = TEMPLATE_B_TEXT.format(frontend_url=frontend_url, full_name=full_name)
    return await _send_and_log(db, str(user["id"]), user["email"], "lifecycle_onboarded_no_report_7d", TEMPLATE_B_SUBJECT, html, text_body)


async def run_lifecycle_cycle(db: AsyncSession) -> dict:
    """Run both triggers once. Returns counts."""
    stats = {"trigger_a_sent": 0, "trigger_b_sent": 0, "trigger_a_candidates": 0, "trigger_b_candidates": 0}
    # Trigger A
    candidates_a = await get_trigger_a_candidates(db)
    stats["trigger_a_candidates"] = len(candidates_a)
    for user in candidates_a:
        if await send_trigger_a(db, user):
            stats["trigger_a_sent"] += 1
    # Trigger B
    candidates_b = await get_trigger_b_candidates(db)
    stats["trigger_b_candidates"] = len(candidates_b)
    for user in candidates_b:
        if await send_trigger_b(db, user):
            stats["trigger_b_sent"] += 1
    return stats
