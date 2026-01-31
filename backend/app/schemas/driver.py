from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class DriverCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    primary_discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    sim_games: List[str] = Field(default_factory=list)


class DriverRead(DriverCreate):
    id: str
    user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
