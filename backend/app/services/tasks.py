from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json

from sqlalchemy.orm import Session, selectinload

from app.models.classification import Classification
from app.models.driver import Driver
from app.models.event import Event
from app.models.incident import Incident
from app.models.participation import Participation, ParticipationState
from app.models.task_completion import TaskCompletion
from app.models.task_definition import TaskDefinition

from app.core.constants import TIER_RANK


def _get_req(task: TaskDefinition, key: str, default=None):
    """Read requirement from task column or fallback to task.requirements JSON."""
    val = getattr(task, key, None)
    if val is not None:
        return val
    return (task.requirements or {}).get(key, default)


def _latest_classification(session: Session, event_id: str) -> Classification | None:
    return (
        session.query(Classification)
        .filter(Classification.event_id == event_id)
        .order_by(Classification.created_at.desc())
        .first()
    )


def _duration_bucket(minutes: int) -> str:
    if minutes < 15:
        return "short"
    if minutes < 30:
        return "medium"
    if minutes < 60:
        return "long"
    if minutes < 120:
        return "endurance"
    return "ultra"


def _event_signature(event: Event) -> str:
    payload = {
        "source": event.source,
        "event_type": event.event_type,
        "format_type": event.format_type,
        "schedule_type": event.schedule_type,
        "duration_bucket": _duration_bucket(event.duration_minutes),
        "class_count": event.class_count,
        "car_class_list": sorted([value for value in (event.car_class_list or []) if value]),
        "damage_model": event.damage_model,
        "penalties": event.penalties,
        "fuel_usage": event.fuel_usage,
        "tire_wear": event.tire_wear,
        "weather": event.weather,
        "night": bool(event.night),
        "team_event": bool(event.team_event),
        "official_event": bool(event.official_event),
        "track_type": event.track_type,
        "surface_type": event.surface_type,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload_bytes).hexdigest()


def _completion_time(completion: TaskCompletion) -> datetime:
    value = completion.completed_at or completion.created_at
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _participation_duration_minutes(participation: Participation) -> float | None:
    if not participation.started_at or not participation.finished_at:
        return None
    delta = participation.finished_at - participation.started_at
    return abs(delta.total_seconds()) / 60.0


def _meets_requirements(
    task: TaskDefinition,
    participation: Participation,
    event: Event,
    classification: Classification | None,
) -> bool:
    part_status = getattr(participation, "status", None)
    part_status = part_status.value if hasattr(part_status, "value") else (str(part_status) if part_status else "")

    min_event_tier = _get_req(task, "min_event_tier") or task.min_event_tier
    if min_event_tier:
        tier = classification.event_tier if classification else "E2"
        if TIER_RANK.get(tier, 0) < TIER_RANK.get(min_event_tier, 0):
            return False

    max_event_tier = _get_req(task, "max_event_tier")
    if max_event_tier:
        tier = classification.event_tier if classification else "E2"
        if TIER_RANK.get(tier, 0) > TIER_RANK.get(max_event_tier, 0):
            return False

    min_duration = _get_req(task, "min_duration_minutes")
    if min_duration is not None:
        actual_minutes = _participation_duration_minutes(participation)
        duration_value = actual_minutes if actual_minutes is not None else event.duration_minutes
        if duration_value < float(min_duration):
            return False

    max_incidents = _get_req(task, "max_incidents")
    if max_incidents is not None and participation.incidents_count > int(max_incidents):
        return False

    max_penalties = _get_req(task, "max_penalties")
    if max_penalties is not None and participation.penalties_count > int(max_penalties):
        return False

    if _get_req(task, "require_night") and not event.night:
        return False

    if _get_req(task, "require_dynamic_weather") and event.weather != "dynamic":
        return False

    if _get_req(task, "require_team_event") and not event.team_event:
        return False

    if _get_req(task, "require_clean_finish"):
        if part_status != "finished":
            return False
        if participation.incidents_count > 0 or participation.penalties_count > 0:
            return False

    if part_status != "finished" and not _get_req(task, "allow_non_finish"):
        return False

    max_position_overall = _get_req(task, "max_position_overall")
    if max_position_overall is not None and participation.position_overall is not None:
        if participation.position_overall > int(max_position_overall):
            return False

    min_position_overall = _get_req(task, "min_position_overall")
    if min_position_overall is not None and participation.position_overall is not None:
        if participation.position_overall < int(min_position_overall):
            return False

    min_laps_completed = _get_req(task, "min_laps_completed")
    if min_laps_completed is not None and participation.laps_completed < int(min_laps_completed):
        return False

    return True


def _meets_requirements_reasons(
    task: TaskDefinition,
    participation: Participation,
    event: Event,
    classification: Classification | None,
) -> tuple[bool, list[str]]:
    """Same checks as _meets_requirements but returns (ok, list of failure reasons)."""
    reasons: list[str] = []
    part_status = getattr(participation, "status", None)
    part_status = part_status.value if hasattr(part_status, "value") else (str(part_status) if part_status else "")

    min_event_tier = _get_req(task, "min_event_tier") or task.min_event_tier
    if min_event_tier:
        tier = classification.event_tier if classification else "E2"
        if TIER_RANK.get(tier, 0) < TIER_RANK.get(min_event_tier, 0):
            reasons.append(f"Event tier must be at least {min_event_tier}, got {tier}")

    max_event_tier = _get_req(task, "max_event_tier")
    if max_event_tier:
        tier = classification.event_tier if classification else "E2"
        if TIER_RANK.get(tier, 0) > TIER_RANK.get(max_event_tier, 0):
            reasons.append(f"Event tier must be at most {max_event_tier}, got {tier}")

    min_duration = _get_req(task, "min_duration_minutes")
    if min_duration is not None:
        actual_minutes = _participation_duration_minutes(participation)
        duration_value = actual_minutes if actual_minutes is not None else event.duration_minutes
        if duration_value < float(min_duration):
            mins_str = f"{actual_minutes:.1f} min" if actual_minutes is not None else "no data"
            reasons.append(f"Session duration must be at least {min_duration} min, actual: {mins_str}")

    max_incidents = _get_req(task, "max_incidents")
    if max_incidents is not None and participation.incidents_count > int(max_incidents):
        reasons.append(f"Incidents must be at most {max_incidents}, got {participation.incidents_count}")

    max_penalties = _get_req(task, "max_penalties")
    if max_penalties is not None and participation.penalties_count > int(max_penalties):
        reasons.append(f"Penalties must be at most {max_penalties}, got {participation.penalties_count}")

    if _get_req(task, "require_night") and not event.night:
        reasons.append("Night session required")

    if _get_req(task, "require_dynamic_weather") and event.weather != "dynamic":
        reasons.append("Dynamic weather required")

    if _get_req(task, "require_team_event") and not event.team_event:
        reasons.append("Team event required")

    if _get_req(task, "require_clean_finish"):
        if part_status != "finished":
            reasons.append("Clean finish (finished) required")
        elif participation.incidents_count > 0 or participation.penalties_count > 0:
            reasons.append("Clean finish required (no incidents or penalties)")

    if part_status != "finished" and not _get_req(task, "allow_non_finish"):
        reasons.append("Participation finish (finished) required")

    max_position_overall = _get_req(task, "max_position_overall")
    if max_position_overall is not None and participation.position_overall is not None and participation.position_overall > int(max_position_overall):
        reasons.append(f"Position overall must be no worse than {max_position_overall}, got {participation.position_overall}")

    min_position_overall = _get_req(task, "min_position_overall")
    if min_position_overall is not None and participation.position_overall is not None and participation.position_overall < int(min_position_overall):
        reasons.append(f"Position overall must be no better than {min_position_overall}, got {participation.position_overall}")

    min_laps_completed = _get_req(task, "min_laps_completed")
    if min_laps_completed is not None and participation.laps_completed < int(min_laps_completed):
        reasons.append(f"Laps completed must be at least {min_laps_completed}, got {participation.laps_completed}")

    return (len(reasons) == 0, reasons)


def assign_tasks_on_registration(
    session: Session, driver_id: str, participation_id: str
) -> list[TaskCompletion]:
    """When driver registers for an event that has task_codes, assign matching tasks to in progress (pending + participation_id)."""
    participation = (
        session.query(Participation)
        .filter(Participation.id == participation_id, Participation.driver_id == driver_id)
        .first()
    )
    if not participation:
        return []
    event = session.query(Event).filter(Event.id == participation.event_id).first()
    if not event or not getattr(event, "task_codes", None) or not isinstance(event.task_codes, list):
        return []
    task_codes = [c for c in event.task_codes if c and isinstance(c, str)]
    if not task_codes:
        return []
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return []
    driver_tier = (driver.tier or "E0").strip()
    part_discipline = (
        participation.discipline.value if hasattr(participation.discipline, "value") else str(participation.discipline)
    )
    created: list[TaskCompletion] = []
    for code in task_codes:
        task = (
            session.query(TaskDefinition)
            .filter(
                TaskDefinition.code == code.strip(),
                TaskDefinition.active.is_(True),
                TaskDefinition.discipline == part_discipline,
            )
            .first()
        )
        if not task:
            continue
        task_min_tier = (task.min_event_tier or "E0").strip()
        if driver_tier not in TIER_RANK or task_min_tier not in TIER_RANK:
            continue
        if TIER_RANK[driver_tier] < TIER_RANK[task_min_tier]:
            continue
        already_completed = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.status == "completed",
            )
            .first()
        )
        if already_completed:
            continue
        already_pending = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.participation_id == participation_id,
                TaskCompletion.status == "pending",
            )
            .first()
        )
        if already_pending:
            continue
        completion = TaskCompletion(
            driver_id=driver_id,
            task_id=task.id,
            participation_id=participation_id,
            status="pending",
        )
        session.add(completion)
        created.append(completion)
    if created:
        session.commit()
        for c in created:
            session.refresh(c)
    return created


def ensure_task_completion(
    session: Session, driver_id: str, task_code: str, notes: str | None = None
) -> TaskCompletion | None:
    task = session.query(TaskDefinition).filter(TaskDefinition.code == task_code).first()
    if not task:
        return None
    existing = (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task.id,
            TaskCompletion.status == "completed",
        )
        .first()
    )
    if existing:
        return existing
    completion = TaskCompletion(
        driver_id=driver_id,
        task_id=task.id,
        status="completed",
        notes=notes,
        completed_at=datetime.now(timezone.utc),
    )
    session.add(completion)
    return completion


def _recent_completions(
    session: Session, driver_id: str, task_id: str, cutoff: datetime
) -> list[TaskCompletion]:
    return (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.status == "completed",
            TaskCompletion.created_at >= cutoff,
        )
        .order_by(TaskCompletion.created_at.desc())
        .all()
    )


def _count_total_completions(session: Session, driver_id: str, task_id: str) -> int:
    return (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.status == "completed",
        )
        .count()
    )


def _latest_completion(session: Session, driver_id: str, task_id: str) -> TaskCompletion | None:
    return (
        session.query(TaskCompletion)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.task_id == task_id,
            TaskCompletion.status == "completed",
        )
        .order_by(TaskCompletion.created_at.desc())
        .first()
    )


def evaluate_tasks(session: Session, driver_id: str, participation_id: str) -> list[TaskCompletion]:
    participation = (
        session.query(Participation)
        .options(
            selectinload(Participation.incidents).selectinload(Incident.penalties),
        )
        .filter(Participation.id == participation_id, Participation.driver_id == driver_id)
        .first()
    )
    if not participation:
        return []

    event = session.query(Event).filter(Event.id == participation.event_id).first()
    if not event:
        return []

    classification = _latest_classification(session, participation.event_id)

    tasks = (
        session.query(TaskDefinition)
        .filter(TaskDefinition.active.is_(True), TaskDefinition.discipline == participation.discipline)
        .all()
    )
    # Only evaluate tasks that are assigned to THIS event (event.task_codes)
    event_task_codes = list(event.task_codes) if getattr(event, "task_codes", None) else []
    if event_task_codes:
        tasks = [t for t in tasks if t.code in event_task_codes]

    completions: list[TaskCompletion] = []

    now = datetime.now(timezone.utc)
    current_signature = _event_signature(event)

    for task in tasks:
        if not getattr(task, "event_related", True):
            continue
        repeatable = bool(_get_req(task, "repeatable", False))

        total_completed = _count_total_completions(session, driver_id, task.id)
        if not repeatable and total_completed > 0:
            continue

        meets, failure_reasons = _meets_requirements_reasons(task, participation, event, classification)
        existing_pending = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.participation_id == participation_id,
                TaskCompletion.status == "pending",
            )
            .first()
        )
        if not meets and existing_pending:
            existing_pending.status = "in_progress"
            existing_pending.evaluation_failed_at = now
            existing_pending.evaluation_failure_reasons = failure_reasons
            continue
        if not meets:
            continue

        max_completions = _get_req(task, "max_completions")
        if max_completions is not None and total_completed >= int(max_completions):
            continue

        cooldown_hours = _get_req(task, "cooldown_hours")
        if cooldown_hours is None and repeatable:
            cooldown_hours = 24
        if cooldown_hours:
            latest = _latest_completion(session, driver_id, task.id)
            if latest and now - _completion_time(latest) < timedelta(hours=float(cooldown_hours)):
                continue

        diversity_window_days = int(_get_req(task, "diversity_window_days") or 30)
        cutoff = now - timedelta(days=diversity_window_days)
        recent = _recent_completions(session, driver_id, task.id, cutoff)

        same_event_count = 0
        if participation.event_id:
            same_event_count = (
                session.query(TaskCompletion)
                .join(Participation, TaskCompletion.participation_id == Participation.id)
                .filter(
                    TaskCompletion.driver_id == driver_id,
                    TaskCompletion.task_id == task.id,
                    TaskCompletion.status == "completed",
                    Participation.event_id == participation.event_id,
                    TaskCompletion.created_at >= cutoff,
                )
                .count()
            )

        same_signature_count = 0
        if current_signature:
            same_signature_count = (
                session.query(TaskCompletion)
                .filter(
                    TaskCompletion.driver_id == driver_id,
                    TaskCompletion.task_id == task.id,
                    TaskCompletion.status == "completed",
                    TaskCompletion.event_signature == current_signature,
                    TaskCompletion.created_at >= cutoff,
                )
                .count()
            )

            if same_signature_count == 0:
                for completion in recent:
                    if completion.event_signature:
                        continue
                    if not completion.participation_id:
                        continue
                    prior_participation = (
                        session.query(Participation)
                        .filter(Participation.id == completion.participation_id)
                        .first()
                    )
                    if not prior_participation:
                        continue
                    prior_event = (
                        session.query(Event)
                        .filter(Event.id == prior_participation.event_id)
                        .first()
                    )
                    if not prior_event:
                        continue
                    if _event_signature(prior_event) == current_signature:
                        same_signature_count += 1

        max_same_event_count = _get_req(task, "max_same_event_count")
        if max_same_event_count is None and repeatable:
            max_same_event_count = 1
        if max_same_event_count is not None and same_event_count >= int(max_same_event_count):
            continue

        require_event_diversity = _get_req(task, "require_event_diversity")
        if require_event_diversity is None:
            require_event_diversity = repeatable
        if require_event_diversity and same_signature_count > 0:
            continue

        max_same_signature_count = _get_req(task, "max_same_signature_count")
        if max_same_signature_count is not None and same_signature_count >= int(max_same_signature_count):
            continue

        signature_cooldown_hours = _get_req(task, "signature_cooldown_hours")
        if signature_cooldown_hours and same_signature_count:
            last_same_signature = None
            for completion in recent:
                signature = completion.event_signature
                if not signature and completion.participation_id:
                    prior_participation = (
                        session.query(Participation)
                        .filter(Participation.id == completion.participation_id)
                        .first()
                    )
                    if prior_participation:
                        prior_event = (
                            session.query(Event)
                            .filter(Event.id == prior_participation.event_id)
                            .first()
                        )
                        if prior_event:
                            signature = _event_signature(prior_event)
                if signature != current_signature:
                    continue
                timestamp = _completion_time(completion)
                if not last_same_signature or timestamp > last_same_signature:
                    last_same_signature = timestamp
            if last_same_signature and now - last_same_signature < timedelta(
                hours=float(signature_cooldown_hours)
            ):
                continue

        multiplier = 1.0
        if _get_req(task, "diminishing_returns") or repeatable:
            step = float(_get_req(task, "diminishing_step") or 0.2)
            floor = float(_get_req(task, "diminishing_floor") or 0.4)
            multiplier = max(floor, 1.0 - step * len(recent))

        existing_pending = (
            session.query(TaskCompletion)
            .filter(
                TaskCompletion.driver_id == driver_id,
                TaskCompletion.task_id == task.id,
                TaskCompletion.participation_id == participation_id,
                TaskCompletion.status.in_(["pending", "in_progress"]),
            )
            .first()
        )
        if existing_pending:
            existing_pending.status = "completed"
            existing_pending.completed_at = now
            existing_pending.event_signature = current_signature
            existing_pending.score_multiplier = multiplier
            existing_pending.evaluation_failed_at = None
            existing_pending.evaluation_failure_reasons = None
            completions.append(existing_pending)
        else:
            completion = TaskCompletion(
                driver_id=driver_id,
                task_id=task.id,
                participation_id=participation_id,
                status="completed",
                completed_at=now,
                event_signature=current_signature,
                score_multiplier=multiplier,
            )
            session.add(completion)
            completions.append(completion)

    session.commit()
    for completion in completions:
        session.refresh(completion)

    return completions


def assign_participation_id_for_completed_participation(
    session: Session, driver_id: str, participation_id: str
) -> int:
    """When a participation is completed, link existing task completions (without participation_id)
    that are satisfied by this participation. Returns the number of completions updated.
    Call after evaluate_tasks so new completions are created first; this backfills manual ones.
    """
    participation = (
        session.query(Participation)
        .options(
            selectinload(Participation.incidents).selectinload(Incident.penalties),
        )
        .filter(Participation.id == participation_id, Participation.driver_id == driver_id)
        .first()
    )
    if not participation or participation.participation_state != ParticipationState.completed:
        return 0
    event = session.query(Event).filter(Event.id == participation.event_id).first()
    if not event:
        return 0
    classification = _latest_classification(session, participation.event_id)
    part_discipline = (
        participation.discipline.value if hasattr(participation.discipline, "value") else str(participation.discipline)
    )
    event_task_codes = list(event.task_codes) if getattr(event, "task_codes", None) else []
    unlinked = (
        session.query(TaskCompletion, TaskDefinition)
        .join(TaskDefinition, TaskCompletion.task_id == TaskDefinition.id)
        .filter(
            TaskCompletion.driver_id == driver_id,
            TaskCompletion.status == "completed",
            TaskCompletion.participation_id.is_(None),
            TaskDefinition.discipline == part_discipline,
        )
        .all()
    )
    updated = 0
    for completion, task in unlinked:
        if event_task_codes and task.code not in event_task_codes:
            continue
        if _meets_requirements(task, participation, event, classification):
            completion.participation_id = participation_id
            updated += 1
    if updated:
        session.commit()
    return updated
