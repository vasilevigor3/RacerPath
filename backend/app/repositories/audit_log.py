"""AuditLog repository: DB access for audit logs."""

from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_recent(self, limit: int = 200) -> List[AuditLog]:
        return (
            self._session.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def add(self, log: AuditLog) -> None:
        self._session.add(log)
