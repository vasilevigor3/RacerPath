"""Recommendation repository: DB access for recommendations."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation


class RecommendationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_driver_id(
        self, driver_id: str, discipline: str | None = None
    ) -> List[Recommendation]:
        query = self._session.query(Recommendation).filter(Recommendation.driver_id == driver_id)
        if discipline:
            query = query.filter(Recommendation.discipline == discipline)
        return query.order_by(Recommendation.created_at.desc()).all()

    def latest_by_driver(self, driver_id: str) -> Recommendation | None:
        return (
            self._session.query(Recommendation)
            .filter(Recommendation.driver_id == driver_id)
            .order_by(Recommendation.created_at.desc())
            .first()
        )

    def add(self, recommendation: Recommendation) -> None:
        self._session.add(recommendation)
