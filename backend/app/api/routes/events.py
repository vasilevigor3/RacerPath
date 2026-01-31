from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.user import User
from app.schemas.classification import ClassificationRead
from app.schemas.event import EventCreate, EventRead
from app.services.classifier import build_event_payload, classify_event
from app.services.auth import require_roles, require_user

router = APIRouter(prefix="/events", tags=["events"])


def infer_discipline(event: Event) -> str:
    event_type = event.event_type
    if event_type == "rally_stage":
        return "rally"
    if event_type in {"rallycross", "offroad", "karting"}:
        return "karting"
    if event_type == "historic":
        return "historic"
    for car_class in event.car_class_list or []:
        if "formula" in car_class.lower():
            return "formula"
    return "gt"


@router.post("", response_model=EventRead)
def create_event(
    payload: EventCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event = Event(**payload.model_dump())
    session.add(event)
    session.commit()
    session.refresh(event)

    classification_payload = build_event_payload(event, infer_discipline(event))
    classification_data = classify_event(classification_payload)

    classification = Classification(event_id=event.id, **classification_data)
    session.add(classification)
    session.commit()

    return event


@router.get("", response_model=List[EventRead])
def list_events(
    game: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    driver_id: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    query = session.query(Event)
    if driver_id and user.role not in {"admin"}:
        driver = session.query(Driver).filter(Driver.id == driver_id).first()
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    if game:
        query = query.filter(Event.game == game)
    if date_from:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            query = query.filter(
                (Event.start_time_utc >= dt) | ((Event.start_time_utc.is_(None)) & (Event.created_at >= dt))
            )
        except (ValueError, TypeError):
            pass
    if date_to:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            query = query.filter(
                (Event.start_time_utc <= dt) | ((Event.start_time_utc.is_(None)) & (Event.created_at <= dt))
            )
        except (ValueError, TypeError):
            pass
    if driver_id:
        driver = session.query(Driver).filter(Driver.id == driver_id).first()
        if driver and driver.sim_games:
            query = query.filter(Event.game.in_(driver.sim_games))
        else:
            return []
    return query.order_by(Event.created_at.desc()).all()


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/{event_id}/classification", response_model=ClassificationRead)
def get_event_classification(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    classification = (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification


@router.get("/{event_id}/classifications", response_model=List[ClassificationRead])
def list_event_classifications(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .all()
    )


@router.post("/{event_id}/classify", response_model=ClassificationRead)
def reclassify_event(
    event_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification_payload = build_event_payload(event, infer_discipline(event))
    classification_data = classify_event(classification_payload)
    classification = session.query(Classification).filter(Classification.event_id == event.id).first()
    if not classification:
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)
    else:
        for key, value in classification_data.items():
            setattr(classification, key, value)
    session.commit()
    session.refresh(classification)
    return classification
