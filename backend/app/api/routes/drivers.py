from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repositories.crs_history import CRSHistoryRepository
from app.repositories.driver import DriverRepository
from app.repositories.user_profile import UserProfileRepository
from app.schemas.crs import CRSHistoryRead
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate
from app.services.auth import require_roles, require_user
from app.services.tasks import ensure_task_completion

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.post("", response_model=DriverRead)
def create_driver(
    payload: DriverCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    if not payload.sim_games:
        raise HTTPException(status_code=400, detail="At least one sim game is required")
    if not payload.user_id:
        raise HTTPException(status_code=400, detail="user_id is required; driver cannot exist without a user")
    driver = Driver(
        name=payload.name,
        primary_discipline=payload.primary_discipline,
        sim_games=payload.sim_games,
        user_id=payload.user_id,
    )
    DriverRepository(session).add(driver)
    session.commit()
    session.refresh(driver)
    suffix = (driver.primary_discipline or "gt").upper()
    ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
    ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
    session.commit()
    return driver


@router.get("", response_model=List[DriverRead])
def list_drivers(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    repo = DriverRepository(session)
    if user.role == "admin":
        return repo.list_all()
    return repo.list_for_user(user.id)


@router.get("/me", response_model=DriverRead | None)
def get_my_driver(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    return DriverRepository(session).get_by_user_id(user.id)


@router.post("/me", response_model=DriverRead)
def create_my_driver(
    payload: DriverCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if (user.role or "").strip().lower() == "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin users cannot create a driver profile. Use the admin console to create drivers for other users.",
        )
    if not payload.sim_games:
        raise HTTPException(status_code=400, detail="At least one sim game is required")
    driver_repo = DriverRepository(session)
    profile_repo = UserProfileRepository(session)
    existing = driver_repo.get_by_user_id(user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Driver profile already exists")
    driver = Driver(
        name=payload.name,
        primary_discipline=payload.primary_discipline,
        sim_games=payload.sim_games,
        user_id=user.id,
        rig_options=payload.rig_options.model_dump() if payload.rig_options is not None else None,
    )
    driver_repo.add(driver)
    session.commit()
    session.refresh(driver)
    profile = profile_repo.get_by_user_id(user.id)
    if not profile:
        profile = UserProfile(
            user_id=user.id,
            full_name=None,
            primary_discipline=driver.primary_discipline,
            sim_platforms=driver.sim_games,
        )
        profile_repo.add(profile)
    else:
        if not profile.primary_discipline:
            profile.primary_discipline = driver.primary_discipline
        if not profile.sim_platforms:
            profile.sim_platforms = driver.sim_games
    session.commit()
    suffix = (driver.primary_discipline or "gt").upper()
    ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
    ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
    session.commit()
    return driver


@router.get("/{driver_id}/crs/history", response_model=List[CRSHistoryRead])
def get_driver_crs_history(
    driver_id: str,
    discipline: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """CRS history for driver (includes inputs_hash, computed_from_participation_id)."""
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return CRSHistoryRepository(session).list_by_driver_id(driver_id, discipline)


@router.patch("/me", response_model=DriverRead)
def update_my_driver(
    payload: DriverUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_user_id(user.id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(driver, key):
            setattr(driver, key, value)
    session.commit()
    session.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return driver
