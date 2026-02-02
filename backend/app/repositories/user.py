"""User repository: DB access for users."""

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: str) -> User | None:
        return self._session.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self._session.query(User).filter(User.email == email).first()

    def get_by_role(self, role: str) -> User | None:
        return self._session.query(User).filter(User.role == role).first()

    def list_all(self) -> list[User]:
        return self._session.query(User).order_by(User.created_at.desc()).all()

    def list_paginated(self, offset: int = 0, limit: int = 100) -> list[User]:
        return (
            self._session.query(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        return self._session.query(User).count()

    def add(self, user: User) -> None:
        self._session.add(user)
