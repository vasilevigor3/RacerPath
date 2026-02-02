"""Diagnose license required_task_codes vs driver completed tasks.
Usage: docker compose exec app python backend/scripts/license_required_tasks_diagnostic.py <driver_id_or_email> [discipline]
Shows: license levels with required_task_codes, driver completed task codes, which level would be awarded.
"""
import sys

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.services.licenses import _completed_task_codes, _latest_crs


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/license_required_tasks_diagnostic.py <driver_id|email> [discipline]", file=sys.stderr)
        sys.exit(1)
    session = SessionLocal()
    try:
        q = sys.argv[1].strip()
        discipline = (sys.argv[2].strip() if len(sys.argv) > 2 else "gt").lower()
        driver = session.query(Driver).filter(Driver.id == q).first()
        if not driver:
            from app.models.user import User
            user = session.query(User).filter(User.email == q).first()
            if user:
                driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            print(f"Driver not found: {q}")
            sys.exit(1)
        driver_id = driver.id
        completed_codes = _completed_task_codes(session, driver_id)
        crs = _latest_crs(session, driver_id, discipline)
        earned = {
            lic.level_code
            for lic in session.query(DriverLicense)
            .filter(DriverLicense.driver_id == driver_id, DriverLicense.discipline == discipline)
            .all()
        }
        levels = (
            session.query(LicenseLevel)
            .filter(LicenseLevel.discipline == discipline, LicenseLevel.active.is_(True))
            .order_by(LicenseLevel.min_crs.asc())
            .all()
        )
        print(f"Driver: {driver_id} ({getattr(driver, 'name', '')})")
        print(f"Discipline: {discipline}")
        print(f"CRS: {crs.score if crs else None}")
        print(f"Completed task codes (for license): {sorted(completed_codes) or '[]'}")
        print(f"Earned licenses: {sorted(earned) or '[]'}")
        print()
        for lev in levels:
            req = list(lev.required_task_codes) if isinstance(lev.required_task_codes, list) else []
            missing = set(req) - completed_codes
            has_all = not missing
            would_pass = lev.code not in earned and (crs and crs.score >= lev.min_crs) and has_all
            print(f"  {lev.code}: min_crs={lev.min_crs}, required_task_codes={req}")
            print(f"    -> missing={sorted(missing) or 'none'}, has_all={has_all}, would_award={would_pass}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
