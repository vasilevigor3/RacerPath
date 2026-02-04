"""Clear all data for one user (licenses, task completions, participations, incidents). Email from arg or CLEAR_USER_EMAIL env.

Run from repo root:
  docker compose exec app python backend/scripts/clear_my_user.py <email>
Example:
  docker compose exec app python backend/scripts/clear_my_user.py vasilevigor3@gmail.com
"""
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.db.session import SessionLocal
from app.services.user_clear import clear_user_data


def main() -> None:
    email = (sys.argv[1].strip() if len(sys.argv) > 1 else None) or os.getenv("CLEAR_USER_EMAIL", "").strip()
    if not email:
        print("Usage: python -m scripts.clear_my_user <email>", file=sys.stderr)
        print("   or: CLEAR_USER_EMAIL=your@email.com python -m scripts.clear_my_user", file=sys.stderr)
        sys.exit(1)
    session = SessionLocal()
    try:
        counts = clear_user_data(session, email)
        session.commit()
        print(f"OK for {email}:")
        print(f"  Licenses deleted: {counts['licenses']}")
        print(f"  Task completions deleted: {counts['task_completions']}")
        print(f"  Participations deleted: {counts['participations']}")
    except ValueError as e:
        session.rollback()
        print(str(e), file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
