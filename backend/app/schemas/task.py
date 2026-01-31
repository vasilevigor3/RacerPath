from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, Field, validator

DISCIPLINE_ALIASES = {"offroad": "karting"}


class TaskDefinitionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    discipline: Literal["formula", "gt", "rally", "karting", "historic", "offroad"]
    description: str = Field(min_length=2, max_length=500)
    requirements: Dict[str, str | int | float | bool] = Field(default_factory=dict)
    min_event_tier: str | None = None
    active: bool = True

    @validator("discipline", pre=True)
    def normalize_discipline(cls, value: object) -> object:
        if isinstance(value, str):
            return DISCIPLINE_ALIASES.get(value, value)
        return value


class TaskDefinitionRead(TaskDefinitionCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCompletionCreate(BaseModel):
    driver_id: str
    task_id: str
    participation_id: str | None = None
    status: Literal["completed", "failed", "pending"] = "completed"
    notes: str | None = Field(default=None, max_length=240)
    completed_at: datetime | None = None
    score_multiplier: float = 1.0


class TaskCompletionRead(TaskCompletionCreate):
    id: str
    event_signature: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
