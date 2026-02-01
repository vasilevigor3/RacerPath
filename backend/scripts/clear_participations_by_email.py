"""Delete all participations for a user by email.
Run from repo root:
  docker compose exec app python backend/scripts/clear_participations_by_email.py <email>
Example:
  docker compose exec app python backend/scripts/clear_participations_by_email.py vasilevigor3@gmail.com
"""
import sys

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.user import User


def clear_participations_for_user(session: Session, email: str) -> int:
    user = session.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError(f"User not found: {email}")

    drivers = session.query(Driver).filter(Driver.user_id == user.id).all()
    if not drivers:
        return 0

    driver_ids = [d.id for d in drivers]
    participation_ids = [
        row[0]
        for row in session.query(Participation.id).filter(Participation.driver_id.in_(driver_ids)).all()
    ]
    if not participation_ids:
        return 0

    # Nullify references, then delete dependents, then participations
    session.query(TaskCompletion).filter(
        TaskCompletion.participation_id.in_(participation_ids)
    ).update({TaskCompletion.participation_id: None}, synchronize_session=False)
    session.query(CRSHistory).filter(
        CRSHistory.computed_from_participation_id.in_(participation_ids)
    ).update({CRSHistory.computed_from_participation_id: None}, synchronize_session=False)
    session.query(Recommendation).filter(
        Recommendation.computed_from_participation_id.in_(participation_ids)
    ).update({Recommendation.computed_from_participation_id: None}, synchronize_session=False)

    session.query(Incident).filter(
        Incident.participation_id.in_(participation_ids)
    ).delete(synchronize_session=False)
    session.query(Participation).filter(
        Participation.id.in_(participation_ids)
    ).delete(synchronize_session=False)

    return len(participation_ids)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: clear_participations_by_email.py <email>", file=sys.stderr)
        sys.exit(1)
    email = sys.argv[1].strip()
    session = SessionLocal()
    try:
        count = clear_participations_for_user(session, email)
        session.commit()
        print(f"OK: deleted {count} participation(s) for {email}")
    except ValueError as e:
        session.rollback()
        print(str(e), file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
