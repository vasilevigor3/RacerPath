"""Classification repository: DB access for event classifications."""

from sqlalchemy.orm import Session

from app.models.classification import Classification


class ClassificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, classification_id: str) -> Classification | None:
        return (
            self._session.query(Classification)
            .filter(Classification.id == classification_id)
            .first()
        )

    def get_latest_for_event(self, event_id: str) -> Classification | None:
        return (
            self._session.query(Classification)
            .filter(Classification.event_id == event_id)
            .order_by(Classification.created_at.desc())
            .first()
        )

    def list_for_events(self, event_ids: list[str]) -> list[Classification]:
        if not event_ids:
            return []
        return (
            self._session.query(Classification)
            .filter(Classification.event_id.in_(event_ids))
            .order_by(Classification.created_at.desc())
            .all()
        )

    def list_for_event_admin(self, event_id: str | None = None) -> list[Classification]:
        """List classifications; if event_id given, filter by it. Ordered by created_at desc."""
        query = self._session.query(Classification).order_by(Classification.created_at.desc())
        if event_id:
            query = query.filter(Classification.event_id == event_id)
        return query.all()

    def tier_by_event(self, event_ids: list[str]) -> dict[str, str]:
        """Return event_id -> event_tier for the latest classification per event."""
        rows = self.list_for_events(event_ids)
        out: dict[str, str] = {}
        for c in rows:
            if c.event_id not in out:
                out[c.event_id] = c.event_tier or "E2"
        return out

    def count(self) -> int:
        return self._session.query(Classification).count()

    def add(self, classification: Classification) -> None:
        self._session.add(classification)
