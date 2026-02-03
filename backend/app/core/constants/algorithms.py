"""Algorithm versions and limits (CRS, recommendations, global tasks)."""

CRS_ALGO_VERSION = "crs_v2"  # v2: rating from Incident.score only; Penalty is UI/result only
REC_ALGO_VERSION = "rec_v1"
PARTICIPATIONS_INPUT_LIMIT = 20

# CRS v2: participation_score = 100 - incident_deduction - status - repeat_penalty + consistency - pace
INCIDENT_K = 2.0  # incident_deduction = incident_score_sum * INCIDENT_K
FREE_INCIDENTS = 2  # first N incidents exempt from repeat penalty
REPEAT_K = 1.0  # repeat_penalty = max(0, incidents_count - FREE_INCIDENTS) * REPEAT_K

TIER_WEIGHTS = {
    "E0": 0.6,
    "E1": 0.8,
    "E2": 1.0,
    "E3": 1.2,
    "E4": 1.4,
    "E5": 1.6,
}

GT_GLOBAL_PROFILE = "GT_GLOBAL_PROFILE"
GT_GLOBAL_SIM_GAMES = "GT_GLOBAL_SIM_GAMES"
