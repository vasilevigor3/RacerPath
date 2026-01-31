from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.driver import Driver
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.user import User
from app.schemas.incident import IncidentRead
from app.services.auth import require_user

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=List[IncidentRead])
def list_all_incidents(
    driver_id: str | None = None,
    participation_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    query = session.query(Incident)
    if user.role not in {"admin"}:
        driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            return []
        if driver_id and driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
        driver_id = driver.id
        if participation_id:
            participation = (
                session.query(Participation)
                .filter(Participation.id == participation_id)
                .first()
            )
            if not participation:
                return []
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    if participation_id:
        query = query.filter(Incident.participation_id == participation_id)
    if driver_id:
        query = (
            query.join(Participation, Incident.participation_id == Participation.id)
            .filter(Participation.driver_id == driver_id)
        )
    limit = max(1, min(limit, 200))
    return query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    incident = session.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if user.role not in {"admin"}:
        participation = (
            session.query(Participation)
            .filter(Participation.id == incident.participation_id)
            .first()
        )
        driver = session.query(Driver).filter(Driver.id == participation.driver_id).first() if participation else None
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return incident
