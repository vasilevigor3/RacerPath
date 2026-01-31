"""Set driver.tier by user email. Run from repo root:
  docker compose exec app python backend/scripts/set_driver_tier.py <email> <tier>
Example: python backend/scripts/set_driver_tier.py vasilevigor3@gmail.com E0
"""
import sys

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.user import User

DRIVER_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5")


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: set_driver_tier.py <email> <tier>", file=sys.stderr)
        sys.exit(1)
    email = sys.argv[1].strip()
    tier = sys.argv[2].strip().upper()
    if tier not in DRIVER_TIERS:
        print(f"Tier must be one of {DRIVER_TIERS}", file=sys.stderr)
        sys.exit(1)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}", file=sys.stderr)
            sys.exit(1)
        driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            print(f"No driver for user {email}", file=sys.stderr)
            sys.exit(1)
        driver.tier = tier
        session.commit()
        print(f"OK: driver {driver.id} ({driver.name}) tier set to {tier}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
