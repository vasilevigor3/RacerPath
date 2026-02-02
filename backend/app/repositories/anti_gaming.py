"""AntiGamingReport repository: DB access for anti-gaming reports."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.anti_gaming import AntiGamingReport


class AntiGamingReportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_driver_id(
        self,
        driver_id: str,
        discipline: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[AntiGamingReport]:
        query = self._session.query(AntiGamingReport).filter(
            AntiGamingReport.driver_id == driver_id
        )
        if discipline:
            query = query.filter(AntiGamingReport.discipline == discipline)
        return (
            query.order_by(AntiGamingReport.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def latest_by_driver_and_discipline(
        self, driver_id: str, discipline: str
    ) -> AntiGamingReport | None:
        return (
            self._session.query(AntiGamingReport)
            .filter(
                AntiGamingReport.driver_id == driver_id,
                AntiGamingReport.discipline == discipline,
            )
            .order_by(AntiGamingReport.created_at.desc())
            .first()
        )

    def add(self, report: AntiGamingReport) -> None:
        self._session.add(report)
