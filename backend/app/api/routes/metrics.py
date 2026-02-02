from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.user import User
from app.repositories.classification import ClassificationRepository
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.user import UserRepository
from app.services.auth import require_roles

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return {
        "users": UserRepository(session).count(),
        "drivers": DriverRepository(session).count(),
        "events": EventRepository(session).count(),
        "classifications": ClassificationRepository(session).count(),
        "participations": ParticipationRepository(session).count(),
    }