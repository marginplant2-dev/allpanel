"""Password hashing and JWT token helpers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = settings.jwt_algorithm


# ---- Password hashing (bcrypt) ----

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---- JWT ----

def _create_token(subject: str, expires_delta: timedelta, token_type: str, extra: dict[str, Any] | None = None) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    token_id = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": token_id,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)
    return encoded, token_id


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    token, _ = _create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
        extra,
    )
    return token


def create_refresh_token(subject: str, extra: dict[str, Any] | None = None) -> tuple[str, str]:
    """Return (token, token_id). token_id is stored in the sessions collection."""
    return _create_token(
        subject,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
        extra,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
