"""Remove all users except demo@racerpath.local, vasilevigor3@gmail.com, admin@racerpath.local.
Run from repo root: docker compose exec app python backend/scripts/delete_extra_users.py
"""
from app.db.session import SessionLocal
from app.models.user import User
from app.models.driver import Driver
from app.models.user_profile import UserProfile
from app.models.audit_log import AuditLog

KEEP_EMAILS = {"demo@racerpath.local", "vasilevigor3@gmail.com", "admin@racerpath.local"}


def main() -> None:
    session = SessionLocal()
    try:
        keep_ids = {
            u.id for u in session.query(User).filter(User.email.in_(KEEP_EMAILS)).all()
        }
        to_delete = session.query(User).filter(User.id.notin_(keep_ids)).all()
        if not to_delete:
            print("No extra users to delete.")
            return
        delete_ids = [u.id for u in to_delete]
        print("Deleting users:", [u.email or "(no email)" for u in to_delete])

        session.query(Driver).filter(Driver.user_id.in_(delete_ids)).update(
            {Driver.user_id: None}, synchronize_session="fetch"
        )
        session.query(UserProfile).filter(UserProfile.user_id.in_(delete_ids)).delete(
            synchronize_session="fetch"
        )
        session.query(AuditLog).filter(AuditLog.actor_user_id.in_(delete_ids)).update(
            {AuditLog.actor_user_id: None}, synchronize_session="fetch"
        )
        session.query(User).filter(User.id.in_(delete_ids)).delete(
            synchronize_session="fetch"
        )
        session.commit()
        print("Done. Remaining users:", [u.email for u in session.query(User).all()])
    finally:
        session.close()


if __name__ == "__main__":
    main()
