from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.db.session import get_session
from app.models.anti_gaming import AntiGamingReport
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.penalty import Penalty
from app.models.real_world_readiness import RealWorldReadiness
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.crs_history import CRSHistory
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


@router.get("/me", response_model=List[DriverRead])
def list_my_drivers(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """List all drivers (careers) for the current user. Use for career switcher; if empty, show onboarding."""
    return DriverRepository(session).list_for_user(user.id)


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
    discipline = (payload.primary_discipline or "gt").strip().lower()
    existing_same_discipline = driver_repo.get_by_user_id_and_discipline(user.id, discipline)
    if existing_same_discipline:
        raise HTTPException(
            status_code=400,
            detail=f"You already have a driver for discipline '{discipline}'. One career per discipline.",
        )
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
    """Update first/only driver (backward compat). Prefer PATCH /{driver_id} when using multiple careers."""
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


@router.patch("/{driver_id}", response_model=DriverRead)
def update_driver(
    driver_id: str,
    payload: DriverUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Update a specific driver (career). Allowed only for own drivers."""
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
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


def _delete_driver_cascade(session: Session, driver_id: str) -> None:
    """Delete driver and all related records (participations, incidents, penalties, etc.)."""
    part_ids = [r[0] for r in session.execute(select(Participation.id).where(Participation.driver_id == driver_id))]
    if part_ids:
        session.execute(Incident.__table__.delete().where(Incident.participation_id.in_(part_ids)))
        session.execute(Penalty.__table__.delete().where(Penalty.participation_id.in_(part_ids)))
    session.execute(Participation.__table__.delete().where(Participation.driver_id == driver_id))
    session.execute(TaskCompletion.__table__.delete().where(TaskCompletion.driver_id == driver_id))
    session.execute(Recommendation.__table__.delete().where(Recommendation.driver_id == driver_id))
    session.execute(CRSHistory.__table__.delete().where(CRSHistory.driver_id == driver_id))
    session.execute(DriverLicense.__table__.delete().where(DriverLicense.driver_id == driver_id))
    session.execute(AntiGamingReport.__table__.delete().where(AntiGamingReport.driver_id == driver_id))
    session.execute(RealWorldReadiness.__table__.delete().where(RealWorldReadiness.driver_id == driver_id))
    session.execute(Driver.__table__.delete().where(Driver.id == driver_id))


@router.delete("/{driver_id}", status_code=204)
def delete_driver(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Permanently delete a driver (career) and all related data. Only own driver or admin."""
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    _delete_driver_cascade(session, driver_id)
    session.commit()
