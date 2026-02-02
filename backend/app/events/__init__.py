"""In-process event dispatch for entity status changes. Handlers run sync; later can be replaced by a broker."""

from app.events.participation_events import (
    dispatch_participation_completed,
    ParticipationCompletedEvent,
)

__all__ = [
    "ParticipationCompletedEvent",
    "dispatch_participation_completed",
]
