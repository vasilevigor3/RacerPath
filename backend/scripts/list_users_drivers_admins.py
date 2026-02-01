"""List all Users, Drivers, and Admins. Run from repo root:
  docker compose exec app python backend/scripts/list_users_drivers_admins.py
"""
from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.user import User


def main() -> None:
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.created_at).all()
        drivers = session.query(Driver).order_by(Driver.created_at).all()
        admins = [u for u in users if (u.role or "").strip().lower() == "admin"]

        print("=== USERS ===")
        print(f"Total: {len(users)}")
        for u in users:
            role = (u.role or "").strip()
            active = getattr(u, "active", True)
            print(f"  id={u.id}  email={u.email or '(none)'}  name={u.name}  role={role}  active={active}")

        print("\n=== DRIVERS ===")
        print(f"Total: {len(drivers)}")
        for d in drivers:
            uid = d.user_id or "(no user)"
            print(f"  id={d.id}  name={d.name}  user_id={uid}  tier={d.tier or 'E0'}")

        print("\n=== ADMINS (users with role=admin) ===")
        print(f"Total: {len(admins)}")
        for u in admins:
            driver = session.query(Driver).filter(Driver.user_id == u.id).first()
            driver_info = f"driver_id={driver.id}" if driver else "no driver"
            print(f"  id={u.id}  email={u.email or '(none)'}  name={u.name}  {driver_info}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
