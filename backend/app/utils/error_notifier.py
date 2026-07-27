import logging
import re
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

_warned_telegram_missing = False


def notify_telegram_error(error: Exception, context: dict) -> None:
    global _warned_telegram_missing

    from app.core.config import settings

    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        if not _warned_telegram_missing:
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — Telegram alerts disabled")
            _warned_telegram_missing = True
        return

    stage = context.get("stage", "unknown")
    user_id = context.get("user_id")
    user_email = context.get("user_email")
    error_msg = str(error)[:500]

    def _escape(text: str) -> str:
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

    parts = [f"⚠️ *Naxely Error*"]
    parts.append(f"*Stage:* {_escape(stage)}")
    if user_id:
        parts.append(f"*User:* `{_escape(user_id)}`")
    if user_email:
        parts.append(f"*Email:* {_escape(user_email)}")
    parts.append("")
    parts.append(f"`{_escape(error_msg)}`")

    message = "\n".join(parts)

    try:
        with httpx.Client(timeout=5) as client:
            resp = client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "MarkdownV2",
                },
            )
            resp.raise_for_status()
    except Exception:
        logger.warning("Failed to send Telegram alert", exc_info=False)
