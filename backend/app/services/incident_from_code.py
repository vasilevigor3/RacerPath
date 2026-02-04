"""
Create incident from platform code (e.g. acc_off_track_time_penalty).
Shared by API and mock: backend resolves score, incident_type, penalty from config and creates Incident + Penalty when needed.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.incident_config import get_incident_by_code, normalize_game_to_platform, validate_code_for_platform
from app.models.incident import Incident
from app.models.participation import ParticipationStatus
from app.models.penalty import Penalty
from app.penalties.scores import get_score_for_penalty_type
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.penalty import PenaltyRepository
from app.schemas.incident import incident_type_from_string


def create_incident_from_code(
    session: Session,
    participation_id: str,
    code: str,
    *,
    severity: int = 1,
    lap: int | None = None,
    timestamp_utc=None,
    description: str | None = None,
) -> Incident:
    """
    Create Incident (and Penalty when config says so) from a platform code.
    Uses event.game to resolve platform; looks up code in config; creates Incident + Penalty if penalty != no_penalty.
    Does not commit; caller must commit. Raises ValueError on validation failure.
    """
    part_repo = ParticipationRepository(session)
    event_repo = EventRepository(session)
    participation = part_repo.get_by_id(participation_id)
    if not participation:
        raise ValueError("Participation not found")
    event = event_repo.get_by_id(participation.event_id) if participation.event_id else None
    platform = normalize_game_to_platform(event.game if event else None)
    if not platform:
        raise ValueError("Event game is not set or not supported. Set event game to AC (or ACC) or iRacing for incident codes.")
    ok, err_msg = validate_code_for_platform(platform, code)
    if not ok:
        raise ValueError(err_msg)
    config_entry = get_incident_by_code(platform, code)
    if not config_entry:
        raise ValueError("Unknown incident code for this event platform.")
    score = config_entry["score"]
    incident_type_value = incident_type_from_string(config_entry["incident_type"]).value
    incident = Incident(
        participation_id=participation_id,
        code=code,
        score=score,
        incident_type=incident_type_value,
        severity=severity,
        lap=lap,
        timestamp_utc=timestamp_utc,
        description=description,
    )
    IncidentRepository(session).add(incident)
    session.flush()
    from app.services.timeline_validation import validate_incident_timeline
    validate_incident_timeline(incident, participation, event)
    penalty_type = config_entry.get("penalty") or "no_penalty"
    if penalty_type and penalty_type != "no_penalty":
        time_seconds = config_entry.get("time_seconds") if penalty_type == "time_penalty" else None
        penalty = Penalty(
            incident_id=incident.id,
            penalty_type=penalty_type,
            score=get_score_for_penalty_type(penalty_type),
            time_seconds=time_seconds,
            lap=lap,
            description=None,
        )
        PenaltyRepository(session).add(penalty)
        session.flush()
        if penalty_type == "dsq":
            participation.status = ParticipationStatus.dsq
        from app.services.timeline_validation import validate_penalty_timeline
        validate_penalty_timeline(penalty, incident, participation, event)
    return incident
