"""Game name aliases: profile/onboarding use full names (e.g. Assetto Corsa Competizione), admin events use short (e.g. ACC)."""

GAME_ALIASES_LONG_TO_SHORT = {
    "Assetto Corsa Competizione": "ACC",
    "Assetto Corsa": "AC",
}


def expand_driver_games_for_event_match(driver_games: list) -> list:
    """Include short names so Event.game='ACC' matches driver with sim_games=['Assetto Corsa Competizione']."""
    out = list(driver_games) if driver_games else []
    for long_name, short_name in GAME_ALIASES_LONG_TO_SHORT.items():
        if long_name in out and short_name not in out:
            out.append(short_name)
    return out
