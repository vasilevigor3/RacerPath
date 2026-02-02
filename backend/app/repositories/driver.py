"""Driver repository: DB access for drivers."""

from sqlalchemy.orm import Session

from app.models.driver import Driver


class DriverRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, driver_id: str) -> Driver | None:
        return self._session.query(Driver).filter(Driver.id == driver_id).first()

    def get_by_user_id(self, user_id: str) -> Driver | None:
        return self._session.query(Driver).filter(Driver.user_id == user_id).first()

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
