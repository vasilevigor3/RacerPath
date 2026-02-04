"""Delete all licenses, task completions, and participations for a user by email.

Run from repo root:
  docker compose exec app python backend/scripts/clear_user_licenses_tasks_participations.py <email>
Example:
  docker compose exec app python backend/scripts/clear_user_licenses_tasks_participations.py vasilevigor3@gmail.com
"""
import sys

from app.db.session import SessionLocal
from app.services.user_clear import clear_user_data


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: clear_user_licenses_tasks_participations.py <email>",
            file=sys.stderr,
        )
        sys.exit(1)
    email = sys.argv[1].strip()
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
