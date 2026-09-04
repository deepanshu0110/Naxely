import logging
import time
from typing import Any, cast

import sentry_sdk

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_params(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
    params: dict = {
        "from": settings.FROM_EMAIL,
        "to": to,
        "subject": subject,
    }
    if html:
        params["html"] = html
    if text:
        params["text"] = text
    if attachments:
        params["attachments"] = attachments
    if headers:
        params["headers"] = headers
    return params


def send_email(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> bool:
    """Send via Resend. Returns True on success, False on failure/missing key."""
    return send_email_with_id(to, subject, html, text, attachments, headers)[0]


def _is_retryable_resend_error(exc: Exception) -> bool:
    """Check if a Resend error is transient and worth retrying (429, 5xx)."""
    # Resend SDK raises ResendError with code as str/int for HTTP errors
    code = str(getattr(exc, "code", ""))
    if code in ("429", "500", "502", "503", "504"):
        return True
    # Some Resend errors use error_type
    error_type = str(getattr(exc, "error_type", "")).lower()
    if "rate_limit" in error_type or "rate_limit_exceeded" in error_type:
        return True
    # Fallback: check message for 429/5xx
    msg = str(getattr(exc, "message", str(exc))).lower()
    if "429" in msg or "rate limit" in msg or "too many requests" in msg:
        return True
    if "500" in msg or "502" in msg or "503" in msg or "504" in msg:
        # Be conservative: only retry if message mentions server error
        if "application error" in msg or "internal server error" in msg:
            return True
    return False


def _is_daily_cap_error(exc: Exception) -> bool:
    """Check if a Resend 429 is specifically the daily quota cap, not a burst limit.

    Resend's free tier 100/day cap and burst rate limits both surface as 429, but
    daily cap contains 'daily' + quota/limit/cap in the message, while burst is
    typically 'rate limit exceeded' without 'daily'. This distinction determines
    whether retrying could ever succeed today (burst: yes, daily: no).
    """
    msg = str(getattr(exc, "message", str(exc))).lower()
    # Daily cap messages typically mention daily + quota/limit/cap/exhausted
    has_daily = "daily" in msg
    has_quota = any(k in msg for k in ("quota", "cap", "exhausted", "limit"))
    # Also check for explicit daily quota phrases
    if has_daily and has_quota:
        return True
    # Some Resend daily cap messages may be "Daily sending quota exceeded"
    if "daily sending" in msg and ("quota" in msg or "exceeded" in msg):
        return True
    return False


def send_email_with_id(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Send via Resend and return (success, resend_id). resend_id may be None if not returned by API."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to)
        return False, None

    import resend

    resend.api_key = settings.RESEND_API_KEY
    params = _build_params(to, subject, html, text, attachments, headers)

    for attempt in range(3):
        try:
            resp = resend.Emails.send(cast(Any, params))
            # resend.Emails.send returns dict like {"id": "re_..."} on success
            resend_id = None
            if isinstance(resp, dict):
                resend_id = resp.get("id")
            elif hasattr(resp, "get"):
                try:
                    resend_id = resp.get("id")  # type: ignore[union-attr]
                except Exception:
                    resend_id = None
            logger.info("Email sent to %s — subject: %s id: %s", to, subject, resend_id)
            return True, resend_id
        except Exception as e:
            # Non-retryable: invalid key, validation, etc. — fail immediately
            if not _is_retryable_resend_error(e):
                logger.error("Failed to send email to %s: %s", to, e)
                return False, None
            # Retryable but daily cap — distinguish and alert without retrying further
            if _is_daily_cap_error(e):
                logger.error("Resend daily cap likely exhausted for %s: %s — retries won't help until reset", to, e)
                try:
                    sentry_sdk.capture_message(f"Resend daily cap likely exhausted for {to}: {e}", level="error")
                except Exception:
                    pass
                try:
                    from app.utils.error_notifier import notify_telegram_error

                    notify_telegram_error(
                        Exception(f"Resend daily cap likely exhausted for {to}: {e}"),
                        {"stage": "email_daily_cap", "recipient": to, "subject": subject},
                    )
                except Exception:
                    pass
                return False, None
            # Transient 429/5xx — retry with backoff if attempts remain
            if attempt < 2:
                backoff = 1 << attempt  # 1s, 2s
                logger.warning("Resend transient error for %s (attempt %d/3): %s — retrying in %ds", to, attempt + 1, e, backoff)
                time.sleep(backoff)
                continue
            logger.error("Failed to send email to %s after 3 attempts: %s", to, e)
            try:
                sentry_sdk.capture_message(f"Failed to send email to {to} after 3 retries: {e}", level="error")
            except Exception:
                pass
            return False, None
