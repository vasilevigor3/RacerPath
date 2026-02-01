from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

DriverTier = Literal["E0", "E1", "E2", "E3", "E4", "E5"]


class DriverCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    primary_discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    sim_games: List[str] = Field(default_factory=list)
    user_id: str | None = Field(None, description="Required when creating via admin; set from auth for POST /me")


class DriverRead(DriverCreate):
    id: str
    user_id: str
    tier: DriverTier = "E0"
    created_at: datetime

    model_config = {"from_attributes": True}
