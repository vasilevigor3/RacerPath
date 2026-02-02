"""Penalty schemas: create/read for penalty records."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PenaltyTypeEnum(str, Enum):
    time_penalty = "time_penalty"
    drive_through = "drive_through"
    stop_and_go = "stop_and_go"
    dsq = "dsq"


class PenaltyCreate(BaseModel):
    participation_id: str
    penalty_type: PenaltyTypeEnum
    time_seconds: int | None = Field(default=None, ge=0)
    lap: int | None = Field(default=None, ge=0)
    description: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def time_required_for_time_penalty(self):
        if self.penalty_type == PenaltyTypeEnum.time_penalty and (self.time_seconds is None or self.time_seconds <= 0):
            raise ValueError("time_penalty requires time_seconds > 0")
        return self


class PenaltyRead(PenaltyCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
