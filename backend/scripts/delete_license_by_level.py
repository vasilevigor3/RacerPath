"""Delete a specific license (level_code) for a user by email.
Usage: docker compose exec app python backend/scripts/delete_license_by_level.py <email> <level_code>
Example: docker compose exec app python backend/scripts/delete_license_by_level.py vasilevigor3@gmail.com GT_CLUB
"""
import sys

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.user import User


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python backend/scripts/delete_license_by_level.py <email> <level_code>", file=sys.stderr)
        sys.exit(1)
    email = sys.argv[1].strip()
    level_code = sys.argv[2].strip()
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)
        drivers = session.query(Driver).filter(Driver.user_id == user.id).all()
        if not drivers:
            print(f"No drivers for user {email}")
            sys.exit(1)
        driver_ids = [d.id for d in drivers]
        deleted = session.query(DriverLicense).filter(
            DriverLicense.driver_id.in_(driver_ids),
            DriverLicense.level_code == level_code,
        ).delete(synchronize_session=False)
        session.commit()
        print(f"Deleted {deleted} license(s): {level_code} for {email}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
