from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.models.user import User
from app.schemas.license import DriverLicenseRead, LicenseLevelCreate, LicenseLevelRead
from app.services.licenses import award_license
from app.services.auth import require_roles, require_user

router = APIRouter(prefix="/licenses", tags=["licenses"])


@router.post("/levels", response_model=LicenseLevelRead)
def create_level(
    payload: LicenseLevelCreate,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    level = LicenseLevel(**payload.model_dump())
    session.add(level)
    session.commit()
    session.refresh(level)
    return level


@router.get("/levels", response_model=List[LicenseLevelRead])
def list_levels(
    discipline: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    query = session.query(LicenseLevel)
    if discipline:
        query = query.filter(LicenseLevel.discipline == discipline)
    return query.order_by(LicenseLevel.min_crs.asc()).all()


@router.post("/award", response_model=DriverLicenseRead)
def award(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    awarded = award_license(session, driver_id, discipline)
    if not awarded:
        raise HTTPException(status_code=400, detail="No eligible license level")
    return awarded


@router.get("", response_model=List[DriverLicenseRead])
def list_driver_licenses(
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
    query = session.query(DriverLicense).filter(DriverLicense.driver_id == driver_id)
    if discipline:
        query = query.filter(DriverLicense.discipline == discipline)
    return query.order_by(DriverLicense.awarded_at.desc()).all()
