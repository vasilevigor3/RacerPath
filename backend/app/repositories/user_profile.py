"""UserProfile repository: DB access for user profiles."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile


class UserProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_id(self, user_id: str) -> UserProfile | None:
        return (
            self._session.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

    def get_by_user_ids(self, user_ids: list[str]) -> list[UserProfile]:
        if not user_ids:
            return []
        return (
            self._session.query(UserProfile)
            .filter(UserProfile.user_id.in_(user_ids))
            .all()
        )

    def add(self, profile: UserProfile) -> None:
        self._session.add(profile)
