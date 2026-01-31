const API_KEY_STORAGE = 'racerpath_api_key';

let apiKey = window.localStorage.getItem(API_KEY_STORAGE) || '';
let currentUserName = '';
let currentProfileGoals = null;
let isAdmin = false;

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

export const resetSession = () => {
  setApiKey('');
  currentUserName = '';
  currentProfileGoals = null;
  readinessState.crsScore = 0;
  readinessState.profileCompletion = 0;
  readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    readinessState.hasDriver = false;
  isAdmin = false;
};
