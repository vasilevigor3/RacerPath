from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.session import get_session
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AuditLogRead,
    BootstrapRequest,
    LoginRequest,
    LoginRead,
    RegisterRead,
    RegisterRequest,
    UserCreate,
    UserRead,
)
from app.services.auth import (
    generate_api_key,
    get_user_by_email,
    hash_key,
    hash_password,
    require_roles,
    require_user,
    verify_password,
)
from app.services.rate_limit import RateLimitConfig, enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/bootstrap", response_model=RegisterRead)
def bootstrap(payload: BootstrapRequest, session: Session = Depends(get_session)):
    if settings.bootstrap_key == "change-me":
        raise HTTPException(status_code=503, detail="BOOTSTRAP_KEY is not configured")
    if payload.bootstrap_key != settings.bootstrap_key:
        raise HTTPException(status_code=403, detail="Invalid bootstrap key")

    user_repo = UserRepository(session)
    if user_repo.get_by_role("admin"):
        raise HTTPException(status_code=400, detail="Admin already exists")

    email = payload.email.strip().lower()
    if user_repo.get_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    api_key = generate_api_key()
    user = User(
        name=payload.login,
        email=email,
        role="admin",
        api_key_hash=hash_key(api_key),
        password_hash=hash_password(payload.password),
    )
    user_repo.add(user)
    session.commit()
    session.refresh(user)
    return RegisterRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        api_key=api_key,
    )


@router.post("/register", response_model=RegisterRead)
def register(payload: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    enforce_rate_limit(
        f"auth:register:{request.client.host if request.client else 'unknown'}",
        RateLimitConfig(limit=settings.auth_rate_limit_per_minute, window_seconds=60),
    )
    email = payload.email.strip().lower()
    user_repo = UserRepository(session)
    if user_repo.get_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    api_key = generate_api_key()
    user = User(
        name=payload.login,
        email=email,
        role="driver",
        api_key_hash=hash_key(api_key),
        password_hash=hash_password(payload.password),
    )
    user_repo.add(user)
    session.commit()
    session.refresh(user)
    return RegisterRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        api_key=api_key,
    )


@router.post("/login", response_model=LoginRead)
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_session)):
    enforce_rate_limit(
        f"auth:login:{request.client.host if request.client else 'unknown'}",
        RateLimitConfig(limit=settings.auth_rate_limit_per_minute, window_seconds=60),
    )
    email = payload.email.strip().lower()
    user = get_user_by_email(session, email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    api_key = generate_api_key()
    user.api_key_hash = hash_key(api_key)
    session.commit()
    session.refresh(user)
    return LoginRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        api_key=api_key,
    )


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(require_user())):
    return user


@router.post("/logout")
def logout(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    user.api_key_hash = hash_key(generate_api_key())
    session.commit()
    return {"detail": "Logged out"}


@router.post("/revoke")
def revoke_api_key(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    target = UserRepository(session).get_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.api_key_hash = hash_key(generate_api_key())
    session.commit()
    return {"detail": "API key revoked"}


@router.post("/users", response_model=UserRead)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    email = payload.email.strip().lower()
    user_repo = UserRepository(session)
    if user_repo.get_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")
    api_key = generate_api_key()
    user = User(
        name=payload.login,
        email=email,
        role=payload.role,
        api_key_hash=hash_key(api_key),
        password_hash=hash_password(payload.password),
    )
    user_repo.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users", response_model=List[UserRead])
def list_users(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return UserRepository(session).list_all()


@router.get("/audit", response_model=List[AuditLogRead])
def list_audit_logs(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return AuditLogRepository(session).list_recent(200)
