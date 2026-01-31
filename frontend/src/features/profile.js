import { apiFetch } from '../api/client.js';
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
import { setList, getFormValue } from '../utils/dom.js';
import { formatDiscipline, toInitials } from '../utils/format.js';
import { getCheckedValues, setCheckedValues } from '../utils/forms.js';
import { parseOptionalInt } from '../utils/parse.js';
import {
  loadDashboardStats,
  loadTasksOverview,
  loadDashboardRecommendations,
  loadDashboardEvents,
  loadLicenseProgress,
  loadActivityFeed
} from './dashboard.js';
import { loadIncidents } from './incidents.js';
import {
  updateDriverSnapshotMeta,
  updateDriverSnapshotChallenges,
  updateDriverSnapshotRisks,
  resetDriverSnapshot
} from './driverSnapshot.js';
import { refreshAdminPanel } from './admin.js';

const dashboardName = document.querySelector('[data-dashboard-name]');
const profileInitials = document.querySelector('[data-profile-initials]');
const profileFullname = document.querySelector('[data-profile-fullname]');
const profileLocation = document.querySelector('[data-profile-location]');
const profileDiscipline = document.querySelector('[data-profile-discipline]');
const profilePlatforms = document.querySelector('[data-profile-platforms]');
const profileUserId = document.querySelector('[data-profile-user-id]');
const profileGoals = document.querySelector('[data-profile-goals]');
const profileGoalsDisplay = document.querySelector('[data-profile-goals-display]');
const profileCtaButton = document.querySelector('[data-profile-cta-button]');
const profileChecklist = document.querySelector('[data-profile-checklist]');
const profileCompletion = document.querySelector('[data-profile-completion]');
const profileLevel = document.querySelector('[data-profile-level]');
const profileMissing = document.querySelector('[data-profile-missing]');
const profileCta = document.querySelector('[data-profile-cta]');
const licenseCurrent = document.querySelector('[data-license-current]');
const licenseNext = document.querySelector('[data-license-next]');
const licenseReqs = document.querySelector('[data-license-reqs]');
const activityFeed = document.querySelector('[data-activity-feed]');
const profileForm = document.querySelector('[data-profile-form]');
const profileSaveStatus = document.querySelector('[data-profile-save-status]');
const profileStatus = document.querySelector('[data-profile-status]');
const profileName = document.querySelector('[data-profile-name]');
const profileRole = document.querySelector('[data-profile-role]');
const profileDriver = document.querySelector('[data-profile-driver]');
const loginStatus = document.querySelector('[data-login-status]');

const fieldLabels = {
  full_name: 'Full name',
  country: 'Country',
  city: 'City',
  experience_years: 'Experience years',
  primary_discipline: 'Primary discipline',
  sim_platforms: 'Sim platforms',
  goals: 'Goals'
};

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
  if (profilePlatforms) profilePlatforms.textContent = 'Platforms: --';
  setProfileIdLabel('--', 'Driver ID');
  if (profileGoals) profileGoals.textContent = 'System goals will appear after your first recommendations.';
  if (profileGoalsDisplay) {
    profileGoalsDisplay.textContent = 'System goals will appear after your first recommendations.';
  }
  if (profileCtaButton) profileCtaButton.textContent = 'Complete profile';
  if (licenseCurrent) licenseCurrent.textContent = '--';
  if (licenseNext) licenseNext.textContent = '--';
  if (licenseReqs) setList(licenseReqs, [], 'Log in to see license progress.');
  if (activityFeed) setList(activityFeed, [], 'Log in to see activity.');
  if (profileForm) {
    const disciplineInput = profileForm.querySelector('#profileDiscipline');
    if (disciplineInput) disciplineInput.value = '';
    setCheckedValues(profileForm, 'profilePlatforms', []);
    setCheckedValues(profileForm, 'rigOptions', []);
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
    const systemGoals = profile.goals || 'System goals will appear after your first recommendations.';
    if (profileGoals) profileGoals.textContent = systemGoals;
    if (profileGoalsDisplay) profileGoalsDisplay.textContent = systemGoals;
    if (profileCompletion) profileCompletion.style.width = `${profile.completion_percent || 0}%`;
    if (profileLevel) profileLevel.textContent = profile.level || 'Rookie';
    readinessState.profileCompletion = profile.completion_percent || 0;
    if (profileMissing) {
      const missing = profile.missing_fields || [];
      profileMissing.textContent =
        missing.length === 0
          ? 'Profile complete.'
          : `Missing ${missing.length} fields to level up.`;
    }
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
    if (profileChecklist) {
      const items = (profile.missing_fields || []).map((field) => `Add ${fieldLabels[field] || field}`);
      setList(profileChecklist, items, 'Profile complete.');
    }
    if (profileForm) {
      const platforms = profile.sim_platforms || [];
      const fallbackPlatforms =
        platforms.length
          ? platforms
          : driver && driver.sim_games && driver.sim_games.length
            ? driver.sim_games
            : [];
      const fullNameInput = profileForm.querySelector('#profileFullName');
      const countryInput = profileForm.querySelector('#profileCountry');
      const cityInput = profileForm.querySelector('#profileCity');
      const ageInput = profileForm.querySelector('#profileAge');
      const expInput = profileForm.querySelector('#profileExperience');
      const disciplineInput = profileForm.querySelector('#profileDiscipline');
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
      setCheckedValues(profileForm, 'profilePlatforms', fallbackPlatforms);
      const rigSelections = (profile.rig || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      setCheckedValues(profileForm, 'rigOptions', rigSelections);
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
    if (profileCompletion) profileCompletion.style.width = '0%';
    if (profileLevel) profileLevel.textContent = 'Rookie';
    if (profileMissing) profileMissing.textContent = 'Log in to complete profile.';
    updateReadiness();
    return;
  }
  if (loginStatus) loginStatus.textContent = 'Checking session...';
  try {
    const res = await apiFetch('/api/auth/me');
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
    await loadActivityFeed(driver);
    await loadIncidents(driver);
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

export const initProfileForm = () => {
  if (!profileForm || !profileSaveStatus) return;
  profileForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!getApiKey()) {
      profileSaveStatus.textContent = 'Log in first.';
      return;
    }
    profileSaveStatus.textContent = 'Saving profile...';
    const platforms = getCheckedValues(profileForm, 'profilePlatforms');
    const rigOptions = getCheckedValues(profileForm, 'rigOptions');
    const rigValue = rigOptions.length ? rigOptions.join(', ') : null;
    try {
      const res = await apiFetch('/api/profile/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: getFormValue(profileForm, '#profileFullName') || null,
          country: getFormValue(profileForm, '#profileCountry') || null,
          city: getFormValue(profileForm, '#profileCity') || null,
          age: parseOptionalInt(getFormValue(profileForm, '#profileAge')),
          experience_years: parseOptionalInt(getFormValue(profileForm, '#profileExperience')),
          primary_discipline: getFormValue(profileForm, '#profileDiscipline') || null,
          sim_platforms: platforms,
          rig: rigValue,
          goals: getCurrentProfileGoals()
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        profileSaveStatus.textContent = err.detail || 'Save failed.';
        return;
      }
      profileSaveStatus.textContent = 'Profile saved.';
      await loadProfile();
    } catch (err) {
      profileSaveStatus.textContent = 'Save failed.';
    }
  });
};
