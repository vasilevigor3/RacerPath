from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.license_level import LicenseLevel
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.driver_license import DriverLicenseRepository
from app.repositories.license_level import LicenseLevelRepository
from app.schemas.license import (
    DriverLicenseRead,
    LicenseLevelCreate,
    LicenseLevelRead,
    LicenseRequirementsRead,
)
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
    LicenseLevelRepository(session).add(level)
    session.commit()
    session.refresh(level)
    return level


@router.get("/levels", response_model=List[LicenseLevelRead])
def list_levels(
    discipline: str | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    return LicenseLevelRepository(session).list_by_discipline(discipline=discipline)


@router.post("/award", response_model=DriverLicenseRead)
def award(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    _: None = Depends(require_roles("admin")),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    awarded = award_license(session, driver_id, discipline)
    if not awarded:
        raise HTTPException(status_code=400, detail="No eligible license level")
    return awarded


@router.get("/latest", response_model=Optional[DriverLicenseRead])
def latest_license(
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
    return DriverLicenseRepository(session).latest_by_driver_and_discipline(driver_id, discipline)


@router.get("/requirements", response_model=LicenseRequirementsRead)
def license_requirements(
    discipline: str,
    driver_id: Optional[str] = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    levels = LicenseLevelRepository(session).list_by_discipline(
        discipline=discipline, active_only=True
    )
    requirements = [
        f"{lev.code}: min CRS {lev.min_crs}" + (
            f", tasks: {','.join(lev.required_task_codes or [])}" if lev.required_task_codes else ""
        )
        for lev in levels
    ]
    next_level = None
    if driver_id and levels:
        driver = DriverRepository(session).get_by_id(driver_id)
        if driver and (user.role == "admin" or driver.user_id == user.id):
            earned = {
                dl.level_code
                for dl in DriverLicenseRepository(session).list_by_driver_id(
                    driver_id, discipline
                )
            }
            for lev in levels:
                if lev.code not in earned:
                    next_level = lev.code
                    break
    elif levels:
        next_level = levels[0].code
    return LicenseRequirementsRead(next_level=next_level, requirements=requirements)


@router.get("", response_model=List[DriverLicenseRead])
def list_driver_licenses(
    driver_id: str,
    discipline: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = DriverRepository(session).get_by_id(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return DriverLicenseRepository(session).list_by_driver_id(driver_id, discipline)
