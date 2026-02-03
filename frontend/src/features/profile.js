import { apiFetch, apiFetchWithRetry } from '../api/client.js';
import {
  readinessState,
  getApiKey,
  setCurrentUserName,
  getCurrentUserName,
  setCurrentProfileGoals,
  getCurrentProfileGoals,
  setIsAdmin
} from '../state/session.js';
import { setAuthVisibility, setOnboardingVisibility, isOnboardingComplete, setAdminVisibility, setDriverVisibility } from '../ui/visibility.js';
import { updateReadiness } from '../ui/readiness.js';
import { getFormValue } from '../utils/dom.js';
import { formatDiscipline, toInitials } from '../utils/format.js';
import { getCheckedValues, setCheckedValues } from '../utils/forms.js';
import { parseOptionalInt } from '../utils/parse.js';
import {
  loadDashboardStats,
  loadTasksOverview,
  loadDashboardRecommendations,
  loadDashboardEvents,
  loadLicenseProgress
} from './dashboard.js';
import { loadIncidents } from './incidents.js';
import { loadPenalties } from './penalties.js';
import { updateDriverSnapshotMeta, resetDriverSnapshot } from './driverSnapshot.js';
import { refreshAdminPanel } from './admin.js';

const dashboardName = document.querySelector('[data-dashboard-name]');
const profileInitials = document.querySelector('[data-profile-initials]');
const profileFullname = document.querySelector('[data-profile-fullname]');
const profileLocation = document.querySelector('[data-profile-location]');
const profileDiscipline = document.querySelector('[data-profile-discipline]');
const profileTier = document.querySelector('[data-profile-tier]');
const profilePlatforms = document.querySelector('[data-profile-platforms]');
const profileUserId = document.querySelector('[data-profile-user-id]');
const profileCtaButton = document.querySelector('[data-profile-cta-button]');
const profileNextTier = document.querySelector('[data-profile-next-tier]');
const profileNextTierMeta = document.querySelector('[data-profile-next-tier-meta]');
const profileCta = document.querySelector('[data-profile-cta]');
const licenseCurrent = document.querySelector('[data-license-current]');
const licenseNext = document.querySelector('[data-license-next]');
const profileForm = document.querySelector('[data-profile-form]');
const profileSaveStatus = document.querySelector('[data-profile-save-status]');
const profileStatus = document.querySelector('[data-profile-status]');
const profileName = document.querySelector('[data-profile-name]');
const profileRole = document.querySelector('[data-profile-role]');
const profileDriver = document.querySelector('[data-profile-driver]');
const loginStatus = document.querySelector('[data-login-status]');

let currentUserId = '';

const setProfileIdLabel = (value, label = 'Driver ID') => {
  if (!profileUserId) return;
  const display = value || '--';
  profileUserId.textContent = `${label}: ${display}`;
};

export const setProfileEmpty = (message, options = {}) => {
  const { hideDriver = true, hideAdmin = true } = options;
  setCurrentProfileGoals(null);
  resetDriverSnapshot();
  if (hideDriver) setDriverVisibility(false);
  if (hideAdmin) setAdminVisibility(false);
  if (profileStatus) profileStatus.textContent = message;
  if (profileName) profileName.textContent = '--';
  if (profileRole) profileRole.textContent = '--';
  if (profileDriver) profileDriver.textContent = 'No driver profile yet.';
  if (profileInitials) profileInitials.textContent = 'RP';
  if (profileFullname) profileFullname.textContent = '--';
  if (profileLocation) profileLocation.textContent = 'Location not set';
  if (profileDiscipline) profileDiscipline.textContent = 'Discipline: --';
  if (profileTier) profileTier.textContent = 'Tier: --';
  if (profilePlatforms) profilePlatforms.textContent = 'Platforms: --';
  setProfileIdLabel('--', 'Driver ID');
  if (profileCtaButton) profileCtaButton.textContent = 'Complete profile';
  if (licenseCurrent) {
    licenseCurrent.textContent = '--';
    delete licenseCurrent.dataset.licenseCode;
  }
  if (licenseNext) {
    licenseNext.textContent = '--';
    delete licenseNext.dataset.licenseCode;
  }
  if (profileNextTier) profileNextTier.style.width = '0%';
  if (profileNextTierMeta) profileNextTierMeta.textContent = 'Complete profile and races to advance.';
  if (profileForm) {
    const disciplineInput = profileForm.querySelector('#profileDiscipline');
    if (disciplineInput) disciplineInput.value = '';
    setCheckedValues(profileForm, 'profilePlatforms', []);
    const wheelSelect = profileForm.querySelector('#profileWheelType');
    const pedalsSelect = profileForm.querySelector('#profilePedalsClass');
    const clutchCheck = profileForm.querySelector('#profileManualWithClutch');
    if (wheelSelect) wheelSelect.value = '';
    if (pedalsSelect) pedalsSelect.value = '';
    if (clutchCheck) clutchCheck.checked = false;
  }
};

const loadUserProfile = async (driver) => {
  if (!getApiKey()) return null;
  try {
    const res = await apiFetch('/api/profile/me');
    if (!res.ok) throw new Error('failed');
    const profile = await res.json();
    const displayName = profile.full_name || (dashboardName ? dashboardName.textContent : '');
    if (profileInitials) profileInitials.textContent = toInitials(displayName || '');
    if (profileFullname) profileFullname.textContent = profile.full_name || displayName || 'Full name missing';
    if (profileLocation) {
      const location = [profile.city, profile.country].filter(Boolean).join(', ');
      profileLocation.textContent = location || 'Location not set';
    }
    if (profileDiscipline) {
      profileDiscipline.textContent = `Discipline: ${formatDiscipline(profile.primary_discipline)}`;
    }
    if (profileTier && driver) {
      profileTier.textContent = `Tier: ${driver.tier ?? 'E0'}`;
    }
    if (profilePlatforms) {
      const platforms =
        profile.sim_platforms && profile.sim_platforms.length
          ? profile.sim_platforms
          : driver && driver.sim_games && driver.sim_games.length
            ? driver.sim_games
            : [];
      profilePlatforms.textContent = platforms.length
        ? `Platforms: ${platforms.join(', ')}`
        : 'Platforms: --';
    }
    const playerId = driver ? driver.id : currentUserId;
    setProfileIdLabel(playerId, driver ? 'Driver ID' : 'User ID');
    setCurrentProfileGoals(profile.goals || null);
    const systemGoals = profile.goals || '';
    const nextTierPercent =
      profile.next_tier_progress_percent != null ? profile.next_tier_progress_percent : 0;
    if (profileNextTier) profileNextTier.style.width = `${nextTierPercent}%`;
    if (profileNextTierMeta) {
      const data = profile.next_tier_data;
      if (data && (data.events_required > 0 || (data.missing_license_codes && data.missing_license_codes.length))) {
        const parts = [];
        if (data.events_required > 0) {
          parts.push(`${data.events_done}/${data.events_required} events (difficulty > ${data.difficulty_threshold})`);
        }
        if (data.missing_license_codes && data.missing_license_codes.length) {
          parts.push(`Missing licenses: ${data.missing_license_codes.join(', ')}`);
        }
        profileNextTierMeta.textContent = parts.join('. ') || 'Complete requirements to advance tier.';
      } else if (data && data.events_required === 0 && (!data.missing_license_codes || !data.missing_license_codes.length)) {
        profileNextTierMeta.textContent = 'Tier rule not set. Add min_events and threshold in Admin → Tier progression.';
      } else {
        const missing = profile.missing_fields || [];
        profileNextTierMeta.textContent =
          missing.length === 0
            ? (nextTierPercent >= 100 ? 'Tier complete.' : 'Profile complete. Race to advance tier.')
            : `Missing ${missing.length} fields to advance.`;
      }
    }
    readinessState.profileCompletion = profile.profile_completion_percent || 0;
    if (profileCtaButton) {
      const missing = profile.missing_fields || [];
      profileCtaButton.textContent = missing.length === 0 ? 'Edit profile' : 'Complete profile';
    }
    if (profileCta) {
      profileCta.textContent =
        profile.missing_fields && profile.missing_fields.length
          ? 'Complete missing fields to unlock your next level.'
          : 'Profile complete. Keep racing to progress.';
    }
    const formEl = profileForm || document.querySelector('[data-profile-form]');
    if (formEl) {
      const platforms = profile.sim_platforms || [];
      const fallbackPlatforms =
        platforms.length
          ? platforms
          : driver && driver.sim_games && driver.sim_games.length
            ? driver.sim_games
            : [];
      const fullNameInput = formEl.querySelector('#profileFullName');
      const countryInput = formEl.querySelector('#profileCountry');
      const cityInput = formEl.querySelector('#profileCity');
      const ageInput = formEl.querySelector('#profileAge');
      const expInput = formEl.querySelector('#profileExperience');
      const disciplineInput = formEl.querySelector('#profileDiscipline');
      if (fullNameInput) {
        const fallbackName = profile.full_name || (driver ? driver.name : '') || getCurrentUserName() || '';
        fullNameInput.value = fallbackName;
      }
      if (countryInput) countryInput.value = profile.country || '';
      if (cityInput) cityInput.value = profile.city || '';
      if (ageInput) ageInput.value = profile.age ?? '';
      if (expInput) expInput.value = profile.experience_years ?? '';
      if (disciplineInput) {
        disciplineInput.value = profile.primary_discipline || (driver ? driver.primary_discipline : '') || '';
      }
      setCheckedValues(formEl, 'profilePlatforms', fallbackPlatforms);
      const ro = driver && driver.rig_options ? driver.rig_options : {};
      const wheelSelect = formEl.querySelector('#profileWheelType');
      const pedalsSelect = formEl.querySelector('#profilePedalsClass');
      const clutchCheck = formEl.querySelector('#profileManualWithClutch');
      if (wheelSelect) wheelSelect.value = ro.wheel_type || '';
      if (pedalsSelect) pedalsSelect.value = ro.pedals_class || '';
      if (clutchCheck) clutchCheck.checked = Boolean(ro.manual_with_clutch);
    }
    updateReadiness();
    const readinessLabel =
      profile.missing_fields && profile.missing_fields.length
        ? `Missing ${profile.missing_fields.length} fields to level up.`
        : 'Profile complete. Keep racing to progress.';
    updateDriverSnapshotMeta({
      name: profile.full_name || (driver ? driver.name : '') || getCurrentUserName() || 'Driver',
      discipline:
        profile.primary_discipline || (driver ? driver.primary_discipline : '') || 'GT / Touring',
      description: systemGoals,
      readinessPercent: readinessState.profileCompletion,
      readinessMetaText: readinessLabel,
      crsScore: readinessState.crsScore,
      tasksCompleted: readinessState.tasksCompleted,
      tasksTotal: readinessState.tasksTotal
    });
    return profile;
  } catch (err) {
    return null;
  }
};

const loadMyDriver = async () => {
  if (!getApiKey()) return null;
  try {
    const res = await apiFetch('/api/drivers/me');
    if (!res.ok) {
      if (profileDriver) profileDriver.textContent = 'Unable to load driver profile.';
      return null;
    }
    const driver = await res.json();
    if (!driver) {
      if (profileDriver) profileDriver.textContent = 'No driver profile yet.';
      return null;
    }
    if (profileDriver) profileDriver.textContent = `${driver.name} / ${driver.primary_discipline}`;
    return driver;
  } catch (err) {
    if (profileDriver) profileDriver.textContent = 'Unable to load driver profile.';
    return null;
  }
};

export const loadProfile = async () => {
  if (!getApiKey()) {
    setAuthVisibility(false);
    setOnboardingVisibility(false);
    setIsAdmin(false);
    setAdminVisibility(false);
    readinessState.crsScore = 0;
    readinessState.profileCompletion = 0;
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    readinessState.hasDriver = false;
    setCurrentUserName('');
    setProfileEmpty('Log in to see your profile.');
    if (loginStatus) loginStatus.textContent = 'Not logged in.';
    if (dashboardName) dashboardName.textContent = 'Driver';
    if (profileNextTier) profileNextTier.style.width = '0%';
    if (profileNextTierMeta) profileNextTierMeta.textContent = 'Complete profile and races to advance.';
    updateReadiness();
    return;
  }
  if (loginStatus) loginStatus.textContent = 'Checking session...';
  try {
    const res = await apiFetchWithRetry(
      '/api/auth/me',
      {},
      (attempt, delayMs) => {
        if (loginStatus) {
          loginStatus.textContent = `Server starting… retry in ${delayMs / 1000}s`;
        }
      }
    );
    if (!res.ok) {
      setAuthVisibility(false);
      setOnboardingVisibility(false);
      readinessState.crsScore = 0;
      readinessState.profileCompletion = 0;
      readinessState.tasksCompleted = 0;
      readinessState.tasksTotal = 0;
      readinessState.hasDriver = false;
      setCurrentUserName('');
      setProfileEmpty('Session invalid. Please log in again.');
      if (loginStatus) loginStatus.textContent = 'Invalid session. Please log in again.';
      if (dashboardName) dashboardName.textContent = 'Driver';
      updateReadiness();
      return;
    }
    const user = await res.json();
    currentUserId = user.id || '';
    const isAdminUser = user.role === 'admin';
    setIsAdmin(isAdminUser);
    setAdminVisibility(isAdminUser);
    setDriverVisibility(!isAdminUser);
    if (isAdminUser) {
      setAuthVisibility(true);
      setCurrentUserName(user.name || '');
      if (profileStatus) profileStatus.textContent = 'Admin console.';
      if (profileName) profileName.textContent = user.name || '--';
      if (profileRole) profileRole.textContent = user.role || '--';
      if (loginStatus) loginStatus.textContent = `Logged in as ${user.name}.`;
      if (dashboardName) dashboardName.textContent = user.name || 'Admin';
      setOnboardingVisibility(true);
      setProfileEmpty('Admin console only.', { hideAdmin: false });
      setProfileIdLabel(currentUserId, 'User ID');
      await refreshAdminPanel();
      updateReadiness();
      return;
    }
    setAuthVisibility(true);
    setCurrentUserName(user.name || '');
    if (profileStatus) profileStatus.textContent = 'Logged in.';
    if (profileName) profileName.textContent = user.name || '--';
    if (profileRole) profileRole.textContent = user.role || '--';
    if (loginStatus) loginStatus.textContent = `Logged in as ${user.name}.`;
    if (dashboardName) dashboardName.textContent = user.name || 'Driver';
    const driver = await loadMyDriver();
    const profile = await loadUserProfile(driver);
    const onboardingComplete = isOnboardingComplete(driver);
    setOnboardingVisibility(onboardingComplete);
    if (!profile) {
      readinessState.profileCompletion = 0;
      updateReadiness();
    }
    if (!onboardingComplete) {
      if (profileStatus) profileStatus.textContent = 'Onboarding required to unlock the dashboard.';
      readinessState.hasDriver = Boolean(driver);
      updateReadiness();
      return;
    }
    await loadDashboardStats(driver);
    await loadTasksOverview(driver);
    await loadDashboardRecommendations(driver);
    await loadDashboardEvents(driver);
    await loadLicenseProgress(driver);
    await loadIncidents(driver);
    await loadPenalties(driver);
    scheduleRecommendationsRefetchAtMidnight();
  } catch (err) {
    setAuthVisibility(false);
    setOnboardingVisibility(false);
    setIsAdmin(false);
    setAdminVisibility(false);
    readinessState.crsScore = 0;
    readinessState.profileCompletion = 0;
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    readinessState.hasDriver = false;
    setCurrentUserName('');
    setProfileEmpty('Unable to load profile.');
    if (loginStatus) loginStatus.textContent = 'Login failed.';
    if (dashboardName) dashboardName.textContent = 'Driver';
    updateReadiness();
  }
};

/** Refetch recommendations at next midnight UTC so "Race of the day" etc. update when the day changes. */
let recommendationsMidnightTimer = null;
function scheduleRecommendationsRefetchAtMidnight() {
  if (recommendationsMidnightTimer) clearTimeout(recommendationsMidnightTimer);
  const now = new Date();
  const nextMidnight = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
  const msUntilMidnight = nextMidnight.getTime() - now.getTime();
  recommendationsMidnightTimer = setTimeout(async () => {
    recommendationsMidnightTimer = null;
    try {
      const driver = await loadMyDriver();
      if (driver) await loadDashboardRecommendations(driver);
    } catch (_) {}
    scheduleRecommendationsRefetchAtMidnight();
  }, Math.max(msUntilMidnight, 60000));
}

/** When tab becomes visible, refetch recommendations so "Race of the day" and expiry state are up to date. */
function onVisibilityChange() {
  if (document.visibilityState !== 'visible') return;
  loadMyDriver()
    .then((driver) => driver && loadDashboardRecommendations(driver))
    .catch(() => {});
}

export const initProfileForm = () => {
  const form = document.querySelector('[data-profile-form]');
  const statusEl = document.querySelector('[data-profile-save-status]');
  if (!form || !statusEl) {
    setTimeout(initProfileForm, 0);
    return;
  }
  if (form.dataset.profileFormInitialized === '1') return;
  form.dataset.profileFormInitialized = '1';
  document.addEventListener('visibilitychange', onVisibilityChange);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!getApiKey()) {
      statusEl.textContent = 'Log in first.';
      return;
    }
    statusEl.textContent = 'Saving profile...';
    const platforms = getCheckedValues(form, 'profilePlatforms');
    const wheelType = getFormValue(form, '#profileWheelType') || null;
    const pedalsClass = getFormValue(form, '#profilePedalsClass') || null;
    const manualWithClutch = form.querySelector('#profileManualWithClutch')?.checked ?? false;
    try {
      const res = await apiFetch('/api/profile/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: getFormValue(form, '#profileFullName') || null,
          country: getFormValue(form, '#profileCountry') || null,
          city: getFormValue(form, '#profileCity') || null,
          age: parseOptionalInt(getFormValue(form, '#profileAge')),
          experience_years: parseOptionalInt(getFormValue(form, '#profileExperience')),
          primary_discipline: getFormValue(form, '#profileDiscipline') || null,
          sim_platforms: platforms,
          rig_options: {
            wheel_type: wheelType,
            pedals_class: pedalsClass,
            manual_with_clutch: manualWithClutch
          },
          goals: getCurrentProfileGoals()
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        statusEl.textContent = err.detail || 'Save failed.';
        return;
      }
      statusEl.textContent = 'Profile saved.';
      await loadProfile();
    } catch (err) {
      statusEl.textContent = 'Save failed.';
    }
  });
};
