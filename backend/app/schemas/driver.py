from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

DriverTier = Literal["E0", "E1", "E2", "E3", "E4", "E5"]

# Rig options: wheel (legacy belt/gear vs force-feedback Nm), pedals class, manual with clutch
WheelType = Literal["legacy", "force_feedback_nm"]
PedalsClass = Literal["basic", "spring", "premium"]


class RigOptions(BaseModel):
    """Driver rig or event required rig. wheel_type: legacy (belt/gear) vs force_feedback_nm; pedals_class: basic/spring/premium; manual_with_clutch."""
    wheel_type: WheelType | None = Field(default=None, description="legacy = belt/gear, force_feedback_nm = direct drive with Nm")
    pedals_class: PedalsClass | None = Field(default=None, description="basic / spring / premium")
    manual_with_clutch: bool | None = Field(default=None, description="Manual gearbox with clutch")


class DriverCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    primary_discipline: Literal["formula", "gt", "rally", "karting", "historic"]
    sim_games: List[str] = Field(default_factory=list)
    user_id: str | None = Field(None, description="Required when creating via admin; set from auth for POST /me")
    rig_options: RigOptions | None = Field(default=None)


class DriverUpdate(BaseModel):
    """Partial update for driver (e.g. rig_options from profile)."""
    name: str | None = Field(default=None, min_length=2, max_length=120)
    primary_discipline: Literal["formula", "gt", "rally", "karting", "historic"] | None = None
    sim_games: List[str] | None = None
    rig_options: RigOptions | None = None


class DriverRead(DriverCreate):
    id: str
    user_id: str
    tier: DriverTier = "E0"
    created_at: datetime

    model_config = {"from_attributes": True}
