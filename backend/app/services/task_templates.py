from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from app.models.task_definition import TaskDefinition

TEMPLATES = [
    {
        "code": "GT_CLEAN_SPRINT",
        "name": "Clean sprint finish",
        "discipline": "gt",
        "description": "Finish a sprint race with zero incidents and penalties.",
        "requirements": {
            "min_duration_minutes": 20,
            "require_clean_finish": True,
            "repeatable": True,
            "cooldown_hours": 48,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.4,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "GT_ENDURANCE_NO_DNF",
        "name": "Endurance completion",
        "discipline": "gt",
        "description": "Complete an endurance event without DNF.",
        "requirements": {
            "min_duration_minutes": 60,
            "max_incidents": 2,
            "max_penalties": 1,
            "repeatable": True,
            "cooldown_hours": 72,
            "require_event_diversity": True,
            "diversity_window_days": 45,
            "diminishing_returns": True,
            "diminishing_step": 0.15,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "GT_CLEAN_ENDURANCE",
        "name": "Clean endurance finish",
        "discipline": "gt",
        "description": "Finish a 60+ minute race with zero incidents or penalties.",
        "requirements": {
            "min_duration_minutes": 60,
            "require_clean_finish": True,
            "repeatable": True,
            "cooldown_hours": 72,
            "require_event_diversity": True,
            "diversity_window_days": 60,
            "diminishing_returns": True,
            "diminishing_step": 0.15,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "GT_NIGHT_RAIN",
        "name": "Night + rain experience",
        "discipline": "gt",
        "description": "Finish a night race with dynamic weather.",
        "requirements": {"require_night": True, "require_dynamic_weather": True},
        "min_event_tier": "E2",
    },
    {
        "code": "F_CLEAN_QUALI",
        "name": "Clean qualifying session",
        "discipline": "formula",
        "description": "Complete a race with zero incidents or penalties.",
        "requirements": {
            "require_clean_finish": True,
            "repeatable": True,
            "cooldown_hours": 36,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.25,
            "diminishing_floor": 0.4,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "F_HIGH_TIER",
        "name": "High-tier formula event",
        "discipline": "formula",
        "description": "Finish a high-tier Formula event.",
        "requirements": {},
        "min_event_tier": "E3",
    },
    {
        "code": "F_LONG_RACE",
        "name": "Long-form race discipline",
        "discipline": "formula",
        "description": "Complete a 45+ minute race without DNF.",
        "requirements": {
            "min_duration_minutes": 45,
            "max_penalties": 1,
            "repeatable": True,
            "cooldown_hours": 48,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "RALLY_NO_DNF",
        "name": "Rally finish rate",
        "discipline": "rally",
        "description": "Complete a rally stage without DNF and with minimal incidents.",
        "requirements": {
            "max_incidents": 1,
            "max_penalties": 0,
            "repeatable": True,
            "cooldown_hours": 24,
            "require_event_diversity": True,
            "diversity_window_days": 21,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "RALLY_NIGHT",
        "name": "Night stage experience",
        "discipline": "rally",
        "description": "Finish a night rally stage.",
        "requirements": {"require_night": True},
        "min_event_tier": "E2",
    },
    {
        "code": "RALLY_DYNAMIC",
        "name": "Dynamic conditions",
        "discipline": "rally",
        "description": "Finish a rally stage with dynamic weather.",
        "requirements": {"require_dynamic_weather": True},
        "min_event_tier": "E2",
    },
    {
        "code": "KARTING_TEAM",
        "name": "Team karting event",
        "discipline": "karting",
        "description": "Complete a team karting event.",
        "requirements": {
            "require_team_event": True,
            "repeatable": True,
            "cooldown_hours": 48,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "KARTING_CLEAN",
        "name": "Clean karting race",
        "discipline": "karting",
        "description": "Finish a karting race with minimal incidents.",
        "requirements": {
            "max_incidents": 1,
            "max_penalties": 0,
            "repeatable": True,
            "cooldown_hours": 36,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
    {
        "code": "HISTORIC_CLEAN",
        "name": "Historic discipline",
        "discipline": "historic",
        "description": "Finish a historic race without penalties.",
        "requirements": {
            "max_penalties": 0,
            "repeatable": True,
            "cooldown_hours": 36,
            "require_event_diversity": True,
            "diversity_window_days": 30,
            "diminishing_returns": True,
            "diminishing_step": 0.2,
            "diminishing_floor": 0.5,
            "max_same_event_count": 1,
        },
        "min_event_tier": "E2",
    },
]

DISCIPLINES = ["gt", "formula", "rally", "karting", "historic"]
ONBOARDING_TEMPLATES = []
for discipline in DISCIPLINES:
    suffix = discipline.upper()
    ONBOARDING_TEMPLATES.extend(
        [
            {
                "code": f"ONBOARD_DRIVER_{suffix}",
                "name": "Create driver profile",
                "discipline": discipline,
                "description": "Create your driver profile to start tracking progress.",
                "requirements": {"manual": True},
                "min_event_tier": None,
            },
            {
                "code": f"ONBOARD_GAMES_{suffix}",
                "name": "Select sim games",
                "discipline": discipline,
                "description": "Add the sim games you race to unlock event matching.",
                "requirements": {"manual": True},
                "min_event_tier": None,
            },
            {
                "code": f"ONBOARD_PROFILE_{suffix}",
                "name": "Complete core profile",
                "discipline": discipline,
                "description": "Fill all core profile fields to unlock readiness tracking.",
                "requirements": {"manual": True},
                "min_event_tier": None,
            },
        ]
    )

TEMPLATES.extend(ONBOARDING_TEMPLATES)


def list_templates() -> List[dict]:
    return TEMPLATES


REQUIREMENT_COLUMN_KEYS = (
    "min_duration_minutes", "max_incidents", "max_penalties",
    "require_night", "require_dynamic_weather", "require_team_event",
    "require_clean_finish", "allow_non_finish",
    "max_position_overall", "min_position_overall", "min_laps_completed",
    "repeatable", "max_completions", "cooldown_hours", "diversity_window_days",
    "max_same_event_count", "require_event_diversity", "max_same_signature_count",
    "signature_cooldown_hours", "diminishing_returns", "diminishing_step", "diminishing_floor",
)


def _apply_requirement_columns(task: TaskDefinition, req: dict) -> None:
    for key in REQUIREMENT_COLUMN_KEYS:
        if key in req:
            setattr(task, key, req[key])


def seed_templates(session: Session) -> List[TaskDefinition]:
    existing_by_code = {
        task.code: task for task in session.query(TaskDefinition).all()
    }
    created: List[TaskDefinition] = []
    for template in TEMPLATES:
        req = template.get("requirements") or {}
        existing = existing_by_code.get(template["code"])
        if existing:
            existing.name = template["name"]
            existing.description = template["description"]
            existing.requirements = template["requirements"]
            existing.min_event_tier = template.get("min_event_tier")
            existing.max_event_tier = req.get("max_event_tier")
            existing.active = True
            _apply_requirement_columns(existing, req)
            continue
        task = TaskDefinition(**template)
        _apply_requirement_columns(task, req)
        session.add(task)
        created.append(task)
    session.commit()
    for task in created:
        session.refresh(task)
    return created
