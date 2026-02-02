"""Check license eligibility for a driver by email. Shows why Eligible is Yes/No.

Run from repo root:
  docker compose exec app python backend/scripts/check_license_eligibility.py <email> [discipline]
Example:
  docker compose exec app python backend/scripts/check_license_eligibility.py vasilevigor3@gmail.com gt
"""
import sys

from app.db.session import SessionLocal
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.license_level import LicenseLevel
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition
from app.models.user import User
from app.services.licenses import check_eligibility, _completed_task_codes, _latest_crs


def main() -> None:
    email = (sys.argv[1] or "").strip()
    discipline = (sys.argv[2] or "gt").strip().lower()
    if not email:
        print("Usage: python backend/scripts/check_license_eligibility.py <email> [discipline]")
        sys.exit(1)

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)
        driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            print(f"User {email} has no driver.")
            sys.exit(1)

        print(f"Driver: {driver.name}  id={driver.id}")
        print(f"Discipline: {discipline}")
        print()

        # CRS
        crs = _latest_crs(session, driver.id, discipline)
        if crs:
            print(f"Current CRS: {crs.score}  (computed_at={crs.computed_at})")
        else:
            print("Current CRS: (none)")
        print()

        # Task completions (all)
        completions = (
            session.query(TaskCompletion, TaskDefinition)
            .join(TaskDefinition, TaskCompletion.task_id == TaskDefinition.id)
            .filter(TaskCompletion.driver_id == driver.id)
            .all()
        )
        print(f"Task completions (all): {len(completions)}")
        for tc, td in completions:
            has_part = "yes" if tc.participation_id else "no"
            print(f"  task_id={tc.task_id}  code={td.code!r}  status={tc.status}  participation_id={has_part}")
        print()

        # Completed task codes that count for license (status=completed + participation_id set)
        completed_codes = _completed_task_codes(session, driver.id)
        print(f"Completed task codes (for license): {sorted(completed_codes) or '—'}")
        print()

        # License levels for discipline
        levels = (
            session.query(LicenseLevel)
            .filter(LicenseLevel.discipline == discipline, LicenseLevel.active.is_(True))
            .order_by(LicenseLevel.min_crs.asc())
            .all()
        )
        print(f"License levels ({discipline}): {len(levels)}")
        earned = {
            lic.level_code
            for lic in session.query(DriverLicense)
            .filter(DriverLicense.driver_id == driver.id, DriverLicense.discipline == discipline)
            .all()
        }
        for lev in levels:
            have = "earned" if lev.code in earned else "not earned"
            req = lev.required_task_codes or []
            missing = set(req) - completed_codes
            print(f"  {lev.code}: min_crs={lev.min_crs}  required_tasks={req}  [{have}]  missing={sorted(missing) or 'none'}")
        print()

        # Eligibility result
        result = check_eligibility(session, driver.id, discipline)
        print("Eligibility (check_eligibility):")
        print(f"  eligible: {result.eligible}")
        print(f"  next_level_code: {result.next_level_code}")
        print(f"  reasons: {result.reasons or '—'}")
        print(f"  completed_task_codes: {result.completed_task_codes or '—'}")
        print(f"  required_task_codes (for next): {result.required_task_codes or '—'}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
