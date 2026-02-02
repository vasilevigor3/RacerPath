"""Event repository: DB access for events."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.event import Event


class EventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, event_id: str) -> Event | None:
        return self._session.query(Event).filter(Event.id == event_id).first()

    def count(self) -> int:
        return self._session.query(Event).count()

    def list_events(
        self,
        *,
        game: str | None = None,
        country: str | None = None,
        city: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        game_in: List[str] | None = None,
        order_desc: bool = True,
    ) -> List[Event]:
        query = self._session.query(Event)
        if game:
            query = query.filter(Event.game == game)
        if country:
            query = query.filter(Event.country == country)
        if city:
            query = query.filter(Event.city == city)
        if date_from:
            try:
                dt = _parse_iso_datetime(date_from)
                query = query.filter(
                    (Event.start_time_utc >= dt)
                    | ((Event.start_time_utc.is_(None)) & (Event.created_at >= dt))
                )
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                dt = _parse_iso_datetime(date_to)
                query = query.filter(
                    (Event.start_time_utc <= dt)
                    | ((Event.start_time_utc.is_(None)) & (Event.created_at <= dt))
                )
            except (ValueError, TypeError):
                pass
        if game_in:
            query = query.filter(Event.game.in_(game_in))
        if order_desc:
            query = query.order_by(Event.created_at.desc())
        return query.all()

    def list_by_ids(self, event_ids: List[str], order_by_start: bool = False) -> List[Event]:
        if not event_ids:
            return []
        query = self._session.query(Event).filter(Event.id.in_(event_ids))
        if order_by_start:
            query = query.order_by(Event.start_time_utc.asc())
        else:
            query = query.order_by(Event.created_at.desc())
        return query.all()

    def breakdown_by_country(self) -> List[tuple[str, int]]:
        rows = (
            self._session.query(Event.country, func.count(Event.id).label("count"))
            .filter(Event.country.isnot(None), Event.country != "")
            .group_by(Event.country)
            .order_by(func.count(Event.id).desc())
            .all()
        )
        return [(r[0], r[1]) for r in rows]

    def breakdown_by_city(self) -> List[tuple[str, str, int]]:
        rows = (
            self._session.query(Event.country, Event.city, func.count(Event.id).label("count"))
            .filter(Event.city.isnot(None), Event.city != "")
            .group_by(Event.country, Event.city)
            .order_by(Event.country, func.count(Event.id).desc())
            .all()
        )
        return [(r[0], r[1], r[2]) for r in rows]

    def add(self, event: Event) -> None:
        self._session.add(event)

    def list_upcoming_ids(
        self,
        driver_tier: str,
        driver_games: List[str] | None = None,
        limit: int = 3,
    ) -> List[str]:
        """Event ids with start_time_utc > now, tier match, optional game filter; order by start, limit."""
        now = datetime.now(timezone.utc)
        query = (
            self._session.query(Event.id)
            .outerjoin(Classification, Event.id == Classification.event_id)
            .filter(
                Event.start_time_utc.isnot(None),
                Event.start_time_utc > now,
                func.coalesce(Classification.event_tier, "E2") == driver_tier,
            )
        )
        if driver_games:
            query = query.filter(Event.game.in_(driver_games))
        subq = (
            query.with_entities(Event.id, Event.start_time_utc)
            .group_by(Event.id, Event.start_time_utc)
            .order_by(Event.start_time_utc.asc())
            .limit(limit)
        )
        rows = subq.all()
        return [row[0] for row in rows]


def _parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
