from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class UserProfileUpsert(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=80)
    age: int | None = Field(default=None, ge=0, le=120)
    experience_years: int | None = Field(default=None, ge=0, le=60)
    primary_discipline: Literal["formula", "gt", "rally", "karting", "historic"] | None = None
    sim_platforms: List[str] = Field(default_factory=list)
    rig: str | None = Field(default=None, max_length=120)
    goals: str | None = Field(default=None, max_length=240)


class UserProfileRead(UserProfileUpsert):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime | None
    profile_completion_percent: int
    next_tier_progress_percent: int = Field(default=0, ge=0, le=100)
    missing_fields: List[str]
    level: str

    model_config = {"from_attributes": True}
