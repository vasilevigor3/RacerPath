from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.user import User
from app.schemas.crs import CRSHistoryRead
from app.services.crs import record_crs
from app.services.auth import require_user

router = APIRouter(prefix="/crs", tags=["crs"])


@router.post("/compute", response_model=CRSHistoryRead)
def compute_crs(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    try:
        return record_crs(session, driver_id, discipline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=List[CRSHistoryRead])
def list_history(
    driver_id: str,
    discipline: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    query = session.query(CRSHistory).filter(CRSHistory.driver_id == driver_id)
    if discipline:
        query = query.filter(CRSHistory.discipline == discipline)
    return query.order_by(CRSHistory.computed_at.desc()).all()


@router.get("/latest", response_model=Optional[CRSHistoryRead])
def latest_crs(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    history = (
        session.query(CRSHistory)
        .filter(CRSHistory.driver_id == driver_id, CRSHistory.discipline == discipline)
        .order_by(CRSHistory.computed_at.desc())
        .first()
    )
    return history