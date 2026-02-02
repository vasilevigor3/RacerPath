"""Incident repository: DB access for incidents."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.participation import Participation


class IncidentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, incident_id: str) -> Optional[Incident]:
        return (
            self._session.query(Incident)
            .filter(Incident.id == incident_id)
            .first()
        )

    def list_by_participation_id(self, participation_id: str) -> List[Incident]:
        return (
            self._session.query(Incident)
            .filter(Incident.participation_id == participation_id)
            .order_by(Incident.created_at.desc())
            .all()
        )

    def list_by_participation_ids(
        self, participation_ids: List[str], limit: int = 100
    ) -> List[Incident]:
        if not participation_ids:
            return []
        return (
            self._session.query(Incident)
            .filter(Incident.participation_id.in_(participation_ids))
            .order_by(Incident.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_filtered(
        self,
        driver_id: Optional[str] = None,
        participation_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Incident]:
        query = self._session.query(Incident)
        if participation_id:
            query = query.filter(Incident.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Incident.participation_id == Participation.id)
                .filter(Participation.driver_id == driver_id)
            )
        return (
            query.order_by(Incident.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_participation_id(self, participation_id: str) -> int:
        return (
            self._session.query(Incident)
            .filter(Incident.participation_id == participation_id)
            .count()
        )

    def count_filtered(
        self,
        driver_id: Optional[str] = None,
        participation_id: Optional[str] = None,
    ) -> int:
        query = self._session.query(Incident)
        if participation_id:
            query = query.filter(Incident.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Incident.participation_id == Participation.id)
                .filter(Participation.driver_id == driver_id)
            )
        return query.count()

    def add(self, incident: Incident) -> None:
        self._session.add(incident)
