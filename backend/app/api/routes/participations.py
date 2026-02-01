from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentRead
from app.schemas.participation import ActiveParticipationRead, ParticipationCreate, ParticipationRead
from app.services.tasks import evaluate_tasks
from app.services.auth import require_user

router = APIRouter(prefix="/participations", tags=["participations"])


@router.post("", response_model=ParticipationRead)
def create_participation(
    payload: ParticipationCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    driver = session.query(Driver).filter(Driver.id == payload.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    event = session.query(Event).filter(Event.id == payload.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification = (
        session.query(Classification)
        .filter(Classification.event_id == payload.event_id)
        .first()
    )
    if not classification:
        raise HTTPException(
            status_code=400,
            detail="Event has no classification; participation requires the event to be classified first.",
        )
    existing = (
        session.query(Participation)
        .filter(
            Participation.driver_id == payload.driver_id,
            Participation.event_id == payload.event_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Participation already exists")

    participation = Participation(**payload.model_dump())
    participation.classification_id = classification.id
    session.add(participation)
    session.commit()
    session.refresh(participation)
    evaluate_tasks(session, driver.id, participation.id)
    return participation


@router.get("", response_model=List[ParticipationRead])
def list_participations(
    driver_id: str | None = None,
    event_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    query = session.query(Participation)
    if user.role not in {"admin"}:
        if driver_id:
            driver = session.query(Driver).filter(Driver.id == driver_id).first()
            if not driver or driver.user_id != user.id:
                raise HTTPException(status_code=403, detail="Insufficient role")
        else:
            driver = session.query(Driver).filter(Driver.user_id == user.id).first()
            if not driver:
                return []
            driver_id = driver.id
    if driver_id:
        query = query.filter(Participation.driver_id == driver_id)
    if event_id:
        query = query.filter(Participation.event_id == event_id)
    limit = max(1, min(limit, 200))
    return query.order_by(Participation.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/active", response_model=ActiveParticipationRead | None)
def get_active_participation(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Return the driver's current race (participation_state=started, finished_at is null), if any."""
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return None
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")
    participation = (
        session.query(Participation)
        .filter(
            Participation.driver_id == driver_id,
            Participation.participation_state == ParticipationState.started,
            Participation.finished_at.is_(None),
        )
        .order_by(Participation.started_at.desc())
        .first()
    )
    if not participation:
        return None
    event = session.query(Event).filter(Event.id == participation.event_id).first()
    event_title = event.title if event else None
    return ActiveParticipationRead(
        **ParticipationRead.model_validate(participation).model_dump(),
        event_title=event_title,
    )


@router.get("/{participation_id}", response_model=ParticipationRead)
def get_participation(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    participation = session.query(Participation).filter(Participation.id == participation_id).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = session.query(Driver).filter(Driver.id == participation.driver_id).first()
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return participation


@router.post("/{participation_id}/incidents", response_model=IncidentRead)
def create_incident(
    participation_id: str,
    payload: IncidentCreate,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if participation_id != payload.participation_id:
        raise HTTPException(status_code=400, detail="Participation mismatch")

    participation = session.query(Participation).filter(Participation.id == participation_id).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = session.query(Driver).filter(Driver.id == participation.driver_id).first()
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")

    incident = Incident(**payload.model_dump())
    session.add(incident)
    participation.incidents_count += 1
    session.commit()
    session.refresh(incident)
    return incident


@router.get("/{participation_id}/incidents", response_model=List[IncidentRead])
def list_incidents(
    participation_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    participation = session.query(Participation).filter(Participation.id == participation_id).first()
    if not participation:
        raise HTTPException(status_code=404, detail="Participation not found")
    if user.role not in {"admin"}:
        driver = session.query(Driver).filter(Driver.id == participation.driver_id).first()
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return (
        session.query(Incident)
        .filter(Incident.participation_id == participation_id)
        .order_by(Incident.created_at.desc())
        .all()
    )
