from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session, selectinload

from app.models.classification import Classification
from app.services.crs import compute_inputs, compute_inputs_hash
from app.models.crs_history import CRSHistory
from app.models.event import Event
from app.models.driver import Driver
from app.models.participation import Participation, ParticipationState
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition
from app.utils.game_aliases import expand_driver_games_for_event_match
from app.utils.special_events import get_period_bounds

from app.core.constants import REC_ALGO_VERSION, TIER_ORDER


def _latest_crs(session: Session, driver_id: str, discipline: str) -> CRSHistory | None:
    return (
        session.query(CRSHistory)
        .filter(CRSHistory.driver_id == driver_id, CRSHistory.discipline == discipline)
        .order_by(CRSHistory.computed_at.desc())
        .first()
    )


def _latest_classification(session: Session, event_id: str) -> Classification | None:
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )


def _period_for_special_slot(special_value: str, now: datetime) -> tuple[datetime, datetime]:
    """Return (period_start, period_end) in UTC for the day/week/month/year containing now."""
    return get_period_bounds(special_value, now)


def _driver_already_participated_special_in_period(
    session: Session, driver_id: str, special_value: str, period_start: datetime, period_end: datetime
) -> bool:
    """True if driver has at least one participation where they actually ran the race (started or completed, not just registered/withdrawn) in an event with this special_event and start_time_utc in [period_start, period_end]."""
    exists = (
        session.query(Participation.id)
        .join(Event, Participation.event_id == Event.id)
        .filter(
            Participation.driver_id == driver_id,
            Participation.participation_state.in_(
                (ParticipationState.started, ParticipationState.completed)
            ),
            Event.special_event == special_value,
            Event.start_time_utc.isnot(None),
            Event.start_time_utc >= period_start,
            Event.start_time_utc <= period_end,
        )
        .limit(1)
        .first()
    )
    return exists is not None


def _tier_in_range(tier: str, min_tier: str, max_tier: str) -> bool:
    if tier not in TIER_ORDER or min_tier not in TIER_ORDER or max_tier not in TIER_ORDER:
        return False
    return TIER_ORDER.index(min_tier) <= TIER_ORDER.index(tier) <= TIER_ORDER.index(max_tier)


def _tier_range_for_status(status: str) -> tuple[str, str]:
    if status == "ready":
        return "E3", "E4"
    if status == "almost_ready":
        return "E2", "E3"
    return "E1", "E2"


def _build_recommendation_content(
    session: Session, driver_id: str, discipline: str
) -> Tuple[str, str, List[str], List[dict]]:
    """Build (readiness_status, summary, items) for a recommendation.

    Items are built in order:
    1. Participation: one line — either risks (incidents/DNF) or "No participation history yet. Complete 2 classified events."
    2. Missing tasks: "Complete task: {name}" for each active discipline task not yet completed; stop after 5 items total in this block.
    3. Race next: up to 3 events in tier range for readiness, filtered by driver sim_games; "Race next: {title} ({game})".
    4. If driver has sim_games but no events in range: "No eligible events for your selected games."
    """
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    driver_games = expand_driver_games_for_event_match(driver.sim_games or []) if driver else []
    crs = _latest_crs(session, driver_id, discipline)
    crs_score = crs.score if crs else 0.0

    if crs_score >= 85:
        readiness = "ready"
    elif crs_score >= 70:
        readiness = "almost_ready"
    else:
        readiness = "not_ready"

    participations = (
        session.query(Participation)
        .options(selectinload(Participation.incidents))
        .filter(Participation.driver_id == driver_id, Participation.discipline == discipline)
        .order_by(Participation.created_at.desc())
        .limit(20)
        .all()
    )

    items: List[str] = []
    if participations:
        avg_incidents = sum(p.incidents_count for p in participations) / len(participations)
        dnf_rate = sum(1 for p in participations if p.status in {"dnf", "dsq"}) / len(participations)
        if avg_incidents > 2:
            items.append("Risk: High incident rate. Target clean races.")
        if dnf_rate > 0.2:
            items.append("Risk: DNF rate above 20%. Focus on finishing races.")
    else:
        items.append("No participation history yet. Complete 2 classified events.")

    completed_task_ids = {
        completion.task_id
        for completion in session.query(TaskCompletion)
        .filter(TaskCompletion.driver_id == driver_id, TaskCompletion.status == "completed")
        .all()
    }
    missing_tasks = (
        session.query(TaskDefinition)
        .filter(TaskDefinition.active.is_(True), TaskDefinition.discipline == discipline)
        .all()
    )
    for task in missing_tasks:
        if task.id not in completed_task_ids:
            items.append(f"Complete task: {task.name}")
            if len(items) >= 5:
                break

    driver_tier = getattr(driver, "tier", "E0") or "E0"
    now_utc = datetime.now(timezone.utc)
    SPECIAL_SLOTS = [
        ("race_of_day", "Race of the day"),
        ("race_of_week", "Race of the week"),
        ("race_of_month", "Race of the month"),
        ("race_of_year", "Race of the year"),
    ]

    def _get_special_event(special_value: str, now: datetime):
        """Return the designated special event only when driver.tier == event tier, game in driver_games, and start_time_utc > now (not expired)."""
        q = (
            session.query(Event)
            .filter(
                Event.special_event == special_value,
                Event.start_time_utc.isnot(None),
                Event.start_time_utc > now,
            )
            .order_by(Event.start_time_utc.asc().nulls_last(), Event.created_at.desc())
        )
        if driver_games:
            q = q.filter(Event.game.in_(driver_games))
        for event in q.all():
            classification = _latest_classification(session, event.id)
            tier = classification.event_tier if classification else None
            if tier == driver_tier:
                return event
        return None

    def _format_featured(label: str, event, expired: bool = False) -> str:
        if event:
            game_note = f" ({event.game})" if event.game else ""
            return f"{label}: {event.title}{game_note}"
        if expired:
            return f"{label}: Sorry, no suitable event."
        return f"{label}: —"

    special_events: List[dict] = []
    for special_value, label in SPECIAL_SLOTS:
        period_start, period_end = _period_for_special_slot(special_value, now_utc)
        if _driver_already_participated_special_in_period(session, driver_id, special_value, period_start, period_end):
            items.append(f"{label}: completed")
            continue
        event = _get_special_event(special_value, now_utc)
        expired = event is None and (
            session.query(Event.id)
            .filter(Event.special_event == special_value, Event.start_time_utc.isnot(None), Event.start_time_utc <= now_utc)
            .limit(1)
            .first()
            is not None
        )
        items.append(_format_featured(label, event, expired=expired))
        if event and event.start_time_utc:
            special_events.append({
                "slot": special_value,
                "label": label,
                "event_id": str(event.id),
                "start_time_utc": event.start_time_utc,
                "title": event.title,
                "game": event.game,
            })

    summary = (
        f"CRS {crs_score:.1f}. Status: {readiness.replace('_', ' ')}. "
        f"Race next: tier {driver_tier}."
    )
    return readiness, summary, items, special_events


def compute_recommendation(session: Session, driver_id: str, discipline: str) -> Tuple[Recommendation, List[dict]]:
    readiness, summary, items, special_events = _build_recommendation_content(session, driver_id, discipline)
    recommendation = Recommendation(
        driver_id=driver_id,
        discipline=discipline,
        readiness_status=readiness,
        summary=summary,
        items=items,
    )
    session.add(recommendation)
    session.commit()
    session.refresh(recommendation)
    return recommendation, special_events


def recompute_recommendations(
    session: Session,
    driver_id: str,
    discipline: str,
    trigger_participation_id: str | None = None,
) -> Tuple[Recommendation, List[dict]]:
    """Compute recommendation and save with inputs_hash, algo_version, computed_from_participation_id."""
    readiness, summary, items, special_events = _build_recommendation_content(session, driver_id, discipline)
    inputs_snapshot = compute_inputs(session, driver_id, discipline)
    inputs_hash = compute_inputs_hash(inputs_snapshot)
    recommendation = Recommendation(
        driver_id=driver_id,
        discipline=discipline,
        readiness_status=readiness,
        summary=summary,
        items=items,
        inputs_hash=inputs_hash,
        algo_version=REC_ALGO_VERSION,
        computed_from_participation_id=trigger_participation_id,
    )
    session.add(recommendation)
    session.commit()
    session.refresh(recommendation)
    return recommendation, special_events
