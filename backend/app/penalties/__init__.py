# Penalties: penalty types and business logic (see PENALTIES.md).

from app.penalties.scores import (
    ALLOWED_TIME_PENALTY_SECONDS,
    TimePenaltySeconds,
)

__all__ = ["ALLOWED_TIME_PENALTY_SECONDS", "TimePenaltySeconds"]
