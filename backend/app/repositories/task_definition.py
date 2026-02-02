"""TaskDefinition repository: DB access for task definitions."""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.task_definition import TaskDefinition


class TaskDefinitionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, task_id: str) -> Optional[TaskDefinition]:
        return (
            self._session.query(TaskDefinition)
            .filter(TaskDefinition.id == task_id)
            .first()
        )

    def get_by_code(self, code: str) -> Optional[TaskDefinition]:
        return (
            self._session.query(TaskDefinition)
            .filter(TaskDefinition.code == code)
            .first()
        )

    def list_all(self) -> List[TaskDefinition]:
        return (
            self._session.query(TaskDefinition)
            .order_by(TaskDefinition.created_at.desc())
            .all()
        )

    def add(self, task: TaskDefinition) -> None:
        self._session.add(task)
