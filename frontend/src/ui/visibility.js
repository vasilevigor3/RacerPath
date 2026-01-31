const query = (selector) => document.querySelectorAll(selector);

const toggleVisibility = (element, hidden) => {
  element.classList.toggle('is-hidden', hidden);
  element.setAttribute('aria-hidden', hidden ? 'true' : 'false');
};

const toggleGroup = (selector, hidden) => {
  query(selector).forEach((element) => toggleVisibility(element, hidden));
};

export const setAuthVisibility = (isAuthed) => {
  toggleGroup('[data-auth-only]', isAuthed);
  toggleGroup('[data-auth-required]', !isAuthed);
};

export const setOnboardingVisibility = (isComplete) => {
  toggleGroup('[data-onboarding-only]', isComplete);
  toggleGroup('[data-onboarding-hidden]', !isComplete);
};

export const isOnboardingComplete = (driver) => {
  if (!driver) return false;
  const hasDiscipline = Boolean(driver.primary_discipline);
  const hasGames = Array.isArray(driver.sim_games) && driver.sim_games.length > 0;
  return hasDiscipline && hasGames;
};

export const setAdminVisibility = (isAdmin) => {
  toggleGroup('[data-admin-only]', !isAdmin);
};

export const setDriverVisibility = (isDriver) => {
  toggleGroup('[data-driver-only]', !isDriver);
};
