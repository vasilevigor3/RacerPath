const API_KEY_STORAGE = 'racerpath_api_key';
const CURRENT_DRIVER_ID_STORAGE = 'racerpath_current_driver_id';

let apiKey = window.localStorage.getItem(API_KEY_STORAGE) || '';
let currentUserName = '';
let currentProfileGoals = null;
let isAdmin = false;
/** List of driver (career) objects for current user. Set after GET /api/drivers/me. */
let myDrivers = [];
/** Currently selected driver id (career). Persisted so reload keeps same career. */
let currentDriverId = window.localStorage.getItem(CURRENT_DRIVER_ID_STORAGE) || '';

export const readinessState = {
  crsScore: 0,
  profileCompletion: 0,
  tasksCompleted: 0,
  tasksTotal: 0,
  hasDriver: false
};

export const getApiKey = () => apiKey;

export const setApiKey = (value) => {
  apiKey = value || '';
  if (apiKey) {
    window.localStorage.setItem(API_KEY_STORAGE, apiKey);
  } else {
    window.localStorage.removeItem(API_KEY_STORAGE);
  }
};

export const getCurrentUserName = () => currentUserName;

export const setCurrentUserName = (value) => {
  currentUserName = value || '';
};

export const getCurrentProfileGoals = () => currentProfileGoals;

export const setCurrentProfileGoals = (value) => {
  currentProfileGoals = value || null;
};

export const isAdminUser = () => isAdmin;

export const setIsAdmin = (value) => {
  isAdmin = Boolean(value);
};

export const getMyDrivers = () => myDrivers;
export const setMyDrivers = (list) => {
  myDrivers = Array.isArray(list) ? list : [];
};

export const getCurrentDriverId = () => currentDriverId || (myDrivers[0] && myDrivers[0].id) || '';
export const setCurrentDriverId = (id) => {
  currentDriverId = id || '';
  if (currentDriverId) {
    window.localStorage.setItem(CURRENT_DRIVER_ID_STORAGE, currentDriverId);
  } else {
    window.localStorage.removeItem(CURRENT_DRIVER_ID_STORAGE);
  }
};

/** Current driver object (selected career). */
export const getCurrentDriver = () => {
  if (currentDriverId && myDrivers.length) {
    const d = myDrivers.find((x) => x.id === currentDriverId);
    if (d) return d;
  }
  return myDrivers[0] || null;
};

export const resetSession = () => {
  setApiKey('');
  currentUserName = '';
  currentProfileGoals = null;
  myDrivers = [];
  currentDriverId = '';
  window.localStorage.removeItem(CURRENT_DRIVER_ID_STORAGE);
  readinessState.crsScore = 0;
  readinessState.profileCompletion = 0;
  readinessState.tasksCompleted = 0;
  readinessState.tasksTotal = 0;
  readinessState.hasDriver = false;
  isAdmin = false;
};
