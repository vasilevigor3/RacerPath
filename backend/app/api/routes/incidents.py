from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.participation import ParticipationRepository
from app.schemas.incident import IncidentRead, IncidentWithEventRead
from app.services.auth import require_user

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/count")
def get_incidents_count(
    driver_id: str | None = None,
    participation_id: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Return total count of incidents for the current driver (or filtered)."""
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_user_id(user.id)
        if not driver:
            return {"total": 0}
        if driver_id and driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
        driver_id = driver.id
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return {"total": 0}
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    total = IncidentRepository(session).count_filtered(
        driver_id=driver_id, participation_id=participation_id
    )
    return {"total": total}


@router.get("", response_model=List[IncidentWithEventRead])
def list_all_incidents(
    driver_id: str | None = None,
    participation_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if user.role not in {"admin"}:
        driver = DriverRepository(session).get_by_user_id(user.id)
        if not driver:
            return []
        if driver_id and driver_id != driver.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
        driver_id = driver.id
        if participation_id:
            participation = ParticipationRepository(session).get_by_id(participation_id)
            if not participation:
                return []
            if participation.driver_id != driver.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 200))
    incidents = IncidentRepository(session).list_filtered(
        driver_id=driver_id, participation_id=participation_id, offset=offset, limit=limit
    )
    if not incidents:
        return []
    part_repo = ParticipationRepository(session)
    event_repo = EventRepository(session)
    result = []
    for inc in incidents:
        part = part_repo.get_by_id(inc.participation_id)
        event = event_repo.get_by_id(part.event_id) if part else None
        result.append(
            IncidentWithEventRead(
                id=inc.id,
                participation_id=inc.participation_id,
                incident_type=inc.incident_type,
                severity=inc.severity,
                lap=inc.lap,
                timestamp_utc=inc.timestamp_utc,
                description=inc.description,
                created_at=inc.created_at,
                event_id=part.event_id if part else None,
                event_title=event.title if event else "",
                event_start_time_utc=event.start_time_utc if event else None,
            )
        )
    return result


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    incident = IncidentRepository(session).get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if user.role not in {"admin"}:
        participation = ParticipationRepository(session).get_by_id(incident.participation_id)
        driver = DriverRepository(session).get_by_id(participation.driver_id) if participation else None
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return incident
