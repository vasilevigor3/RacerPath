/**
 * Event.game can be short (ACC, AC); driver.sim_games use full names (Assetto Corsa Competizione, Assetto Corsa).
 * Treat these as the same when matching.
 */
const GAME_ALIASES = {
  ACC: ['Assetto Corsa Competizione'],
  'Assetto Corsa Competizione': ['ACC'],
  AC: ['Assetto Corsa'],
  'Assetto Corsa': ['AC'],
};

/**
 * Normalize game string for comparison (lowercase, trim).
 */
function normalizeGame(g) {
  return (g || '').trim().toLowerCase();
}

/**
 * All names that should match the given game (the name itself + aliases).
 */
export function namesForGame(game) {
  const g = (game || '').trim();
  if (!g) return [];
  const lower = g.toLowerCase();
  const out = new Set([g, lower]);
  const aliases = GAME_ALIASES[g] || GAME_ALIASES[g.toLowerCase()];
  if (aliases) aliases.forEach((a) => out.add(a) && out.add(a.toLowerCase()));
  return [...out];
}

/**
 * Returns true if event's game matches any of driver's sim_games (considering aliases).
 */
export function eventGameMatchesDriverGames(eventGame, driverSimGames) {
  if (!eventGame || !driverSimGames?.length) return false;
  const driverSet = new Set((driverSimGames || []).map(normalizeGame));
  const possible = namesForGame(eventGame);
  return possible.some((name) => driverSet.has(normalizeGame(name)));
}
