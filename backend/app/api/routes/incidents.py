from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.participation import ParticipationStatus
from app.models.user import User
from app.penalties.scores import get_score_for_penalty_type
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.penalty import PenaltyRepository
from app.schemas.incident import IncidentRead, IncidentWithEventRead
from app.schemas.penalty import PenaltyCreateByIncident, PenaltyRead, PenaltyTypeEnum, PenaltyWithEventRead
from app.services.auth import require_user
from app.models.penalty import Penalty

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
        if driver_id:
            driver = DriverRepository(session).get_by_id(driver_id)
            if not driver or driver.user_id != user.id:
                return {"total": 0}
        else:
            driver = DriverRepository(session).get_by_user_id(user.id)
            if not driver:
                return {"total": 0}
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
        if driver_id:
            driver = DriverRepository(session).get_by_id(driver_id)
            if not driver or driver.user_id != user.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
        else:
            driver = DriverRepository(session).get_by_user_id(user.id)
            if not driver:
                return []
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
                code=getattr(inc, "code", None),
                score=getattr(inc, "score", 0.0),
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


@router.post("/{incident_id}/penalties", response_model=PenaltyRead)
def create_penalty_for_incident(
    incident_id: str,
    payload: PenaltyCreateByIncident,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Create a penalty for an incident. Participation is derived from the incident."""
    incident = IncidentRepository(session).get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    participation_id = incident.participation_id
    if user.role not in {"admin"}:
        participation = ParticipationRepository(session).get_by_id(participation_id)
        if not participation:
            raise HTTPException(status_code=404, detail="Participation not found")
        driver = DriverRepository(session).get_by_id(participation.driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    participation = ParticipationRepository(session).get_by_id(participation_id)
    score = payload.score if payload.score is not None else get_score_for_penalty_type(payload.penalty_type.value)
    penalty = Penalty(
        incident_id=incident_id,
        penalty_type=payload.penalty_type.value,
        score=score,
        time_seconds=payload.time_seconds,
        lap=payload.lap,
        description=payload.description,
    )
    PenaltyRepository(session).add(penalty)
    session.flush()
    event = EventRepository(session).get_by_id(participation.event_id) if participation else None
    try:
        from app.services.timeline_validation import validate_penalty_timeline
        validate_penalty_timeline(penalty, incident, participation, event)
    except ValueError as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    if payload.penalty_type == PenaltyTypeEnum.dsq and participation:
        participation.status = ParticipationStatus.dsq
    session.commit()
    session.refresh(penalty)
    session.refresh(penalty, attribute_names=["incident"])
    return penalty


@router.get("/{incident_id}/penalties", response_model=List[PenaltyWithEventRead])
def list_penalties_by_incident(
    incident_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Return penalties for this incident (for incident card penalty section)."""
    incident = IncidentRepository(session).get_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if user.role not in {"admin"}:
        participation = ParticipationRepository(session).get_by_id(incident.participation_id)
        driver = DriverRepository(session).get_by_id(participation.driver_id) if participation else None
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    penalties = PenaltyRepository(session).list_by_incident_id(incident_id)
    if not penalties:
        return []
    part_repo = ParticipationRepository(session)
    event_repo = EventRepository(session)
    result = []
    for p in penalties:
        inc = IncidentRepository(session).get_by_id(p.incident_id)
        part = part_repo.get_by_id(inc.participation_id) if inc else None
        event = event_repo.get_by_id(part.event_id) if part else None
        result.append(
            PenaltyWithEventRead(
                id=p.id,
                incident_id=p.incident_id,
                penalty_type=p.penalty_type,
                score=p.score,
                time_seconds=p.time_seconds,
                lap=p.lap,
                description=p.description,
                created_at=p.created_at,
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
