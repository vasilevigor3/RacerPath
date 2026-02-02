from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.driver import RigOptions
from app.models.enums.event_enums import (EventStatus,
    ScheduleType, EventType, FormatType,
    DamageModel, RulesToggle, WeatherType,
    StewardingType, LicenseRequirement,
)

EVENT_TIERS = ("E0", "E1", "E2", "E3", "E4", "E5")
EventTier = Literal["E0", "E1", "E2", "E3", "E4", "E5"]

SPECIAL_EVENT_VALUES = ("race_of_day", "race_of_week", "race_of_month", "race_of_year")
SpecialEvent = Literal["race_of_day", "race_of_week", "race_of_month", "race_of_year"]

SESSION_TYPE_VALUES = ("race", "training")
SessionType = Literal["race", "training"]


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    source: str
    game: Optional[str] = Field(default=None, max_length=60)
    country: Optional[str] = Field(default=None, max_length=80)
    city: Optional[str] = Field(default=None, max_length=80)
    start_time_utc: Optional[datetime] = None
    finished_time_utc: Optional[datetime] = None
    event_tier: Optional[EventTier] = Field(default=None, description="Override classification tier (E0–E5)")
    special_event: Optional[SpecialEvent] = None

    event_status: EventStatus = EventStatus.scheduled

    session_type: SessionType = "race"
    schedule_type: ScheduleType = ScheduleType.weekly
    event_type: EventType = EventType.circuit
    format_type: FormatType = FormatType.sprint

    session_list: List[str] = Field(default_factory=list)
    team_size_min: int = Field(default=1, ge=1, le=8)
    team_size_max: int = Field(default=1, ge=1, le=8)

    rolling_start: bool = False
    pit_rules: Dict[str, bool | int | str] = Field(default_factory=dict)

    duration_minutes: int = Field(default=0, ge=0, le=1440)
    grid_size_expected: int = Field(default=0, ge=0, le=100)

    class_count: int = Field(default=1, ge=1, le=6)
    car_class_list: List[str] = Field(default_factory=list)

    damage_model: DamageModel = DamageModel.off
    penalties: RulesToggle = RulesToggle.off
    fuel_usage: RulesToggle = RulesToggle.off
    tire_wear: RulesToggle = RulesToggle.off

    weather: WeatherType = WeatherType.fixed
    night: bool = False
    time_acceleration: bool = False

    surface_type: Optional[str] = None
    track_type: Optional[str] = None

    stewarding: StewardingType = StewardingType.none
    team_event: bool = False
    license_requirement: LicenseRequirement = LicenseRequirement.none
    official_event: bool = False
    assists_allowed: bool = False
    rig_options: Optional[RigOptions] = Field(default=None, description="Required/minimum rig for event")
    task_codes: Optional[List[str]] = Field(default=None, description="Task codes that can be completed at this event; empty/None = normal race only")

    @model_validator(mode="after")
    def validate_team_sizes(self):
        if self.team_size_min > self.team_size_max:
            raise ValueError("team_size_min cannot be greater than team_size_max")
        return self


class EventUpdate(BaseModel):
    """Partial update for admin; all fields optional. event_tier updates Classification."""
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    source: Optional[str] = Field(default=None, max_length=40)
    game: Optional[str] = Field(default=None, max_length=60)
    country: Optional[str] = Field(default=None, max_length=80)
    city: Optional[str] = Field(default=None, max_length=80)
    start_time_utc: Optional[datetime] = None
    finished_time_utc: Optional[datetime] = None
    event_tier: Optional[EventTier] = None
    special_event: Optional[SpecialEvent] = None

    session_type: Optional[SessionType] = None
    schedule_type: Optional[ScheduleType] = None
    event_type: Optional[EventType] = None
    format_type: Optional[FormatType] = None

    session_list: Optional[List[str]] = None
    team_size_min: Optional[int] = Field(default=None, ge=1, le=8)
    team_size_max: Optional[int] = Field(default=None, ge=1, le=8)

    rolling_start: Optional[bool] = None
    pit_rules: Optional[Dict[str, bool | int | str]] = None

    duration_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
    grid_size_expected: Optional[int] = Field(default=None, ge=0, le=100)

    class_count: Optional[int] = Field(default=None, ge=1, le=6)
    car_class_list: Optional[List[str]] = None

    damage_model: Optional[DamageModel] = None
    penalties: Optional[RulesToggle] = None
    fuel_usage: Optional[RulesToggle] = None
    tire_wear: Optional[RulesToggle] = None

    weather: Optional[WeatherType] = None
    night: Optional[bool] = None
    time_acceleration: Optional[bool] = None

    surface_type: Optional[str] = None
    track_type: Optional[str] = None

    stewarding: Optional[StewardingType] = None
    team_event: Optional[bool] = None
    license_requirement: Optional[LicenseRequirement] = None
    official_event: Optional[bool] = None
    assists_allowed: Optional[bool] = None
    rig_options: Optional[RigOptions] = None
    task_codes: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_team_sizes(self):
        if self.team_size_min is not None and self.team_size_max is not None and self.team_size_min > self.team_size_max:
            raise ValueError("team_size_min cannot be greater than team_size_max")
        return self


class EventRead(EventCreate):
    id: str
    created_at: datetime
    difficulty_score: Optional[float] = Field(default=None, description="From latest classification")
    model_config = {"from_attributes": True}
