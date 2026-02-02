"""RawEvent repository: DB access for raw events (ingestion)."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.raw_event import RawEvent


class RawEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, raw_event_id: str) -> Optional[RawEvent]:
        return (
            self._session.query(RawEvent)
            .filter(RawEvent.id == raw_event_id)
            .first()
        )

    def list_paginated(self, offset: int = 0, limit: int = 100) -> List[RawEvent]:
        return (
            self._session.query(RawEvent)
            .order_by(RawEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def add(self, raw_event: RawEvent) -> None:
        self._session.add(raw_event)
