from enum import Enum

class EventStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    live = "live"
    completed = "completed"
    finished = "finished"
    cancelled = "cancelled"

class ScheduleType(str, Enum):
    weekly = "weekly"
    daily = "daily"
    tournament = "tournament"
    special = "special"


class EventType(str, Enum):
    circuit = "circuit"
    rally = "rally"
    drift = "drift"
    time_attack = "time_attack"


class FormatType(str, Enum):
    sprint = "sprint"
    endurance = "endurance"
    hotlap = "hotlap"


class DamageModel(str, Enum):
    off = "off"
    reduced = "reduced"
    full = "full"
    limited = "limited"


class RulesToggle(str, Enum):
    off = "off"
    reduced = "reduced"
    realistic = "realistic"
    real = "real"
    normal = "normal"
    strict = "strict"
    standard = "standard"


class WeatherType(str, Enum):
    fixed = "fixed"
    dynamic = "dynamic"


class StewardingType(str, Enum):
    none = "none"
    automated = "automated"
    live = "live"
    human_review = "human_review"
    standard = "standard"  # legacy/alias for automated


class LicenseRequirement(str, Enum):
    none = "none"
    entry = "entry"
    rookie = "rookie"
    intermediate = "intermediate"
    pro = "pro"
