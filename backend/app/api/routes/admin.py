from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.profile import _build_read, _compute_completion
from app.db.session import get_session
from app.models.driver import Driver
from app.models.user import User
from app.models.event import Event
from app.models.participation import Participation
from app.models.user_profile import UserProfile
from app.schemas.admin import (
    AdminParticipationSearchRead,
    AdminParticipationSummary,
    AdminPlayerInspectRead,
    AdminUserRead,
    AdminUserSearchRead,
)
from app.schemas.driver import DriverRead
from app.schemas.profile import UserProfileRead, UserProfileUpsert
from app.services.auth import require_roles
from app.services.tasks import ensure_task_completion

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/profiles/{user_id}", response_model=UserProfileRead)
def get_profile(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _build_read(profile)

@router.put("/profiles/{user_id}", response_model=UserProfileRead)
def update_profile(
    user_id: str,
    payload: UserProfileUpsert,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        session.add(profile)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "sim_platforms" and value is None:
            value = []
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    driver = session.query(Driver).filter(Driver.user_id == user_id).first()
    if profile.sim_platforms and driver:
        driver.sim_games = profile.sim_platforms
    session.commit()
    session.refresh(profile)
    completion, missing, _ = _compute_completion(profile)
    if driver:
        suffix = (driver.primary_discipline or "gt").upper()
        if driver.sim_games:
            ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
        if completion >= 100 or not missing:
            ensure_task_completion(session, driver.id, f"ONBOARD_PROFILE_{suffix}")
        ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
        session.commit()
    return _build_read(profile)


@router.get("/users", response_model=List[AdminUserRead])
def list_users(
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    limit = max(1, min(limit, 200))
    users = (
        session.query(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    user_ids = [user.id for user in users]
    profiles = session.query(UserProfile).filter(UserProfile.user_id.in_(user_ids)).all()
    drivers = session.query(Driver).filter(Driver.user_id.in_(user_ids)).all()
    profile_map = {profile.user_id: profile for profile in profiles}
    driver_map = {driver.user_id: driver for driver in drivers}
    response = []
    for user in users:
        profile = profile_map.get(user.id)
        completion, _, level = _compute_completion(profile)
        driver = driver_map.get(user.id)
        response.append(
            AdminUserRead(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                active=user.active,
                created_at=user.created_at,
                profile_id=profile.id if profile else None,
                completion_percent=completion,
                level=level,
                driver_id=driver.id if driver else None,
            )
        )
    return sorted(response, key=lambda row: row.completion_percent, reverse=True)


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user_detail(
    user_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    driver = session.query(Driver).filter(Driver.user_id == user.id).first()
    completion, _, level = _compute_completion(profile)
    return AdminUserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        active=user.active,
        created_at=user.created_at,
        profile_id=profile.id if profile else None,
        completion_percent=completion,
        level=level,
        driver_id=driver.id if driver else None,
    )


def _find_user_and_driver(session: Session, query: str) -> tuple[User | None, Driver | None]:
    if "@" in query:
        user = session.query(User).filter(User.email == query).first()
        driver = session.query(Driver).filter(Driver.user_id == user.id).first() if user else None
        return user, driver
    driver = session.query(Driver).filter(Driver.id == query).first()
    user = session.query(User).filter(User.id == driver.user_id).first() if driver else None
    return user, driver


@router.get("/search/user", response_model=AdminUserSearchRead)
def search_user_by_email(
    email: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user = session.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    driver = session.query(Driver).filter(Driver.user_id == user.id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return AdminUserSearchRead(
        driver_id=driver.id,
        email=user.email,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
    )


@router.get("/search/participations", response_model=AdminParticipationSearchRead)
def search_participations(
    q: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user, driver = _find_user_and_driver(session, q)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    participations = (
        session.query(Participation, Event)
        .join(Event, Participation.event_id == Event.id, isouter=True)
        .filter(Participation.driver_id == driver.id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .all()
    )
    items = []
    for participation, event in participations:
        item = participation.__dict__.copy()
        item["game"] = event.game if event else None
        item.pop("_sa_instance_state", None)
        items.append(item)
    return AdminParticipationSearchRead(
        driver_id=driver.id,
        driver_email=user.email if user else None,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
        participations=items,
    )


@router.get("/driver/inspect", response_model=AdminPlayerInspectRead)
def inspect_driver(
    q: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    user, driver = _find_user_and_driver(session, q)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    participations = (
        session.query(Participation)
        .filter(Participation.driver_id == driver.id)
        .order_by(Participation.started_at.desc(), Participation.created_at.desc())
        .all()
    )
    summary = [
        AdminParticipationSummary(id=item.id, started_at=item.started_at) for item in participations
    ]
    return AdminPlayerInspectRead(
        driver_id=driver.id,
        driver_email=user.email if user else None,
        primary_discipline=driver.primary_discipline,
        sim_games=driver.sim_games or [],
        participations=summary,
    )
