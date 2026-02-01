import { getApiKey } from '../state/session.js';

export const apiFetch = (url, options = {}) => {
  const headers = { ...(options.headers || {}) };
  const apiKey = getApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return fetch(url, { ...options, headers });
};

const RETRYABLE_STATUS = new Set([502, 503, 504]);
const RETRY_DELAYS_MS = [2000, 4000, 6000, 8000, 10000];
export const API_FETCH_MAX_RETRIES = RETRY_DELAYS_MS.length;

/** Same as apiFetch but retries on 502/503/504 or network error (e.g. backend not ready after rebuild). */
export const apiFetchWithRetry = async (url, options = {}, onRetry) => {
  let lastRes = null;
  let lastErr = null;
  for (let attempt = 0; attempt <= API_FETCH_MAX_RETRIES; attempt++) {
    try {
      const res = await apiFetch(url, options);
      if (res.ok || !RETRYABLE_STATUS.has(res.status)) {
        return res;
      }
      lastRes = res;
      if (attempt < API_FETCH_MAX_RETRIES && onRetry) {
        onRetry(attempt + 1, RETRY_DELAYS_MS[attempt]);
      }
      if (attempt < API_FETCH_MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, RETRY_DELAYS_MS[attempt]));
      }
    } catch (err) {
      lastErr = err;
      if (attempt < API_FETCH_MAX_RETRIES && onRetry) {
        onRetry(attempt + 1, RETRY_DELAYS_MS[attempt]);
      }
      if (attempt < API_FETCH_MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, RETRY_DELAYS_MS[attempt]));
      }
    }
  }
  if (lastRes) return lastRes;
  throw lastErr;
};
