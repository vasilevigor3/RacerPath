from __future__ import annotations

import hashlib
import secrets
from typing import Iterable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_session
from app.models.audit_log import AuditLog
from app.models.user import User


def hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return secrets.token_urlsafe(24)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, digest = stored_hash.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return secrets.compare_digest(candidate.hex(), digest)


def get_user_by_key(session: Session, api_key: str) -> User | None:
    key_hash = hash_key(api_key)
    return (
        session.query(User)
        .filter(User.api_key_hash == key_hash, User.active.is_(True))
        .first()
    )


def get_user_by_email(session: Session, email: str) -> User | None:
    return (
        session.query(User)
        .filter(User.email == email, User.active.is_(True))
        .first()
    )


def require_roles(*roles: str):
    def dependency(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        session: Session = Depends(get_session),
    ) -> User | None:
        if not settings.auth_enabled:
            return None
        if not x_api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        user = get_user_by_key(session, x_api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user

    return dependency


def require_user():
    def dependency(
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        session: Session = Depends(get_session),
    ) -> User:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        user = get_user_by_key(session, x_api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return user

    return dependency


def log_audit(session: Session, user: User | None, action: str, path: str, status_code: int) -> None:
    if not settings.auth_enabled:
        return
    entry = AuditLog(
        actor_user_id=user.id if user else None,
        actor_role=user.role if user else None,
        action=action,
        path=path,
        status_code=status_code,
        details={},
    )
    session.add(entry)
    session.commit()
