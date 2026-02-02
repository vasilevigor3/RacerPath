"""RealWorldFormat and RealWorldReadiness repositories."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.real_world_format import RealWorldFormat
from app.models.real_world_readiness import RealWorldReadiness


class RealWorldFormatRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> List[RealWorldFormat]:
        return (
            self._session.query(RealWorldFormat)
            .order_by(RealWorldFormat.discipline, RealWorldFormat.code)
            .all()
        )

    def list_by_discipline(self, discipline: str | None = None) -> List[RealWorldFormat]:
        query = self._session.query(RealWorldFormat)
        if discipline:
            query = query.filter(RealWorldFormat.discipline == discipline)
        return query.order_by(RealWorldFormat.min_crs.asc()).all()

    def add(self, fmt: RealWorldFormat) -> None:
        self._session.add(fmt)


class RealWorldReadinessRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_driver_id(
        self,
        driver_id: str,
        discipline: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[RealWorldReadiness]:
        query = self._session.query(RealWorldReadiness).filter(
            RealWorldReadiness.driver_id == driver_id
        )
        if discipline:
            query = query.filter(RealWorldReadiness.discipline == discipline)
        return (
            query.order_by(RealWorldReadiness.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def latest_by_driver_and_discipline(
        self, driver_id: str, discipline: str
    ) -> RealWorldReadiness | None:
        return (
            self._session.query(RealWorldReadiness)
            .filter(
                RealWorldReadiness.driver_id == driver_id,
                RealWorldReadiness.discipline == discipline,
            )
            .order_by(RealWorldReadiness.created_at.desc())
            .first()
        )

    def add(self, readiness: RealWorldReadiness) -> None:
        self._session.add(readiness)
