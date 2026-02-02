"""TierProgressionRule repository: DB access for tier progression rules."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.tier_progression_rule import TierProgressionRule


class TierProgressionRuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_tier(self, tier: str) -> Optional[TierProgressionRule]:
        return (
            self._session.query(TierProgressionRule)
            .filter(TierProgressionRule.tier == tier)
            .first()
        )

    def list_all(self) -> List[TierProgressionRule]:
        return (
            self._session.query(TierProgressionRule)
            .order_by(TierProgressionRule.tier)
            .all()
        )

    def add(self, rule: TierProgressionRule) -> None:
        self._session.add(rule)
