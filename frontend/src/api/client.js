import { getApiKey } from '../state/session.js';

export const apiFetch = (url, options = {}) => {
  const headers = { ...(options.headers || {}) };
  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return fetch(url, { ...options, headers });
};
