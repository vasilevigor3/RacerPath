"""Event business logic: listing, diagnostic, breakdown (uses repos + domain)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.domain.events import TIER_ORDER, infer_discipline as domain_infer_discipline
from app.models.event import Event
from app.repositories.classification import ClassificationRepository
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.schemas.event import EventRead
from app.services.classifier import TIER_LABELS
from app.utils.game_aliases import expand_driver_games_for_event_match
from app.utils.rig_compat import driver_rig_satisfies_event


def infer_discipline(event: Event) -> str:
    """Delegate to domain with event attributes."""
    return domain_infer_discipline(event.event_type, event.car_class_list)


def events_diagnostic(
    session: Session,
    driver_id: str,
    user_id: str,
    user_role: str,
) -> dict[str, Any]:
    """Explain why GET /events?driver_id=... might return []."""
    driver_repo = DriverRepository(session)
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)

    driver = driver_repo.get_by_id(driver_id)
    if not driver or (user_role != "admin" and driver.user_id != user_id):
        return {"reason": "driver_not_found_or_forbidden", "driver_found": False}

    total_in_db = event_repo.count()
    driver_games = list(expand_driver_games_for_event_match(driver.sim_games or []))
    events = event_repo.list_events(game_in=driver_games if driver.sim_games else None)
    event_ids = [e.id for e in events]
    tier_by_event = classification_repo.tier_by_event(event_ids) if event_ids else {}
    driver_tier = getattr(driver, "tier", "E0") or "E0"
    driver_idx = TIER_ORDER.index(driver_tier) if driver_tier in TIER_ORDER else 0
    after_tier = sum(
        1
        for eid in event_ids
        if TIER_ORDER.index(tier_by_event.get(eid, "E2")) >= driver_idx
    )
    if total_in_db == 0:
        reason = "no_events_in_db"
    elif len(events) == 0 and driver.sim_games:
        reason = "no_events_match_sim_games"
    elif after_tier == 0:
        reason = "no_events_match_tier"
    else:
        reason = "ok"
    hint = None
    if reason == "no_events_match_sim_games":
        hint = "Add ACC or Assetto Corsa Competizione to Profile → Sim games to see test events."
    elif reason == "no_events_in_db":
        hint = "Run create_test_task_and_event.py to create test events."
    return {
        "reason": reason,
        "driver_found": True,
        "driver_sim_games": driver.sim_games,
        "driver_tier": driver_tier,
        "events_total_in_db": total_in_db,
        "events_after_game_filter": len(events),
        "events_after_tier_filter": after_tier,
        "hint": hint,
    }


def list_events(
    session: Session,
    *,
    game: str | None = None,
    country: str | None = None,
    city: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    driver_id: str | None = None,
    same_tier: bool = False,
    rig_filter: bool = True,
    task_code: str | None = None,
    user_id: str,
    user_role: str,
) -> list[EventRead]:
    """List events with optional filters; driver_id applies sim_games + tier + rig."""
    driver_repo = DriverRepository(session)
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)

    driver = None
    if driver_id:
        driver = driver_repo.get_by_id(driver_id)
        if not driver:
            return []
        if user_role != "admin" and driver.user_id != user_id:
            return []

    game_in = None
    if driver and driver.sim_games:
        game_in = expand_driver_games_for_event_match(driver.sim_games)

    events = event_repo.list_events(
        game=game,
        country=country,
        city=city,
        date_from=date_from,
        date_to=date_to,
        game_in=game_in,
    )
    if task_code:
        events = [e for e in events if getattr(e, "task_codes", None) and task_code in e.task_codes]
    if not events:
        return []

    event_ids = [e.id for e in events]
    tier_by_event = classification_repo.tier_by_event(event_ids)

    if driver_id and driver:
        driver_tier = getattr(driver, "tier", "E0") or "E0"
        driver_tier_idx = TIER_ORDER.index(driver_tier) if driver_tier in TIER_ORDER else 0
        if same_tier:
            events = [e for e in events if (tier_by_event.get(e.id) or "E2") == driver_tier]
        else:
            events = [
                e
                for e in events
                if TIER_ORDER.index(tier_by_event.get(e.id) or "E2") >= driver_tier_idx
            ]
        if rig_filter:
            events = [e for e in events if driver_rig_satisfies_event(driver.rig_options, e.rig_options)]

    return [
        EventRead.model_validate(e).model_copy(update={"event_tier": tier_by_event.get(e.id) or "E2"})
        for e in events
    ]


def list_upcoming_events(
    session: Session,
    driver_id: str,
    user_id: str,
    user_role: str,
    limit: int = 3,
) -> list[EventRead]:
    """Upcoming events for driver: start_time_utc > now, tier match, sim_games, rig filter."""
    driver_repo = DriverRepository(session)
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)

    driver = driver_repo.get_by_id(driver_id)
    if not driver or (user_role != "admin" and driver.user_id != user_id):
        return []

    driver_tier = getattr(driver, "tier", "E0") or "E0"
    driver_games = expand_driver_games_for_event_match(driver.sim_games or [])

    event_ids = event_repo.list_upcoming_ids(
        driver_tier=driver_tier,
        driver_games=driver_games if driver_games else None,
        limit=limit,
    )
    if not event_ids:
        return []

    events = event_repo.list_by_ids(event_ids, order_by_start=True)
    tier_by_event = classification_repo.tier_by_event(event_ids)
    out = []
    for e in events:
        tier = tier_by_event.get(e.id)
        if tier != driver_tier:
            continue
        if not driver_rig_satisfies_event(driver.rig_options, e.rig_options):
            continue
        out.append(EventRead.model_validate(e).model_copy(update={"event_tier": tier}))
    return out


def events_breakdown(session: Session) -> dict[str, Any]:
    """Events grouped by country and city."""
    event_repo = EventRepository(session)
    by_country = event_repo.breakdown_by_country()
    by_city = event_repo.breakdown_by_city()
    return {
        "by_country": [{"country": c, "count": n} for c, n in by_country],
        "by_city": [{"country": c, "city": t, "count": n} for c, t, n in by_city],
    }


def get_event_with_tier(
    session: Session,
    event_id: str,
) -> tuple[Event | None, str]:
    """Return (event, event_tier). event_tier defaults to E2 if no classification."""
    event_repo = EventRepository(session)
    classification_repo = ClassificationRepository(session)
    event = event_repo.get_by_id(event_id)
    if not event:
        return None, "E2"
    classification = classification_repo.get_latest_for_event(event_id)
    tier = classification.event_tier if classification else "E2"
    return event, tier
