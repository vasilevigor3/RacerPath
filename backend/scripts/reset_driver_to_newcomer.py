"""Reset a driver to newcomer state: tier E0, no participations, licenses, CRS, tasks, etc.
Run from repo root:
  docker compose exec app python backend/scripts/reset_driver_to_newcomer.py <driver_id>
Example:
  python backend/scripts/reset_driver_to_newcomer.py 6dac740e-3e20-4038-8ffe-5dce307a56ca
"""
import sys

from app.db.session import SessionLocal
from app.models.anti_gaming import AntiGamingReport
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.real_world_readiness import RealWorldReadiness
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: reset_driver_to_newcomer.py <driver_id>", file=sys.stderr)
        sys.exit(1)
    driver_id = sys.argv[1].strip()
    session = SessionLocal()
    try:
        driver = session.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            print(f"Driver not found: {driver_id}", file=sys.stderr)
            sys.exit(1)

        participation_ids = [
            row[0] for row in session.query(Participation.id).filter(Participation.driver_id == driver_id).all()
        ]

        # Order matters: delete children before parents (incidents -> participations)
        session.query(Incident).filter(Incident.participation_id.in_(participation_ids)).delete(
            synchronize_session=False
        )
        session.query(TaskCompletion).filter(TaskCompletion.driver_id == driver_id).delete(synchronize_session=False)
        session.query(Participation).filter(Participation.driver_id == driver_id).delete(synchronize_session=False)
        session.query(CRSHistory).filter(CRSHistory.driver_id == driver_id).delete(synchronize_session=False)
        session.query(DriverLicense).filter(DriverLicense.driver_id == driver_id).delete(synchronize_session=False)
        session.query(AntiGamingReport).filter(AntiGamingReport.driver_id == driver_id).delete(
            synchronize_session=False
        )
        session.query(RealWorldReadiness).filter(RealWorldReadiness.driver_id == driver_id).delete(
            synchronize_session=False
        )
        session.query(Recommendation).filter(Recommendation.driver_id == driver_id).delete(synchronize_session=False)

        driver.tier = "E0"
        session.commit()
        print(f"OK: driver {driver_id} ({driver.name}) reset to newcomer (tier E0, all participations/licenses/CRS/tasks removed)")
    finally:
        session.close()


if __name__ == "__main__":
    main()
