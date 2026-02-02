"""DriverLicense repository: DB access for driver licenses."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.driver_license import DriverLicense


class DriverLicenseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_driver_id(
        self, driver_id: str, discipline: str | None = None
    ) -> List[DriverLicense]:
        query = self._session.query(DriverLicense).filter(DriverLicense.driver_id == driver_id)
        if discipline:
            query = query.filter(DriverLicense.discipline == discipline)
        return query.order_by(DriverLicense.awarded_at.desc()).all()

    def latest_by_driver_and_discipline(
        self, driver_id: str, discipline: str
    ) -> DriverLicense | None:
        return (
            self._session.query(DriverLicense)
            .filter(
                DriverLicense.driver_id == driver_id,
                DriverLicense.discipline == discipline,
            )
            .order_by(DriverLicense.awarded_at.desc())
            .first()
        )

    def add(self, license_: DriverLicense) -> None:
        self._session.add(license_)
