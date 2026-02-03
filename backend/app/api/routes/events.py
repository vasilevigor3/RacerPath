from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.classification import Classification
from app.models.event import Event
from app.models.user import User
from app.repositories.classification import ClassificationRepository
from app.repositories.event import EventRepository
from app.schemas.classification import ClassificationRead
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.classifier import build_event_payload, classify_event, TIER_LABELS
from app.services.auth import require_roles, require_user
from app.services.event_service import (
    events_breakdown,
    events_diagnostic,
    get_event_with_tier,
    infer_discipline,
    list_events as service_list_events,
    list_past_count as service_list_past_count,
    list_past_events as service_list_past_events,
    list_upcoming_count as service_list_upcoming_count,
    list_upcoming_events as service_list_upcoming_events,
)
from app.utils.special_events import special_slot_tier_conflict

router = APIRouter(prefix="/events", tags=["events"])


def _event_create_to_orm_data(payload: EventCreate) -> dict:
    """Event model has no event_status/event_tier; filter schema-only and enum-serialized fields."""
    data = payload.model_dump()
    data.pop("event_status", None)
    data.pop("event_tier", None)
    orm_keys = {c.key for c in Event.__table__.columns}
    return {k: v for k, v in data.items() if k in orm_keys}


@router.post("", response_model=EventRead)
def create_event(
    payload: EventCreate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event = Event(**_event_create_to_orm_data(payload))
    session.add(event)
    session.commit()
    session.refresh(event)

    tier = (payload.event_tier and payload.event_tier.strip()) or "E2"
    # One unique special event per tier per period (day/week/month/year)
    if payload.special_event and event.start_time_utc:
        if special_slot_tier_conflict(session, payload.special_event, event.start_time_utc, tier):
            session.delete(event)
            session.commit()
            raise HTTPException(
                409,
                detail=f"Another event already exists for {payload.special_event} (tier {tier}) in this period. Only one per tier per day/week/month/year.",
            )

    classification_payload = build_event_payload(event, infer_discipline(event))
    classification_data = classify_event(classification_payload)
    classification_data["event_tier"] = tier
    classification_data["tier_label"] = TIER_LABELS.get(tier, tier)

    classification = Classification(event_id=event.id, **classification_data)
    session.add(classification)
    session.commit()

    return EventRead.model_validate(event).model_copy(update={"event_tier": tier})


@router.get("/diagnostic")
def events_empty_diagnostic(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Explain why GET /events?driver_id=... might return []. Use when list is empty."""
    return events_diagnostic(session, driver_id, user.id, user.role or "")


@router.get("", response_model=List[EventRead])
def list_events(
    game: str | None = None,
    country: str | None = None,
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    driver_id: str | None = None,
    same_tier: bool = False,
    rig_filter: bool = True,
    task_code: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    if driver_id and user.role not in {"admin"}:
        from app.repositories.driver import DriverRepository
        driver = DriverRepository(session).get_by_id(driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    return service_list_events(
        session,
        game=game,
        country=country,
        city=city,
        date_from=date_from,
        date_to=date_to,
        driver_id=driver_id,
        same_tier=same_tier,
        rig_filter=rig_filter,
        task_code=task_code,
        user_id=user.id,
        user_role=user.role or "",
    )


@router.get("/upcoming", response_model=List[EventRead])
def list_upcoming_events(
    driver_id: str,
    discipline: str,
    limit: int = 3,
    offset: int = 0,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Upcoming events for driver: start_time_utc > now, tier match, sim_games. Paginated."""
    limit = max(1, min(limit, 50))
    out = service_list_upcoming_events(
        session, driver_id, user.id, user.role or "", limit=limit, offset=offset
    )
    if not out and driver_id:
        from app.repositories.driver import DriverRepository
        if not DriverRepository(session).get_by_id(driver_id):
            raise HTTPException(status_code=404, detail="Driver not found")
    return out


@router.get("/upcoming/count")
def get_upcoming_count(
    driver_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Total count of upcoming events for driver."""
    total = service_list_upcoming_count(session, driver_id, user.id, user.role or "")
    return {"total": total}


@router.get("/past", response_model=List[EventRead])
def list_past_events(
    driver_id: str,
    limit: int = 3,
    offset: int = 0,
    recent_days: int = 30,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Past events for driver: start_time_utc < now, within recent_days. Paginated."""
    if driver_id and user.role not in {"admin"}:
        from app.repositories.driver import DriverRepository
        driver = DriverRepository(session).get_by_id(driver_id)
        if not driver or driver.user_id != user.id:
            raise HTTPException(status_code=403, detail="Insufficient role")
    limit = max(1, min(limit, 50))
    return service_list_past_events(
        session, driver_id, user.id, user.role or "",
        limit=limit, offset=offset, recent_days=recent_days,
    )


@router.get("/past/count")
def get_past_count(
    driver_id: str,
    recent_days: int = 30,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Total count of past events for driver within recent_days."""
    total = service_list_past_count(
        session, driver_id, user.id, user.role or "", recent_days=recent_days
    )
    return {"total": total}


@router.get("/breakdown")
def events_breakdown_route(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Events grouped by country and city: by_country, by_city."""
    return events_breakdown(session)


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    event, event_tier = get_event_with_tier(session, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification = ClassificationRepository(session).get_latest_for_event(event_id)
    difficulty_score = getattr(classification, "difficulty_score", None) if classification else None
    return EventRead.model_validate(event).model_copy(
        update={"event_tier": event_tier, "difficulty_score": difficulty_score}
    )


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: str,
    payload: EventUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)
    event = event_repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    event_tier = data.pop("event_tier", None)
    orm_keys = {c.key for c in Event.__table__.columns}
    for key, value in data.items():
        if key in orm_keys:
            setattr(event, key, value)
    if event_tier is not None:
        classification = classification_repo.get_latest_for_event(event_id)
        if classification:
            classification.event_tier = event_tier
            classification.tier_label = TIER_LABELS.get(event_tier, event_tier)
        else:
            classification = Classification(
                event_id=event_id,
                event_tier=event_tier,
                tier_label=TIER_LABELS.get(event_tier, event_tier),
                difficulty_score=0.0,
                seriousness_score=0.0,
                realism_score=0.0,
                discipline_compatibility={},
                caps_applied=[],
                classification_version="admin_override",
                inputs_hash="",
                inputs_snapshot={},
            )
            classification_repo.add(classification)
    if event.special_event and event.start_time_utc:
        if event_tier is not None:
            effective_tier = event_tier
        else:
            cls = classification_repo.get_latest_for_event(event_id)
            effective_tier = cls.event_tier if cls else "E2"
        if special_slot_tier_conflict(session, event.special_event, event.start_time_utc, effective_tier, exclude_event_id=event_id):
            session.rollback()
            raise HTTPException(
                409,
                detail=f"Another event already exists for {event.special_event} (tier {effective_tier}) in this period. Only one per tier per day/week/month/year.",
            )
    session.commit()
    session.refresh(event)
    classification = classification_repo.get_latest_for_event(event_id)
    event_tier_out = classification.event_tier if classification else "E2"
    return EventRead.model_validate(event).model_copy(update={"event_tier": event_tier_out})


@router.get("/{event_id}/classification", response_model=ClassificationRead)
def get_event_classification(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    classification = ClassificationRepository(session).get_latest_for_event(event_id)
    if not classification:
        raise HTTPException(status_code=404, detail="Classification not found")
    return classification


@router.get("/{event_id}/classifications", response_model=List[ClassificationRead])
def list_event_classifications(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    return ClassificationRepository(session).list_for_events([event_id])


@router.post("/{event_id}/classify", response_model=ClassificationRead)
def reclassify_event(
    event_id: str,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)
    event = event_repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification_payload = build_event_payload(event, infer_discipline(event))
    classification_data = classify_event(classification_payload)
    classification = classification_repo.get_latest_for_event(event.id)
    if not classification:
        classification = Classification(event_id=event.id, **classification_data)
        classification_repo.add(classification)
    else:
        for key, value in classification_data.items():
            setattr(classification, key, value)
    session.commit()
    session.refresh(classification)
    return classification
