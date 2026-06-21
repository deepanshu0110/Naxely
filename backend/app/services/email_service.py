import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to: str | list[str],
    subject: str,
    html: str | None = None,
    text: str | None = None,
    attachments: list[dict] | None = None,
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set; skipping email to %s", to)
        return False

    import resend

    resend.api_key = settings.RESEND_API_KEY

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

    try:
        resend.Emails.send(params)
        logger.info("Email sent to %s — subject: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False
