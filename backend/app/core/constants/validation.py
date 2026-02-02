"""Validation sets for event/participation normalization (ingest, API)."""

ALLOWED_SESSION_TYPE = {"race", "training"}
ALLOWED_SCHEDULE = {"daily", "weekly", "seasonal", "special"}
ALLOWED_EVENT_TYPE = {"circuit", "rally_stage", "rallycross", "karting", "offroad", "historic"}
ALLOWED_FORMAT = {"sprint", "endurance", "series", "time_trial"}
ALLOWED_DAMAGE = {"off", "visual", "limited", "full"}
ALLOWED_PENALTIES = {"off", "low", "standard", "strict"}
ALLOWED_FUEL = {"off", "normal", "real"}
ALLOWED_TIRE = {"off", "normal", "real"}
ALLOWED_WEATHER = {"fixed", "dynamic"}
ALLOWED_STEWARDING = {"none", "automated", "human_review"}
ALLOWED_LICENSE = {"none", "entry", "intermediate", "advanced", "pro_sim"}
ALLOWED_SURFACE = {"tarmac", "gravel", "dirt", "mixed", "snow", "other"}
ALLOWED_TRACK = {"road", "street", "oval", "mixed", "stage"}
