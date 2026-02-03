"""Penalty repository: DB access for penalties. Penalty belongs to Incident; participation via incident."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.participation import Participation
from app.models.penalty import Penalty
from app.penalties.scores import DEFAULT_PENALTY_SCORE


class PenaltyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, penalty_id: str, load_incident: bool = False) -> Optional[Penalty]:
        q = self._session.query(Penalty).filter(Penalty.id == penalty_id)
        if load_incident:
            q = q.options(selectinload(Penalty.incident))
        return q.first()

    def list_by_participation_id(self, participation_id: str) -> List[Penalty]:
        return (
            self._session.query(Penalty)
            .join(Incident, Penalty.incident_id == Incident.id)
            .filter(Incident.participation_id == participation_id)
            .order_by(Penalty.created_at.desc())
            .all()
        )

    def list_filtered(
        self,
        driver_id: Optional[str] = None,
        participation_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Penalty]:
        query = (
            self._session.query(Penalty)
            .options(selectinload(Penalty.incident))
            .join(Incident, Penalty.incident_id == Incident.id)
        )
        if participation_id:
            query = query.filter(Incident.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Incident.participation_id == Participation.id)
                .filter(Participation.driver_id == driver_id)
            )
        return (
            query.order_by(Penalty.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_filtered(
        self,
        driver_id: Optional[str] = None,
        participation_id: Optional[str] = None,
    ) -> int:
        query = self._session.query(Penalty).join(Incident, Penalty.incident_id == Incident.id)
        if participation_id:
            query = query.filter(Incident.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Incident.participation_id == Participation.id)
                .filter(Participation.driver_id == driver_id)
            )
        return query.count()

    def sum_score_by_participation_id(self, participation_id: str) -> float:
        """Sum penalty scores for a participation (via incident). Null score treated as DEFAULT_PENALTY_SCORE (legacy)."""
        rows = (
            self._session.query(Penalty.score)
            .join(Incident, Penalty.incident_id == Incident.id)
            .filter(Incident.participation_id == participation_id)
            .all()
        )
        total = 0.0
        for (s,) in rows:
            total += s if s is not None else DEFAULT_PENALTY_SCORE
        return total

    def add(self, penalty: Penalty) -> None:
        self._session.add(penalty)
