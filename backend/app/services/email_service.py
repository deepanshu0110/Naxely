import logging
from typing import Any, cast

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_params(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
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
    return params


def send_email(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
) -> bool:
    """Send via Resend. Returns True on success, False on failure/missing key."""
    return send_email_with_id(to, subject, html, text, attachments)[0]


def send_email_with_id(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
) -> tuple[bool, str | None]:
    """Send via Resend and return (success, resend_id). resend_id may be None if not returned by API."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to)
        return False, None

    import resend

    resend.api_key = settings.RESEND_API_KEY
    params = _build_params(to, subject, html, text, attachments)

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
        logger.error("Failed to send email to %s: %s", to, e)
        return False, None
