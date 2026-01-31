from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class RealWorldFormatCreate(BaseModel):
    discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=500)
    min_crs: float = Field(ge=0, le=100)
    required_license_code: str | None = None
    required_task_codes: List[str] = Field(default_factory=list)
    required_event_tiers: List[str] = Field(default_factory=list)
    active: bool = True


class RealWorldFormatRead(RealWorldFormatCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RealWorldReadinessRead(BaseModel):
    id: str
    driver_id: str
    discipline: str
    status: str
    summary: str
    formats: list
    created_at: datetime

    model_config = {"from_attributes": True}
