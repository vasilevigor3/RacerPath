from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.models.driver import Driver
from app.models.user_profile import UserProfile
from app.schemas.profile import NextTierData, UserProfileRead, UserProfileUpsert
from app.services.auth import require_user
from app.services.next_tier import compute_next_tier_progress
from app.services.tasks import ensure_task_completion

router = APIRouter(prefix="/profile", tags=["profile"])

REQUIRED_FIELDS = [
    "full_name",
    "country",
    "city",
    "experience_years",
    "primary_discipline",
    "sim_platforms",
]


def _compute_completion(profile: UserProfile | None) -> tuple[int, List[str], str]:
    if not profile:
        missing = REQUIRED_FIELDS.copy()
        return 0, missing, "Rookie"

    missing = []
    for field in REQUIRED_FIELDS:
        value = getattr(profile, field)
        if field == "sim_platforms":
            if not value:
                missing.append(field)
        else:
            if value in (None, ""):
                missing.append(field)

    profile_completion = int(round((len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS) * 100))
    if profile_completion >= 85:
        level = "Elite"
    elif profile_completion >= 60:
        level = "Advanced"
    else:
        level = "Rookie"
    return profile_completion, missing, level


def _build_read(
    profile: UserProfile | None,
    next_tier_progress_percent: int = 0,
    next_tier_data: dict | None = None,
) -> UserProfileRead:
    profile_completion, missing, level = _compute_completion(profile)
    tier_data = NextTierData(**next_tier_data) if next_tier_data else None
    if not profile:
        return UserProfileRead(
            id="",
            user_id="",
            full_name=None,
            country=None,
            city=None,
            age=None,
            experience_years=None,
            primary_discipline=None,
            sim_platforms=[],
            rig=None,
            goals=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            profile_completion_percent=profile_completion,
            next_tier_progress_percent=next_tier_progress_percent,
            next_tier_data=tier_data,
            missing_fields=missing,
            level=level,
        )
    return UserProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        country=profile.country,
        city=profile.city,
        age=profile.age,
        experience_years=profile.experience_years,
        primary_discipline=profile.primary_discipline,
        sim_platforms=profile.sim_platforms or [],
        rig=profile.rig,
        goals=profile.goals,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        profile_completion_percent=profile_completion,
        next_tier_progress_percent=next_tier_progress_percent,
        next_tier_data=tier_data,
        missing_fields=missing,
        level=level,
    )


@router.get("/me", response_model=UserProfileRead)
def get_my_profile(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    next_tier, next_tier_data = compute_next_tier_progress(session, user.id)
    return _build_read(profile, next_tier_progress_percent=next_tier, next_tier_data=next_tier_data)


@router.put("/me", response_model=UserProfileRead)
def upsert_my_profile(
    payload: UserProfileUpsert,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        session.add(profile)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field == "sim_platforms" and value is None:
            value = []
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    driver = session.query(Driver).filter(Driver.user_id == user.id).first()
    if profile.sim_platforms and driver:
        driver.sim_games = profile.sim_platforms
    session.commit()
    session.refresh(profile)
    profile_completion, missing, _ = _compute_completion(profile)
    if driver:
        suffix = (driver.primary_discipline or "gt").upper()
        if driver.sim_games:
            ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
        if profile_completion >= 100 or not missing:
            ensure_task_completion(session, driver.id, f"ONBOARD_PROFILE_{suffix}")
        ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
        session.commit()
    next_tier, next_tier_data = compute_next_tier_progress(session, user.id)
    return _build_read(profile, next_tier_progress_percent=next_tier, next_tier_data=next_tier_data)
