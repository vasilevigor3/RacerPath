"""Timeline validation for Event, Participation, Incident, Penalty.

Business rules (all timestamps UTC):
- Event: created_at <= start_time_utc <= finished_time_utc (when set)
- Participation vs Event: event.created_at <= part.created_at <= event.start_time_utc (when set);
  part.finished_at <= event.finished_time_utc (when set)
- Participation: created_at < started_at <= finished_at (when set)
- Incident/Penalty: event.start_time_utc < inc.created_at/pen.created_at;
  part.started_at <= inc.created_at/pen.created_at <= part.finished_at <= event.finished_time_utc (when set)

Raises ValueError with a clear message on violation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.incident import Incident
    from app.models.participation import Participation
    from app.models.penalty import Penalty


def _ensure_tz(dt):
    """Naive datetimes not supported for comparison; caller should pass timezone-aware."""
    if dt is not None and getattr(dt, "tzinfo", None) is None:
        from datetime import timezone
        return dt.replace(tzinfo=timezone.utc)
    return dt


def validate_event_timeline(event: Event) -> None:
    """Event: created_at <= start_time_utc; start_time_utc <= finished_time_utc when set."""
    if event.start_time_utc is not None and event.created_at is not None:
        if _ensure_tz(event.created_at) > _ensure_tz(event.start_time_utc):
            raise ValueError(
                "Event.created_at must be <= Event.start_time_utc; "
                f"got created_at={event.created_at!s} start_time_utc={event.start_time_utc!s}"
            )
    if event.start_time_utc is not None and event.finished_time_utc is not None:
        if _ensure_tz(event.start_time_utc) > _ensure_tz(event.finished_time_utc):
            raise ValueError(
                "Event.start_time_utc must be <= Event.finished_time_utc; "
                f"got start_time_utc={event.start_time_utc!s} finished_time_utc={event.finished_time_utc!s}"
            )


def validate_participation_timeline(participation: Participation, event: Event | None) -> None:
    """Participation: created_at < started_at <= finished_at; vs Event: event.created_at <= part.created_at <= event.start_time_utc; part.finished_at <= event.finished_time_utc."""
    part = participation
    if part.started_at is not None and part.created_at is not None:
        if _ensure_tz(part.created_at) >= _ensure_tz(part.started_at):
            raise ValueError(
                "Participation.created_at must be < Participation.started_at; "
                f"got created_at={part.created_at!s} started_at={part.started_at!s}"
            )
    if part.started_at is not None and part.finished_at is not None:
        if _ensure_tz(part.started_at) > _ensure_tz(part.finished_at):
            raise ValueError(
                "Participation.started_at must be <= Participation.finished_at; "
                f"got started_at={part.started_at!s} finished_at={part.finished_at!s}"
            )
    if event is None:
        return
    if part.created_at is not None and event.created_at is not None:
        if _ensure_tz(event.created_at) > _ensure_tz(part.created_at):
            raise ValueError(
                "Event.created_at must be <= Participation.created_at; "
                f"event.created_at={event.created_at!s} part.created_at={part.created_at!s}"
            )
    if event.start_time_utc is not None and part.created_at is not None:
        if _ensure_tz(part.created_at) > _ensure_tz(event.start_time_utc):
            raise ValueError(
                "Participation.created_at must be <= Event.start_time_utc; "
                f"part.created_at={part.created_at!s} event.start_time_utc={event.start_time_utc!s}"
            )
    if part.finished_at is not None and event.finished_time_utc is not None:
        if _ensure_tz(part.finished_at) > _ensure_tz(event.finished_time_utc):
            raise ValueError(
                "Participation.finished_at must be <= Event.finished_time_utc; "
                f"part.finished_at={part.finished_at!s} event.finished_time_utc={event.finished_time_utc!s}"
            )


def validate_incident_timeline(
    incident: Incident,
    participation: Participation,
    event: Event | None,
) -> None:
    """Incident: part.started_at <= inc.created_at <= part.finished_at; event.start_time_utc < inc.created_at; part.finished_at <= event.finished_time_utc."""
    inc_created = _ensure_tz(incident.created_at) if incident.created_at else None
    if inc_created is None:
        return
    if participation.started_at is not None:
        if inc_created < _ensure_tz(participation.started_at):
            raise ValueError(
                "Incident.created_at must be >= Participation.started_at; "
                f"incident.created_at={incident.created_at!s} part.started_at={participation.started_at!s}"
            )
    if participation.finished_at is not None:
        if inc_created > _ensure_tz(participation.finished_at):
            raise ValueError(
                "Incident.created_at must be <= Participation.finished_at; "
                f"incident.created_at={incident.created_at!s} part.finished_at={participation.finished_at!s}"
            )
    if event is None:
        return
    if event.start_time_utc is not None:
        if inc_created <= _ensure_tz(event.start_time_utc):
            raise ValueError(
                "Incident.created_at must be > Event.start_time_utc; "
                f"incident.created_at={incident.created_at!s} event.start_time_utc={event.start_time_utc!s}"
            )
    if participation.finished_at is not None and event.finished_time_utc is not None:
        if _ensure_tz(participation.finished_at) > _ensure_tz(event.finished_time_utc):
            raise ValueError(
                "Participation.finished_at must be <= Event.finished_time_utc; "
                f"part.finished_at={participation.finished_at!s} event.finished_time_utc={event.finished_time_utc!s}"
            )


def validate_penalty_timeline(
    penalty: Penalty,
    incident: Incident,
    participation: Participation,
    event: Event | None,
) -> None:
    """Penalty: part.started_at <= pen.created_at <= part.finished_at; event.start_time_utc < pen.created_at; same bounds as incident."""
    pen_created = _ensure_tz(penalty.created_at) if penalty.created_at else None
    if pen_created is None:
        return
    if participation.started_at is not None:
        if pen_created < _ensure_tz(participation.started_at):
            raise ValueError(
                "Penalty.created_at must be >= Participation.started_at; "
                f"penalty.created_at={penalty.created_at!s} part.started_at={participation.started_at!s}"
            )
    if participation.finished_at is not None:
        if pen_created > _ensure_tz(participation.finished_at):
            raise ValueError(
                "Penalty.created_at must be <= Participation.finished_at; "
                f"penalty.created_at={penalty.created_at!s} part.finished_at={participation.finished_at!s}"
            )
    if event is None:
        return
    if event.start_time_utc is not None:
        if pen_created <= _ensure_tz(event.start_time_utc):
            raise ValueError(
                "Penalty.created_at must be > Event.start_time_utc; "
                f"penalty.created_at={penalty.created_at!s} event.start_time_utc={event.start_time_utc!s}"
            )
    if participation.finished_at is not None and event.finished_time_utc is not None:
        if _ensure_tz(participation.finished_at) > _ensure_tz(event.finished_time_utc):
            raise ValueError(
                "Participation.finished_at must be <= Event.finished_time_utc; "
                f"part.finished_at={participation.finished_at!s} event.finished_time_utc={event.finished_time_utc!s}"
            )
