import json
import logging
import time
from urllib.parse import urlparse
from urllib.request import urlopen

from fastapi import HTTPException
from jose import jwk, jwt, JWTError

from app.core.config import settings


def _validate_url_scheme(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed (only http/https)")

logger = logging.getLogger(__name__)

_jwks: list[dict] = []
_jwks_fetched_at: float = 0
JWKS_CACHE_TTL = 3600


def _get_jwks() -> list[dict]:
    global _jwks, _jwks_fetched_at
    now = time.time()

    if _jwks and (now - _jwks_fetched_at) < JWKS_CACHE_TTL:
        return _jwks

    url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        _validate_url_scheme(url)
        resp = urlopen(url, timeout=10)
        data: dict = json.loads(resp.read().decode())
        _jwks = data.get("keys", [])
        _jwks_fetched_at = now
    except Exception as e:
        logger.error("Failed to fetch JWKS from %s: %s", url, e)
        if not _jwks:
            raise

    return _jwks


def verify_supabase_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise JWTError("Token missing kid in header")

        keys = _get_jwks()
        key_data = next((k for k in keys if k.get("kid") == kid), None)
        if not key_data:
            raise JWTError(f"No matching JWK for kid: {kid}")

        key = jwk.construct(key_data)
        payload = jwt.decode(
            token,
            key,
            algorithms=[key_data["alg"]],
            options={"verify_aud": False},
        )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error("JWT verification failed: %s: %s", type(e).__name__, str(e))
        raise HTTPException(status_code=401, detail="Invalid token")
