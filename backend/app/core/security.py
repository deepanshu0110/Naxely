import logging

from fastapi import HTTPException
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_supabase_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        logger.error("JWT verification failed: %s: %s", type(e).__name__, str(e))
        raise HTTPException(status_code=401, detail="Invalid token")
