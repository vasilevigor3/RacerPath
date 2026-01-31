from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.driver import DriverCreate, DriverRead
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
    driver = Driver(name=payload.name, primary_discipline=payload.primary_discipline)
    driver.sim_games = payload.sim_games
    session.add(driver)
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
    query = session.query(Driver)
    if user.role not in {"admin"}:
        query = query.filter(Driver.user_id == user.id)
    return query.order_by(Driver.created_at.desc()).all()


@router.get("/me", response_model=DriverRead | None)
def get_my_driver(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    return session.query(Driver).filter(Driver.user_id == user.id).first()


@router.post("/me", response_model=DriverRead)
def create_my_driver(
    payload: DriverCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if not payload.sim_games:
        raise HTTPException(status_code=400, detail="At least one sim game is required")
    existing = session.query(Driver).filter(Driver.user_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Driver profile already exists")
    driver = Driver(
        name=payload.name,
        primary_discipline=payload.primary_discipline,
        sim_games=payload.sim_games,
        user_id=user.id,
    )
    session.add(driver)
    session.commit()
    session.refresh(driver)
    profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(
            user_id=user.id,
            full_name=None,
            primary_discipline=driver.primary_discipline,
            sim_platforms=driver.sim_games,
        )
        session.add(profile)
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


@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return driver
