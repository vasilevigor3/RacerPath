from datetime import datetime
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, field_validator

# If you are here, fix this: delete DISCIPLINE_ALIASES, and use kartingn instead of offroad.check corresponding dependencies.
DISCIPLINE_ALIASES = {"offroad": "karting"}

TASK_SCOPE = Literal["global", "per_participation", "rolling_window", "periodic"]
TASK_PERIOD = Literal["daily", "weekly", "monthly"]


class TaskDefinitionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    discipline: Literal["formula", "gt", "rally", "karting", "historic", "offroad"]
    description: str = Field(min_length=2, max_length=500)
    requirements: Dict[str, str | int | float | bool] = Field(default_factory=dict)
    min_event_tier: str | None = None
    active: bool = True
    event_related: bool = True
    scope: TASK_SCOPE = "per_participation"
    cooldown_days: int | None = Field(default=None, ge=0, le=365)
    period: TASK_PERIOD | None = None
    window_size: int | None = Field(default=None, ge=1, le=1000)
    window_unit: Literal["participations", "days"] | None = None

    @field_validator("discipline", mode="before")
    @classmethod
    def normalize_discipline(cls, value: object) -> object:
        if isinstance(value, str):
            return DISCIPLINE_ALIASES.get(value, value)
        return value


class TaskDefinitionRead(TaskDefinitionCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskDefinitionUpdate(BaseModel):
    code: str | None = Field(None, min_length=2, max_length=40)
    name: str | None = Field(None, min_length=2, max_length=120)
    discipline: Literal["formula", "gt", "rally", "karting", "historic", "offroad"] | None = None
    description: str | None = Field(None, min_length=2, max_length=500)
    requirements: Dict[str, str | int | float | bool] | None = None
    min_event_tier: str | None = None
    active: bool | None = None
    event_related: bool | None = None
    scope: TASK_SCOPE | None = None
    cooldown_days: int | None = Field(None, ge=0, le=365)
    period: TASK_PERIOD | None = None
    window_size: int | None = Field(None, ge=1, le=1000)
    window_unit: Literal["participations", "days"] | None = None


class TaskCompletionCreate(BaseModel):
    driver_id: str
    task_id: str
    participation_id: str | None = None
    status: Literal["completed", "failed", "pending"] = "completed"
    notes: str | None = Field(default=None, max_length=240)
    completed_at: datetime | None = None
    score_multiplier: float = 1.0
    period_key: str | None = Field(default=None, max_length=16)
    achieved_by: List[str] | Dict[str, Any] | None = None


class TaskCompletionRead(TaskCompletionCreate):
    id: str
    event_signature: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCompleteRequest(BaseModel):
    """Request for POST /api/dev/tasks/complete (by task_code)."""
    driver_id: str
    task_code: str
    participation_id: str | None = None
    period_key: str | None = Field(default=None, max_length=16)
    achieved_by: List[str] | None = None
