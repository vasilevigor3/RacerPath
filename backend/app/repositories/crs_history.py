"""CRSHistory repository: DB access for CRS history."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.crs_history import CRSHistory


class CRSHistoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_driver_id(
        self, driver_id: str, discipline: str | None = None
    ) -> List[CRSHistory]:
        query = self._session.query(CRSHistory).filter(CRSHistory.driver_id == driver_id)
        if discipline:
            query = query.filter(CRSHistory.discipline == discipline)
        return query.order_by(CRSHistory.computed_at.desc()).all()

    def latest_by_driver(self, driver_id: str) -> CRSHistory | None:
        return (
            self._session.query(CRSHistory)
            .filter(CRSHistory.driver_id == driver_id)
            .order_by(CRSHistory.computed_at.desc())
            .first()
        )

    def latest_by_driver_and_discipline(
        self, driver_id: str, discipline: str
    ) -> CRSHistory | None:
        return (
            self._session.query(CRSHistory)
            .filter(
                CRSHistory.driver_id == driver_id,
                CRSHistory.discipline == discipline,
            )
            .order_by(CRSHistory.computed_at.desc())
            .first()
        )

    def add(self, record: CRSHistory) -> None:
        self._session.add(record)
