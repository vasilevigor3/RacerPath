"""Participation status change events and handlers. Fired when participation becomes completed."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy.orm import Session

from app.services.participation_completed import on_participation_completed


@dataclass
class ParticipationCompletedEvent:
    driver_id: str
    participation_id: str


_handlers: list[Callable[[Session, ParticipationCompletedEvent], None]] = []


def register_participation_completed_handler(
    handler: Callable[[Session, ParticipationCompletedEvent], None],
) -> None:
    _handlers.append(handler)


def dispatch_participation_completed(
    session: Session, driver_id: str, participation_id: str
) -> None:
    """Run all handlers for participation completed (evaluate_tasks, license award, etc.)."""
    event = ParticipationCompletedEvent(driver_id=driver_id, participation_id=participation_id)
    for h in _handlers:
        h(session, event)


def _handle_participation_completed(session: Session, event: ParticipationCompletedEvent) -> None:
    on_participation_completed(session, event.driver_id, event.participation_id)


# Register default handler: tasks + license
register_participation_completed_handler(_handle_participation_completed)
