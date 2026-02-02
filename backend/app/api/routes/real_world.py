from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.real_world_format import RealWorldFormat
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.real_world import RealWorldFormatRepository, RealWorldReadinessRepository
from app.schemas.real_world import RealWorldFormatCreate, RealWorldFormatRead, RealWorldReadinessRead
from app.services.auth import require_roles, require_user
from app.services.real_world import compute_real_world_readiness

router = APIRouter(prefix="/real-world", tags=["real-world"])


@router.post("/formats", response_model=RealWorldFormatRead)
def create_format(
    payload: RealWorldFormatCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    fmt = RealWorldFormat(**payload.model_dump())
    RealWorldFormatRepository(session).add(fmt)
    session.commit()
    session.refresh(fmt)
    return fmt


@router.get("/formats", response_model=List[RealWorldFormatRead])
def list_formats(
    discipline: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    return RealWorldFormatRepository(session).list_by_discipline(discipline)


@router.post("/assess", response_model=RealWorldReadinessRead)
def assess(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return compute_real_world_readiness(session, driver_id, discipline)


@router.get("/assessments", response_model=List[RealWorldReadinessRead])
def list_assessments(
    driver_id: str,
    discipline: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 200))
    return RealWorldReadinessRepository(session).list_by_driver_id(
        driver_id, discipline=discipline, offset=offset, limit=limit
    )


@router.get("/assessments/latest", response_model=RealWorldReadinessRead)
def latest_assessment(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    readiness = RealWorldReadinessRepository(session).latest_by_driver_and_discipline(
        driver_id, discipline
    )
    if not readiness:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return readiness