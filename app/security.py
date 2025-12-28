"""Security utilities for hashing passwords and issuing JWTs."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt

from app.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Validate that a plaintext password matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: Dict[str, Any], expires_minutes: int) -> str:
    """Create a signed JWT token with an expiration claim."""

    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""

    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
