"""TaskCompletion repository: DB access for task completions."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task_completion import TaskCompletion


class TaskCompletionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, completion_id: str) -> Optional[TaskCompletion]:
        return (
            self._session.query(TaskCompletion)
            .filter(TaskCompletion.id == completion_id)
            .first()
        )

    def list_by_driver_id(self, driver_id: str) -> List[TaskCompletion]:
        return (
            self._session.query(TaskCompletion)
            .filter(TaskCompletion.driver_id == driver_id)
            .order_by(TaskCompletion.created_at.desc())
            .all()
        )

    def list_by_driver_and_participation(
        self, driver_id: str, participation_id: str
    ) -> List[TaskCompletion]:
        return (
            self._session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.participation_id == participation_id,
            )
            .all()
        )

    def find_global_completion(
        self, driver_id: str, task_id: str
    ) -> Optional[TaskCompletion]:
        return (
            self._session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.participation_id.is_(None),
                TaskCompletion.period_key.is_(None),
            )
            .first()
        )

    def find_pending_or_in_progress(
        self, driver_id: str, task_id: str
    ) -> Optional[TaskCompletion]:
        """Latest completion for this driver+task with status pending or in_progress (for Decline)."""
        return (
            self._session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task_id,
                TaskCompletion.status.in_(["pending", "in_progress"]),
            )
            .order_by(TaskCompletion.created_at.desc())
            .first()
        )

    def list_by_driver(self, driver_id: str, task_id: str | None = None) -> List[TaskCompletion]:
        query = self._session.query(TaskCompletion).filter(TaskCompletion.driver_id == driver_id)
        if task_id:
            query = query.filter(TaskCompletion.task_id == task_id)
        return query.order_by(TaskCompletion.created_at.desc()).all()

    def delete_by_participation_and_status(
        self, participation_id: str, statuses: List[str]
    ) -> None:
        self._session.query(TaskCompletion).filter(
            TaskCompletion.participation_id == participation_id,
            TaskCompletion.status.in_(statuses),
        ).delete(synchronize_session=False)

    def add(self, completion: TaskCompletion) -> None:
        self._session.add(completion)
