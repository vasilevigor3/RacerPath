from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.participation import Participation
from app.models.user import User
from app.services.auth import require_roles

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
def get_metrics(
    session: Session = Depends(get_session),
    _: User | None = Depends(require_roles("admin")),
):
    return {
        "users": session.query(User).count(),
        "drivers": session.query(Driver).count(),
        "events": session.query(Event).count(),
        "classifications": session.query(Classification).count(),
        "participations": session.query(Participation).count(),
    }