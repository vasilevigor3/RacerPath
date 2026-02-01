"""Delete driver records for users with role=admin. Run from repo root:
  docker compose exec app python backend/scripts/delete_admin_drivers.py
"""
from app.db.session import SessionLocal
from app.models.anti_gaming import AntiGamingReport
from app.models.crs_history import CRSHistory
from app.models.driver import Driver
from app.models.driver_license import DriverLicense
from app.models.incident import Incident
from app.models.participation import Participation
from app.models.recommendation import Recommendation
from app.models.real_world_readiness import RealWorldReadiness
from app.models.task_completion import TaskCompletion
from app.models.user import User


def main() -> None:
    session = SessionLocal()
    try:
        admins = [
            u for u in session.query(User).all()
            if (u.role or "").strip().lower() == "admin"
        ]
        admin_ids = [u.id for u in admins]
        if not admin_ids:
            print("No admin users found.")
            return

        driver_ids = [
            d.id for d in session.query(Driver).filter(Driver.user_id.in_(admin_ids)).all()
        ]
        if not driver_ids:
            print("No drivers linked to admin users.")
            return

        print(f"Admin user IDs: {admin_ids}")
        print(f"Driver IDs to remove: {driver_ids}")

        # Delete in dependency order
        participations = session.query(Participation).filter(Participation.driver_id.in_(driver_ids)).all()
        participation_ids = [p.id for p in participations]
        if participation_ids:
            session.query(Incident).filter(Incident.participation_id.in_(participation_ids)).delete(
                synchronize_session=False
            )
        session.query(TaskCompletion).filter(TaskCompletion.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(Participation).filter(Participation.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(CRSHistory).filter(CRSHistory.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(DriverLicense).filter(DriverLicense.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(AntiGamingReport).filter(AntiGamingReport.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(RealWorldReadiness).filter(RealWorldReadiness.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(Recommendation).filter(Recommendation.driver_id.in_(driver_ids)).delete(
            synchronize_session=False
        )
        session.query(Driver).filter(Driver.id.in_(driver_ids)).delete(synchronize_session=False)
        session.commit()
        print(f"Deleted {len(driver_ids)} driver(s) for admin users.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
