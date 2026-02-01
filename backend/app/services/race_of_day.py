"""Restart Race of the day: delete current event(s) with all relations, create new one."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event


def restart_race_of_day(session: Session) -> dict:
    """
    Delete all events with special_event=race_of_day (and their participations, incidents,
    classifications; nullify references in task_completions, crs_history, recommendation),
    then create a new Race of the day (E0) event.
    Returns {"deleted_count": int, "new_event_id": str, "new_event_title": str}.
    """
    events = (
        session.query(Event)
        .filter(Event.special_event == "race_of_day")
        .all()
    )
    deleted_count = 0
    for event in events:
        event_id = event.id
        participation_ids = [
            row[0]
            for row in session.query(Participation.id).filter(Participation.event_id == event_id).all()
        ]
        if participation_ids:
            session.query(TaskCompletion).filter(
                TaskCompletion.participation_id.in_(participation_ids)
            ).update({TaskCompletion.participation_id: None}, synchronize_session=False)
            session.query(CRSHistory).filter(
                CRSHistory.computed_from_participation_id.in_(participation_ids)
            ).update({CRSHistory.computed_from_participation_id: None}, synchronize_session=False)
            session.query(Recommendation).filter(
                Recommendation.computed_from_participation_id.in_(participation_ids)
            ).update({Recommendation.computed_from_participation_id: None}, synchronize_session=False)
            session.query(Incident).filter(
                Incident.participation_id.in_(participation_ids)
            ).delete(synchronize_session=False)
            session.query(Participation).filter(
                Participation.event_id == event_id
            ).delete(synchronize_session=False)
        session.query(Classification).filter(Classification.event_id == event_id).delete(
            synchronize_session=False
        )
        session.delete(event)
        deleted_count += 1

    session.flush()

    start_utc = datetime.now(timezone.utc) + timedelta(hours=2)
    start_utc = start_utc.replace(minute=0, second=0, microsecond=0)

    new_event = Event(
        title="Race of the day (E0)",
        source="admin",
        game="ACC",
        start_time_utc=start_utc,
        special_event="race_of_day",
        session_type="race",
        schedule_type="weekly",
        event_type="circuit",
        format_type="sprint",
        duration_minutes=30,
        grid_size_expected=20,
    )
    session.add(new_event)
    session.flush()

    tier = "E0"
    payload = build_event_payload(new_event, "gt")
    classification_data = classify_event(payload)
    classification_data["event_tier"] = tier
    classification_data["tier_label"] = TIER_LABELS.get(tier, tier)
    classification = Classification(event_id=new_event.id, **classification_data)
    session.add(classification)

    session.commit()
    session.refresh(new_event)

    return {
        "deleted_count": deleted_count,
        "new_event_id": str(new_event.id),
        "new_event_title": new_event.title,
        "new_event_start_utc": start_utc.isoformat(),
    }
