"""
Penalty and incident scores for UI and reporting.

CRS (driver rating) uses only Incident.score per participation; Penalty is for UI/result/audit only.
PENALTY_TYPE_SCORES: used when creating a Penalty (stored in DB for display). Not used in CRS.
"""

from enum import IntEnum


class TimePenaltySeconds(IntEnum):
    """Allowed time penalty amounts (seconds). Used when penalty_type=time_penalty."""
    s1 = 1
    s2 = 2
    s5 = 5
    s10 = 10
    s15 = 15
    s30 = 30


ALLOWED_TIME_PENALTY_SECONDS = frozenset(e.value for e in TimePenaltySeconds)


# Score deducted from participation base (100) per penalty. CRS uses sum of penalty scores.
PENALTY_TYPE_SCORES = {
    "time_penalty": 6.0,
    "drive_through": 8.0,
    "stop_and_go": 10.0,
    "dsq": 35.0,
}

DEFAULT_PENALTY_SCORE = 6.0  # fallback when penalty_type not in map or legacy null score


def get_score_for_penalty_type(penalty_type: str) -> float:
    """Return CRS score for penalty type (string enum value)."""
    return PENALTY_TYPE_SCORES.get(penalty_type, DEFAULT_PENALTY_SCORE)


# Reference: Situation -> Incident type -> Penalty type (for future incident/penalty mapping)
# Each penalty type has its own score in PENALTY_TYPE_SCORES above.
# Incident types can have their own scores (e.g. INCIDENT_TYPE_SCORES) for incident-only CRS impact.
#
# | Situation                           | Incident             | Penalty      |
# | ----------------------------------- | -------------------- | ------------ |
# | Лёгкий боковой контакт              | Light contact        | ❌            |
# | Контакт → потеря позиции соперником | Causing disadvantage | +Time        |
# | Удар сзади (brake too late)         | Rear-end collision   | +Time / DT   |
# | Выдавливание за трассу              | Forcing off track    | +Time        |
# | Контакт → разворот соперника        | Causing spin         | +Time / DT   |
# | Контакт → сход соперника            | Causing retirement   | DT / Stop&Go |
# | Массовый завал                      | Multi-car incident   | DSQ / Grid   |
# | Netcode / racing incident           | Racing incident      | ❌            |
#
SITUATION_INCIDENT_PENALTY = [
    {"situation": "Light side contact", "incident": "Light contact", "penalty": None},
    {"situation": "Contact → opponent loses position", "incident": "Causing disadvantage", "penalty": "time_penalty"},
    {"situation": "Rear-end (brake too late)", "incident": "Rear-end collision", "penalty": "time_penalty"},  # or drive_through
    {"situation": "Forcing off track", "incident": "Forcing off track", "penalty": "time_penalty"},
    {"situation": "Contact → opponent spin", "incident": "Causing spin", "penalty": "time_penalty"},  # or drive_through
    {"situation": "Contact → opponent retirement", "incident": "Causing retirement", "penalty": "drive_through"},  # or stop_and_go
    {"situation": "Multi-car pileup", "incident": "Multi-car incident", "penalty": "dsq"},
    {"situation": "Netcode / racing incident", "incident": "Racing incident", "penalty": None},
]
