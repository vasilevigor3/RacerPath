from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.event import Event
from app.models.user import User
from app.schemas.classification import ClassificationRead
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.services.classifier import build_event_payload, classify_event, TIER_LABELS
from app.services.auth import require_roles, require_user
from app.utils.game_aliases import expand_driver_games_for_event_match
from app.utils.rig_compat import driver_rig_satisfies_event
from app.utils.special_events import special_slot_tier_conflict

TIER_ORDER = ["E0", "E1", "E2", "E3", "E4", "E5"]

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


def _event_create_to_orm_data(payload: EventCreate) -> dict:
    """Event model has no event_status/event_tier; filter schema-only and enum-serialized fields."""
    data = payload.model_dump()
    data.pop("event_status", None)
    data.pop("event_tier", None)
    orm_keys = {c.key for c in Event.__table__.columns}
    return {k: v for k, v in data.items() if k in orm_keys}


def _tier_range_for_readiness(crs_score: float) -> tuple[str, str]:
    if crs_score >= 85:
        return "E3", "E4"
    if crs_score >= 70:
        return "E2", "E3"
    return "E1", "E2"


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
    if country:
        query = query.filter(Event.country == country)
    if city:
        query = query.filter(Event.city == city)
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
        if not driver:
            return []
        if driver.sim_games:
            query = query.filter(Event.game.in_(expand_driver_games_for_event_match(driver.sim_games)))
        # else: no sim_games filter — show all events (e.g. newcomer before adding games)
        # same_tier filter applied after we have latest classification per event (below)
    events = query.order_by(Event.created_at.desc()).all()
    if not events:
        return []
    # Latest classification per event (same source we use for display)
    event_ids = [e.id for e in events]
    classifications = (
        session.query(Classification)
        .filter(Classification.event_id.in_(event_ids))
        .order_by(Classification.created_at.desc())
        .all()
    )
    tier_by_event = {}
    for c in classifications:
        if c.event_id not in tier_by_event:
            tier_by_event[c.event_id] = c.event_tier
    # Filter by driver tier: same_tier = only exact match; else only events with tier >= driver tier (no E0 for E1+)
    if driver_id and driver:
        driver_tier = getattr(driver, "tier", "E0") or "E0"
        driver_tier_idx = TIER_ORDER.index(driver_tier) if driver_tier in TIER_ORDER else 0
        if same_tier:
            events = [e for e in events if (tier_by_event.get(e.id) or "E2") == driver_tier]
        else:
            events = [
                e for e in events
                if TIER_ORDER.index(tier_by_event.get(e.id) or "E2") >= driver_tier_idx
            ]
    # Filter by rig: only when rig_filter=True (e.g. Recent events can show all without rig filter)
    if driver_id and driver and rig_filter:
        events = [e for e in events if driver_rig_satisfies_event(driver.rig_options, e.rig_options)]
    return [
        EventRead.model_validate(e).model_copy(update={"event_tier": tier_by_event.get(e.id) or "E2"})
        for e in events
    ]


@router.get("/upcoming", response_model=List[EventRead])
def list_upcoming_events(
    driver_id: str,
    discipline: str,
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Upcoming events for driver: start_time_utc > now, event tier matches driver.tier, filtered by sim_games. Max 3."""
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    if user.role not in {"admin"} and driver.user_id != user.id:
        raise HTTPException(status_code=403, detail="Insufficient role")

    driver_tier = getattr(driver, "tier", "E0") or "E0"
    driver_games = expand_driver_games_for_event_match(driver.sim_games or [])

    now = datetime.now(timezone.utc)
    from sqlalchemy import func
    # Only events whose tier matches driver.tier; events without Classification default to E2
    query = (
        session.query(Event)
        .outerjoin(Classification, Event.id == Classification.event_id)
        .filter(
            Event.start_time_utc.isnot(None),
            Event.start_time_utc > now,
            func.coalesce(Classification.event_tier, "E2") == driver_tier,
        )
    )
    if driver_games:
        query = query.filter(Event.game.in_(driver_games))
    # PostgreSQL: DISTINCT ON (x) requires ORDER BY x first. Use subquery to get 3 soonest event ids.
    subq = (
        query.with_entities(Event.id, Event.start_time_utc)
        .group_by(Event.id, Event.start_time_utc)
        .order_by(Event.start_time_utc.asc())
        .limit(3)
    )
    event_ids = [row[0] for row in subq.all()]
    if not event_ids:
        return []
    events = (
        session.query(Event)
        .filter(Event.id.in_(event_ids))
        .order_by(Event.start_time_utc.asc())
        .all()
    )
    # Attach event_tier from Classification; exclude events without matching tier (defensive)
    classifications = (
        session.query(Classification)
        .filter(Classification.event_id.in_(event_ids))
        .all()
    )
    tier_by_event = {c.event_id: c.event_tier for c in classifications}
    out = []
    for e in events:
        tier = tier_by_event.get(e.id)
        if tier != driver_tier:
            continue  # no classification or wrong tier — do not show
        if not driver_rig_satisfies_event(driver.rig_options, e.rig_options):
            continue  # event requires rig driver doesn't have
        out.append(
            EventRead.model_validate(e).model_copy(update={"event_tier": tier})
        )
    return out


@router.get("/breakdown")
def events_breakdown(
    session: Session = Depends(get_session),
    user: User = Depends(require_user()),
):
    """Разбивка событий по странам и городам: by_country, by_city."""
    from sqlalchemy import func

    by_country = (
        session.query(Event.country, func.count(Event.id).label("count"))
        .filter(Event.country.isnot(None), Event.country != "")
        .group_by(Event.country)
        .order_by(func.count(Event.id).desc())
        .all()
    )
    by_city = (
        session.query(Event.country, Event.city, func.count(Event.id).label("count"))
        .filter(Event.city.isnot(None), Event.city != "")
        .group_by(Event.country, Event.city)
        .order_by(Event.country, func.count(Event.id).desc())
        .all()
    )
    return {
        "by_country": [{"country": c, "count": n} for c, n in by_country],
        "by_city": [{"country": c, "city": t, "count": n} for c, t, n in by_city],
    }


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: str,
    session: Session = Depends(get_session),
    _: User = Depends(require_user()),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    classification = (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )
    event_tier = classification.event_tier if classification else "E2"
    return EventRead.model_validate(event).model_copy(update={"event_tier": event_tier})


@router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: str,
    payload: EventUpdate,
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    event = session.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    event_tier = data.pop("event_tier", None)
    orm_keys = {c.key for c in Event.__table__.columns}
    for key, value in data.items():
        if key in orm_keys:
            setattr(event, key, value)
    if event_tier is not None:
        classification = (
            session.query(Classification)
            .filter(Classification.event_id == event_id)
            .order_by(Classification.created_at.desc())
            .first()
        )
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
            session.add(classification)
    # One unique special event per tier per period
    if event.special_event and event.start_time_utc:
        if event_tier is not None:
            effective_tier = event_tier
        else:
            cls = session.query(Classification).filter(Classification.event_id == event_id).order_by(Classification.created_at.desc()).first()
            effective_tier = cls.event_tier if cls else "E2"
        if special_slot_tier_conflict(session, event.special_event, event.start_time_utc, effective_tier, exclude_event_id=event_id):
            session.rollback()
            raise HTTPException(
                409,
                detail=f"Another event already exists for {event.special_event} (tier {effective_tier}) in this period. Only one per tier per day/week/month/year.",
            )
    session.commit()
    session.refresh(event)
    classification = (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )
    event_tier = classification.event_tier if classification else "E2"
    return EventRead.model_validate(event).model_copy(update={"event_tier": event_tier})


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
