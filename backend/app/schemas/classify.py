from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class ClassificationRequest(BaseModel):
    discipline: Literal["formula", "gt", "rally", "karting", "historic"] = "gt"
    format: Literal["sprint", "endurance", "series", "time_trial"] = "sprint"
    duration: int = 0
    grid: int = 0
    classes: int = 1
    schedule: Literal["daily", "weekly", "seasonal", "special"] = "weekly"
    damage: Literal["off", "limited", "full"] = "off"
    penalties: Literal["off", "low", "standard", "strict"] = "off"
    fuel: Literal["off", "normal", "real"] = "off"
    tire: Literal["off", "normal", "real"] = "off"
    weather: Literal["fixed", "dynamic"] = "fixed"
    stewarding: Literal["none", "automated", "human"] = "automated"
    night: bool = False
    team: bool = False
    license: Literal["none", "entry", "intermediate", "advanced", "pro_sim"] = "none"
    official: bool = False
    assists: bool = False
    event_type: Literal["circuit", "rally_stage", "rallycross", "karting", "offroad", "historic"] | None = None
    car_class_list: List[str] = Field(default_factory=list)
    track_type: Literal["road", "street", "oval", "mixed", "stage"] | None = None
    surface_type: Literal["tarmac", "gravel", "dirt", "mixed", "snow", "other"] | None = None
    team_size_max: int = 1
    pit_rules: Dict[str, bool | int | str] = Field(default_factory=dict)
    rolling_start: bool = False
    time_acceleration: bool = False
    session_list: List[Literal["practice", "qualifying", "race"]] = Field(default_factory=list)
