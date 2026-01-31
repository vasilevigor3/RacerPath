from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.anti_gaming import AntiGamingReport
from app.models.driver import Driver
from app.models.user import User
from app.schemas.anti_gaming import AntiGamingReportRead
from app.services.anti_gaming import evaluate_anti_gaming
from app.services.auth import require_user

router = APIRouter(prefix="/anti-gaming", tags=["anti-gaming"])


@router.post("/evaluate", response_model=AntiGamingReportRead)
def evaluate(
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
    return evaluate_anti_gaming(session, driver_id, discipline)


@router.get("/reports", response_model=List[AntiGamingReportRead])
def list_reports(
    driver_id: str,
    discipline: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 200))
    query = session.query(AntiGamingReport).filter(AntiGamingReport.driver_id == driver_id)
    if discipline:
        query = query.filter(AntiGamingReport.discipline == discipline)
    return query.order_by(AntiGamingReport.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/reports/latest", response_model=AntiGamingReportRead)
def latest_report(
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
    report = (
        session.query(AntiGamingReport)
        .filter(AntiGamingReport.driver_id == driver_id, AntiGamingReport.discipline == discipline)
        .order_by(AntiGamingReport.created_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report