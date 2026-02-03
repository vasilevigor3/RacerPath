"""Reset all tasks/licenses/events and create test set. Used by admin API and scripts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.classification import Classification
from app.models.crs_history import CRSHistory
from app.models.driver_license import DriverLicense
from app.models.event import Event
from app.models.incident import Incident
from app.models.license_level import LicenseLevel
from app.models.participation import Participation
from app.models.penalty import Penalty
from app.models.raw_event import RawEvent
from app.models.recommendation import Recommendation
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition
from app.services.classifier import TIER_LABELS, build_event_payload, classify_event

TASK_CODES = ["GT_TEST_FLOW", "GT_TEST_FLOW_2"]
EVENT_TITLE = "Test Flow · E2 Sprint"
EVENT_TIER = "E2"
LICENSE_CODE = "GT_E0_TEST"
LICENSE_NAME = "GT E0 Test"
LICENSE_DESC = "Test license: complete both GT_TEST_FLOW and GT_TEST_FLOW_2 (Test Flow events) to become eligible."
TASK_SPECS = [
    ("GT_TEST_FLOW", "Test flow 1: clean sprint", "Finish a sprint race with zero incidents and penalties (task 1)."),
    ("GT_TEST_FLOW_2", "Test flow 2: clean sprint", "Finish a sprint race with zero incidents and penalties (task 2)."),
]


def reset_all_tasks_licenses_events(session: Session) -> dict:
    """Delete all tasks, licenses, events and related. Returns counts."""
    participation_ids = [row[0] for row in session.query(Participation.id).all()]
    if participation_ids:
        session.query(CRSHistory).filter(
            CRSHistory.computed_from_participation_id.in_(participation_ids)
        ).update(
            {CRSHistory.computed_from_participation_id: None},
            synchronize_session=False,
        )
        session.query(Recommendation).filter(
            Recommendation.computed_from_participation_id.in_(participation_ids)
        ).update(
            {Recommendation.computed_from_participation_id: None},
            synchronize_session=False,
        )
        incident_ids = [r[0] for r in session.query(Incident.id).filter(
            Incident.participation_id.in_(participation_ids)
        ).all()]
        if incident_ids:
            session.query(Penalty).filter(
                Penalty.incident_id.in_(incident_ids)
            ).delete(synchronize_session=False)
        session.query(Incident).filter(
            Incident.participation_id.in_(participation_ids)
        ).delete(synchronize_session=False)

    task_completions_deleted = session.query(TaskCompletion).delete(synchronize_session=False)
    participations_deleted = session.query(Participation).delete(synchronize_session=False)
    session.query(RawEvent).delete(synchronize_session=False)
    session.query(Classification).delete(synchronize_session=False)
    events_deleted = session.query(Event).delete(synchronize_session=False)
    licenses_deleted = session.query(DriverLicense).delete(synchronize_session=False)
    task_definitions_deleted = session.query(TaskDefinition).delete(synchronize_session=False)
    license_levels_deleted = session.query(LicenseLevel).delete(synchronize_session=False)

    return {
        "task_completions": task_completions_deleted,
        "participations": participations_deleted,
        "events": events_deleted,
        "driver_licenses": licenses_deleted,
        "task_definitions": task_definitions_deleted,
        "license_levels": license_levels_deleted,
    }


def create_test_task_and_event_set(session: Session) -> dict:
    """Create GT_TEST_FLOW, GT_TEST_FLOW_2, two events, GT_E0_TEST license. Returns created counts/titles."""
    created_tasks = []
    created_events = []

    for code, name, desc in TASK_SPECS:
        task = session.query(TaskDefinition).filter(TaskDefinition.code == code).first()
        if not task:
            task = TaskDefinition(
                code=code,
                name=name,
                discipline="gt",
                description=desc,
                requirements={"require_clean_finish": True, "min_duration_minutes": 15},
                min_event_tier="E0",
                min_duration_minutes=15.0,
                require_clean_finish=True,
                active=True,
                event_related=True,
                scope="per_participation",
            )
            session.add(task)
            session.flush()
            created_tasks.append(code)

    base_start = datetime.now(timezone.utc) + timedelta(hours=1)
    base_start = base_start.replace(minute=0, second=0, microsecond=0)
    for i, hour_offset in enumerate([0, 1], start=1):
        start_utc = base_start + timedelta(hours=hour_offset)
        task_codes_for_event = [TASK_CODES[i - 1]]
        event = Event(
            title=f"{EVENT_TITLE} #{i}",
            source="script",
            game="ACC",
            start_time_utc=start_utc,
            session_type="race",
            schedule_type="weekly",
            event_type="circuit",
            format_type="sprint",
            duration_minutes=30,
            grid_size_expected=20,
            task_codes=task_codes_for_event,
        )
        session.add(event)
        session.flush()
        payload = build_event_payload(event, "gt")
        classification_data = classify_event(payload)
        classification_data["event_tier"] = EVENT_TIER
        classification_data["tier_label"] = TIER_LABELS.get(EVENT_TIER, EVENT_TIER)
        classification = Classification(event_id=event.id, **classification_data)
        session.add(classification)
        created_events.append(f"{EVENT_TITLE} #{i}")

    level = session.query(LicenseLevel).filter(LicenseLevel.code == LICENSE_CODE).first()
    required = list(TASK_CODES)
    if not level:
        level = LicenseLevel(
            discipline="gt",
            code=LICENSE_CODE,
            name=LICENSE_NAME,
            description=LICENSE_DESC,
            min_crs=0.0,
            required_task_codes=required,
            active=True,
        )
        session.add(level)
    else:
        level.required_task_codes = required

    return {
        "tasks": created_tasks,
        "events": created_events,
        "license": LICENSE_CODE,
    }
