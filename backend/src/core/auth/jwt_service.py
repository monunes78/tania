from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import structlog

from src.config import settings

log = structlog.get_logger()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(user_id: str, is_admin: bool) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "type": ACCESS_TOKEN_TYPE,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "type": REFRESH_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        log.debug("jwt.decode.failed", error=str(e))
        return None


def verify_access_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload and payload.get("type") == ACCESS_TOKEN_TYPE:
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if payload and payload.get("type") == REFRESH_TOKEN_TYPE:
        return payload
    return None
