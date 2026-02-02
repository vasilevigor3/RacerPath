"""LicenseLevel repository: DB access for license levels."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.license_level import LicenseLevel


class LicenseLevelRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, level_id: str) -> Optional[LicenseLevel]:
        return (
            self._session.query(LicenseLevel)
            .filter(LicenseLevel.id == level_id)
            .first()
        )

    def list_all(self) -> List[LicenseLevel]:
        return (
            self._session.query(LicenseLevel)
            .order_by(LicenseLevel.discipline, LicenseLevel.code)
            .all()
        )

    def list_by_discipline(
        self, discipline: str | None = None, active_only: bool = False
    ) -> List[LicenseLevel]:
        query = self._session.query(LicenseLevel)
        if discipline:
            query = query.filter(LicenseLevel.discipline == discipline)
        if active_only:
            query = query.filter(LicenseLevel.active.is_(True))
        return query.order_by(LicenseLevel.min_crs.asc()).all()

    def add(self, level: LicenseLevel) -> None:
        self._session.add(level)
