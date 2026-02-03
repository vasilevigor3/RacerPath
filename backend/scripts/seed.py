from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.incident import Incident
from app.models.license_level import LicenseLevel
from app.models.participation import Participation
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.auth import hash_key, hash_password
from app.services.classifier import build_event_payload, classify_event
from app.services.crs import record_crs
from app.services.licenses import award_license
from app.services.recommendations import compute_recommendation
from app.services.task_templates import seed_templates
from app.services.tasks import ensure_task_completion, evaluate_tasks


def seed() -> None:
    session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        demo_key = "demo-driver-12345678"
        demo_email = "demo@racerpath.local"
        demo_password = "demo12345"
        user = session.query(User).filter(User.name == "Demo Driver").first()
        if not user:
            user = User(
                name="Demo Driver",
                email=demo_email,
                password_hash=hash_password(demo_password),
                role="driver",
                api_key_hash=hash_key(demo_key),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            updated = False
            if not user.email:
                user.email = demo_email
                updated = True
            if not user.password_hash:
                user.password_hash = hash_password(demo_password)
                updated = True
            if updated:
                session.commit()

        profile = session.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(
                user_id=user.id,
                full_name="Igor Vasiliev",
                country="Latvia",
                city="Riga",
                age=29,
                experience_years=6,
                primary_discipline="gt",
                sim_platforms=["iRacing", "ACC"],
                rig="Direct drive, load cell pedals",
                goals="Earn GT Club license and complete endurance checklist.",
                updated_at=datetime.now(timezone.utc),
            )
            session.add(profile)
            session.commit()

        driver = session.query(Driver).filter(Driver.user_id == user.id).first()
        if not driver:
            driver = Driver(
                name="Igor V.",
                primary_discipline="gt",
                sim_games=["Assetto Corsa Competizione", "iRacing"],
                user_id=user.id,
            )
            session.add(driver)
            session.commit()
            session.refresh(driver)
        elif not driver.sim_games:
            driver.sim_games = ["Assetto Corsa Competizione", "iRacing"]
            session.commit()

        suffix = (driver.primary_discipline or "gt").upper()
        ensure_task_completion(session, driver.id, f"ONBOARD_DRIVER_{suffix}")
        if driver.sim_games:
            ensure_task_completion(session, driver.id, f"ONBOARD_GAMES_{suffix}")
        if profile:
            ensure_task_completion(session, driver.id, f"ONBOARD_PROFILE_{suffix}")
        session.commit()

        event_specs = [
            {
                "title": "Weekly GT3 Challenge",
                "source": "wss",
                "game": "Assetto Corsa Competizione",
                "start_time_utc": now - timedelta(days=10),
                "schedule_type": "weekly",
                "event_type": "circuit",
                "format_type": "endurance",
                "duration_minutes": 90,
                "grid_size_expected": 24,
                "class_count": 2,
                "car_class_list": ["gt3", "gt4"],
                "damage_model": "full",
                "penalties": "strict",
                "fuel_usage": "real",
                "tire_wear": "real",
                "weather": "dynamic",
                "night": True,
                "stewarding": "automated",
                "team_event": False,
                "license_requirement": "entry",
                "official_event": True,
                "seed_participation": True,
            },
            {
                "title": "Sprint GT4 Cup",
                "source": "gridfinder",
                "game": "Assetto Corsa Competizione",
                "start_time_utc": now - timedelta(days=6),
                "schedule_type": "daily",
                "event_type": "circuit",
                "format_type": "sprint",
                "duration_minutes": 25,
                "grid_size_expected": 18,
                "class_count": 1,
                "car_class_list": ["gt4"],
                "damage_model": "limited",
                "penalties": "standard",
                "fuel_usage": "normal",
                "tire_wear": "normal",
                "weather": "fixed",
                "night": False,
                "stewarding": "automated",
                "team_event": False,
                "license_requirement": "none",
                "official_event": True,
                "seed_participation": True,
            },
            {
                "title": "Night Rain Enduro",
                "source": "wss",
                "game": "iRacing",
                "start_time_utc": now - timedelta(days=3),
                "schedule_type": "special",
                "event_type": "circuit",
                "format_type": "endurance",
                "duration_minutes": 120,
                "grid_size_expected": 30,
                "class_count": 3,
                "car_class_list": ["gt3", "gt4", "tcr"],
                "damage_model": "full",
                "penalties": "strict",
                "fuel_usage": "real",
                "tire_wear": "real",
                "weather": "dynamic",
                "night": True,
                "stewarding": "human_review",
                "team_event": True,
                "license_requirement": "intermediate",
                "official_event": True,
                "seed_participation": True,
            },
            {
                "title": "60-Minute Consistency Run",
                "source": "wss",
                "game": "Assetto Corsa Competizione",
                "start_time_utc": now - timedelta(days=2),
                "schedule_type": "weekly",
                "event_type": "circuit",
                "format_type": "endurance",
                "duration_minutes": 60,
                "grid_size_expected": 20,
                "class_count": 1,
                "car_class_list": ["gt3"],
                "damage_model": "full",
                "penalties": "strict",
                "fuel_usage": "real",
                "tire_wear": "real",
                "weather": "fixed",
                "night": False,
                "stewarding": "automated",
                "team_event": False,
                "license_requirement": "entry",
                "official_event": True,
                "seed_participation": True,
            },
            {
                "title": "Upcoming GT3 Qualifier",
                "source": "gridfinder",
                "game": "Assetto Corsa Competizione",
                "start_time_utc": now + timedelta(days=4),
                "schedule_type": "special",
                "event_type": "circuit",
                "format_type": "sprint",
                "duration_minutes": 40,
                "grid_size_expected": 26,
                "class_count": 1,
                "car_class_list": ["gt3"],
                "damage_model": "full",
                "penalties": "strict",
                "fuel_usage": "real",
                "tire_wear": "real",
                "weather": "fixed",
                "night": False,
                "stewarding": "automated",
                "team_event": False,
                "license_requirement": "entry",
                "official_event": True,
                "seed_participation": False,
            },
        ]

        events: list[tuple[Event, bool]] = []
        for spec in event_specs:
            seed_participation = spec.pop("seed_participation", True)
            event = session.query(Event).filter(Event.title == spec["title"]).first()
            if not event:
                event = Event(**spec)
                session.add(event)
                session.commit()
                session.refresh(event)
                payload = build_event_payload(event, "gt")
                classification_data = classify_event(payload)
                session.add(Classification(event_id=event.id, **classification_data))
                session.commit()
            else:
                for field, value in spec.items():
                    setattr(event, field, value)
                session.commit()
            events.append((event, seed_participation))

        participations: list[Participation] = []
        seed_events = [event for event, seed_participation in events if seed_participation]
        for index, event in enumerate(seed_events):
            participation = (
                session.query(Participation)
                .filter(Participation.driver_id == driver.id, Participation.event_id == event.id)
                .first()
            )
            if not participation:
                started_at = event.start_time_utc or now - timedelta(days=7 - index)
                finished_at = started_at + timedelta(minutes=event.duration_minutes)
                participation = Participation(
                    driver_id=driver.id,
                    event_id=event.id,
                    discipline="gt",
                    status="finished" if index != 1 else "dnf",
                    position_overall=6 if index == 0 else 12,
                    position_class=3 if index == 0 else 5,
                    laps_completed=45 if index == 0 else 18,
                    consistency_score=7.2 if index == 0 else 6.1,
                    pace_delta=0.8 if index == 0 else 1.4,
                    started_at=started_at,
                    finished_at=finished_at,
                )
                session.add(participation)
                session.commit()
                session.refresh(participation)
            participations.append(participation)

        incident_event = participations[-1]
        if session.query(Incident).filter(Incident.participation_id == incident_event.id).count() == 0:
            for lap in (12, 28):
                session.add(
                    Incident(
                        participation_id=incident_event.id,
                        incident_type="Contact",
                        severity=2,
                        lap=lap,
                        description="Minor contact in traffic.",
                    )
                )
            session.commit()
        # Penalty belongs to Incident; get one incident for this participation to attach penalty
        if incident_event:
            one_incident = session.query(Incident).filter(Incident.participation_id == incident_event.id).first()
            if one_incident and session.query(PenaltyModel).filter(PenaltyModel.incident_id == one_incident.id).count() == 0:
                session.add(
                    PenaltyModel(
                        incident_id=one_incident.id,
                        penalty_type="time_penalty",
                        time_seconds=5,
                        lap=12,
                    )
                )
                session.commit()

        seed_templates(session)
        for participation in participations:
            evaluate_tasks(session, driver.id, participation.id)

        record_crs(session, driver.id, "gt")
        compute_recommendation(session, driver.id, "gt")

        if session.query(LicenseLevel).count() == 0:
            levels = [
                LicenseLevel(
                    discipline="gt",
                    code="GT_ROOKIE",
                    name="GT Rookie",
                    description="Entry license for GT progression.",
                    min_crs=50,
                    required_task_codes=["GT_CLEAN_SPRINT"],
                ),
                LicenseLevel(
                    discipline="gt",
                    code="GT_CLUB",
                    name="GT Club",
                    description="Club-level license with endurance focus.",
                    min_crs=65,
                    required_task_codes=["GT_ENDURANCE_NO_DNF", "GT_NIGHT_RAIN"],
                ),
            ]
            session.add_all(levels)
            session.commit()

        award_license(session, driver.id, "gt")

        session.commit()
        print(f"Demo API key: {demo_key}")
        print(f"Demo login: {demo_email} / {demo_password}")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
