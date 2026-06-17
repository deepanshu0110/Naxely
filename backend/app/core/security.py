from fastapi import HTTPException
from jose import jwt, JWTError
from app.core.config import settings


def verify_supabase_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
