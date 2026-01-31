from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums.event_enums import (EventStatus,
    ScheduleType, EventType, FormatType,
    DamageModel, RulesToggle, WeatherType,
    StewardingType, LicenseRequirement,
)


class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    source: str
    game: Optional[str] = Field(default=None, max_length=60)
    country: Optional[str] = Field(default=None, max_length=80)
    city: Optional[str] = Field(default=None, max_length=80)
    start_time_utc: Optional[datetime] = None

    event_status: EventStatus = EventStatus.scheduled

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

    @model_validator(mode="after")
    def validate_team_sizes(self):
        if self.team_size_min > self.team_size_max:
            raise ValueError("team_size_min cannot be greater than team_size_max")
        return self


class EventRead(EventCreate):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}
