"""
Mock incident service: for participations with state "started", creates realistic mock incidents.

Runs on the same schedule as mock race (each tick). Picks a subset of "started" participations
and with a configurable probability adds one incident per tick with realistic type, score, lap,
and timestamp (between participation.started_at and now).
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState
from app.repositories.incident import IncidentRepository
from app.schemas.incident import IncidentType

logger = logging.getLogger("racerpath.mock_incident")

# Types and CRS score ranges (realistic)
INCIDENT_CHOICES: List[Tuple[str, str, float, float]] = [
    ("contact", IncidentType.contact.value, 2.0, 5.0),
    ("off_track", IncidentType.off_track.value, 1.0, 4.0),
    ("track_limits", IncidentType.track_limits.value, 0.5, 2.0),
    ("unsafe_rejoin", IncidentType.unsafe_rejoin.value, 4.0, 8.0),
    ("blocking", IncidentType.blocking.value, 3.0, 6.0),
    ("avoidable_contact", IncidentType.avoidable_contact.value, 4.0, 8.0),
    ("other", IncidentType.other.value, 0.0, 3.0),
]


def _started_participations(session: Session) -> List[Participation]:
    """Participations currently in progress (state=started, started_at set)."""
    return (
        session.query(Participation)
        .filter(
            Participation.participation_state == ParticipationState.started,
            Participation.started_at.isnot(None),
        )
        .all()
    )


def tick_mock_incidents(
    session: Session,
    *,
    probability: float = 0.15,
    max_per_tick: int = 3,
) -> dict:
    """
    One tick: for a random subset of "started" participations, create one incident each
    with realistic type, score, lap, timestamp_utc.     Returns incidents_created, driver_discipline_pairs (for CRS recompute).
    """
    now = datetime.now(timezone.utc)
    participations = _started_participations(session)
    if not participations:
        return {"incidents_created": 0, "driver_discipline_pairs": []}

    repo = IncidentRepository(session)
    created = 0
    driver_discipline_pairs: List[Tuple[str, str]] = []

    # Shuffle and cap so we don't add too many per tick
    candidates = list(participations)
    random.shuffle(candidates)
    for part in candidates[:max_per_tick]:
        if random.random() > probability:
            continue
        code, incident_type_str, score_lo, score_hi = random.choice(INCIDENT_CHOICES)
        score = round(random.uniform(score_lo, score_hi), 1)
        severity = random.randint(1, 4)
        lap = (part.laps_completed or 1) if part.laps_completed else 1
        # Timestamp between started_at and now
        started = part.started_at
        if getattr(started, "tzinfo", None) is None and started is not None:
            started = started.replace(tzinfo=timezone.utc)
        if started and now > started:
            ts = started
        else:
            ts = now

        incident = Incident(
            participation_id=part.id,
            code=code,
            score=score,
            incident_type=incident_type_str,
            severity=severity,
            lap=lap,
            timestamp_utc=ts,
            description=None,
        )
        repo.add(incident)
        session.flush()
        try:
            from app.services.timeline_validation import validate_incident_timeline
            event = None
            if part.event_id:
                from app.models.event import Event
                event = session.query(Event).filter(Event.id == part.event_id).first()
            validate_incident_timeline(incident, part, event)
        except ValueError as e:
            logger.warning("mock_incident: timeline validation failed, skipping: %s", e)
            session.delete(incident)
            session.flush()
            continue
        created += 1
        disc = part.discipline.value if hasattr(part.discipline, "value") else str(part.discipline or "gt")
        if (part.driver_id, disc) not in driver_discipline_pairs:
            driver_discipline_pairs.append((part.driver_id, disc))
        logger.info(
            "incident: part_id=%s driver_id=%s type=%s score=%.1f lap=%s",
            part.id[:8], part.driver_id[:8], incident_type_str, score, lap,
        )

    return {"incidents_created": created, "driver_discipline_pairs": driver_discipline_pairs}
