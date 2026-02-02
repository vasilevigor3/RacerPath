"""Penalty repository: DB access for penalties."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.participation import Participation
from app.models.penalty import Penalty


class PenaltyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, penalty_id: str) -> Optional[Penalty]:
        return (
            self._session.query(Penalty)
            .filter(Penalty.id == penalty_id)
            .first()
        )

    def list_by_participation_id(self, participation_id: str) -> List[Penalty]:
        return (
            self._session.query(Penalty)
            .filter(Penalty.participation_id == participation_id)
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
        query = self._session.query(Penalty)
        if participation_id:
            query = query.filter(Penalty.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Penalty.participation_id == Participation.id)
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
        query = self._session.query(Penalty)
        if participation_id:
            query = query.filter(Penalty.participation_id == participation_id)
        if driver_id:
            query = (
                query.join(Participation, Penalty.participation_id == Participation.id)
                .filter(Participation.driver_id == driver_id)
            )
        return query.count()

    def add(self, penalty: Penalty) -> None:
        self._session.add(penalty)
