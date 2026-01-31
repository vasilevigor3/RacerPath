from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.event import Event
from app.models.driver import Driver
from app.models.participation import Participation
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition

TIER_ORDER = ["E0", "E1", "E2", "E3", "E4", "E5"]


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


def compute_recommendation(session: Session, driver_id: str, discipline: str) -> Recommendation:
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    driver_games = driver.sim_games if driver and driver.sim_games else []
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

    min_tier, max_tier = _tier_range_for_status(readiness)
    candidate_query = session.query(Event)
    if driver_games:
        candidate_query = candidate_query.filter(Event.game.in_(driver_games))
    candidate_events = candidate_query.order_by(Event.created_at.desc()).all()
    recommended = []
    for event in candidate_events:
        classification = _latest_classification(session, event.id)
        tier = classification.event_tier if classification else "E2"
        if _tier_in_range(tier, min_tier, max_tier):
            recommended.append(event)
        if len(recommended) >= 3:
            break

    for event in recommended:
        game_note = f" ({event.game})" if event.game else ""
        items.append(f"Race next: {event.title}{game_note}")

    if driver_games and not recommended:
        items.append("No eligible events for your selected games. Add more games or import events.")

    summary = (
        f"CRS {crs_score:.1f}. Status: {readiness.replace('_', ' ')}. "
        f"Recommended events tier range: {min_tier}-{max_tier}."
    )

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
    return recommendation
