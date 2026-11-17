
import os
from datetime import datetime, timedelta, timezone
from hmac import compare_digest

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

load_dotenv()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def validate_auth_settings():
    if len(JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be configured with at least 32 characters."
        )

    if not ADMIN_EMAIL or not ADMIN_PASSWORD_HASH:
        raise RuntimeError(
            "ADMIN_EMAIL and ADMIN_PASSWORD_HASH must be configured."
        )


def authenticate_admin(email: str, password: str) -> bool:
    validate_auth_settings()

    normalized_email = email.strip().lower()

    if not compare_digest(normalized_email, ADMIN_EMAIL):
        return False

    try:
        return password_hasher.verify(password, ADMIN_PASSWORD_HASH)
    except Exception:
        return False


def create_access_token() -> str:
    validate_auth_settings()

    now = datetime.now(timezone.utc)

    payload = {
        "sub": ADMIN_EMAIL,
        "role": "admin",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        subject = payload.get("sub")
        role = payload.get("role")

        if (
            not subject
            or role != "admin"
            or not compare_digest(subject, ADMIN_EMAIL)
        ):
            raise unauthorized

        return {"email": subject, "role": role}

    except jwt.InvalidTokenError:
        raise unauthorized
