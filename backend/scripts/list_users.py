"""Print all user emails from the database. Run from repo root:
  docker compose exec app python scripts/list_users.py
"""
from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.created_at.asc()).all()
        for u in users:
            print(u.email or "(no email)")
        if not users:
            print("(no users)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
