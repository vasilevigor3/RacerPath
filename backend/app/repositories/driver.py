"""Driver repository: DB access for drivers."""

from sqlalchemy.orm import Session

from app.models.driver import Driver


class DriverRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, driver_id: str) -> Driver | None:
        return self._session.query(Driver).filter(Driver.id == driver_id).first()

    def get_by_user_id(self, user_id: str) -> Driver | None:
        """First driver for user (by created_at desc). For multi-career, use list_for_user + pick one."""
        return (
            self._session.query(Driver)
            .filter(Driver.user_id == user_id)
            .order_by(Driver.created_at.desc())
            .first()
        )

    def get_by_user_id_and_discipline(self, user_id: str, primary_discipline: str) -> Driver | None:
        return (
            self._session.query(Driver)
            .filter(Driver.user_id == user_id, Driver.primary_discipline == primary_discipline)
            .first()
        )

    def list_for_user(self, user_id: str) -> list[Driver]:
        return (
            self._session.query(Driver)
            .filter(Driver.user_id == user_id)
            .order_by(Driver.created_at.desc())
            .all()
        )

    def list_all(self) -> list[Driver]:
        return self._session.query(Driver).order_by(Driver.created_at.desc()).all()

    def count(self) -> int:
        return self._session.query(Driver).count()

    def add(self, driver: Driver) -> None:
        self._session.add(driver)
