"""Participation repository: DB access for participations."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState


class ParticipationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(
        self, participation_id: str, with_counts: bool = False
    ) -> Optional[Participation]:
        q = self._session.query(Participation).filter(Participation.id == participation_id)
        if with_counts:
            q = q.options(
                selectinload(Participation.incidents).selectinload(Incident.penalties),
            )
        return q.first()

    def list_filtered(
        self,
        driver_id: Optional[str] = None,
        event_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Participation]:
        query = (
            self._session.query(Participation)
            .options(
                selectinload(Participation.incidents).selectinload(Incident.penalties),
            )
        )
        if driver_id:
            query = query.filter(Participation.driver_id == driver_id)
        if event_id:
            query = query.filter(Participation.event_id == event_id)
        return (
            query.order_by(Participation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_driver_id(self, driver_id: str) -> List[Participation]:
        return (
            self._session.query(Participation)
            .filter(Participation.driver_id == driver_id)
            .order_by(Participation.created_at.desc())
            .all()
        )

    def list_by_driver_id_with_events(
        self, driver_id: str, limit: int = 50
    ) -> List[tuple[Participation, Optional["Event"]]]:
        """Return (Participation, Event) pairs for driver, ordered by started_at desc."""
        from app.models.event import Event
        rows = (
            self._session.query(Participation, Event)
            .outerjoin(Event, Participation.event_id == Event.id)
            .filter(Participation.driver_id == driver_id)
            .order_by(Participation.started_at.desc(), Participation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [(part, ev) for part, ev in rows]

    def list_by_driver_id_and_event_id(
        self, driver_id: str, event_id: str
    ) -> List[Participation]:
        return (
            self._session.query(Participation)
            .filter(
                Participation.driver_id == driver_id,
                Participation.event_id == event_id,
            )
            .all()
        )

    def get_by_driver_and_event(self, driver_id: str, event_id: str) -> Optional[Participation]:
        return (
            self._session.query(Participation)
            .filter(
                Participation.driver_id == driver_id,
                Participation.event_id == event_id,
            )
            .first()
        )

    def get_active_by_driver(self, driver_id: str) -> Optional[Participation]:
        """Current race: participation_state=started, finished_at is null."""
        return (
            self._session.query(Participation)
            .filter(
                Participation.driver_id == driver_id,
                Participation.participation_state == ParticipationState.started,
                Participation.finished_at.is_(None),
            )
            .order_by(Participation.started_at.desc())
            .first()
        )

    def list_by_event_id(self, event_id: str) -> List[Participation]:
        return (
            self._session.query(Participation)
            .filter(Participation.event_id == event_id)
            .all()
        )

    def list_by_event_id_with_drivers(
        self, event_id: str, limit: int = 200
    ) -> List[tuple[Participation, Optional["Driver"]]]:
        """Return (Participation, Driver) pairs for event (incidents/penalties loaded for counts)."""
        from app.models.driver import Driver
        rows = (
            self._session.query(Participation, Driver)
            .outerjoin(Driver, Participation.driver_id == Driver.id)
            .options(
                selectinload(Participation.incidents).selectinload(Incident.penalties),
            )
            .filter(Participation.event_id == event_id)
            .order_by(Participation.started_at.desc(), Participation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [(part, dr) for part, dr in rows]

    def count(self) -> int:
        return self._session.query(Participation).count()

    def add(self, participation: Participation) -> None:
        self._session.add(participation)
