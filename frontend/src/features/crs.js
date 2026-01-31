import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';

const crsForm = document.querySelector('[data-crs-form]');
const crsStatus = document.querySelector('[data-crs-status]');
const crsLatest = document.querySelector('[data-crs-latest]');
const crsList = document.querySelector('[data-crs-list]');
const crsComputeButton = document.querySelector('[data-crs-compute]');
const crsHistoryButton = document.querySelector('[data-crs-history]');

const loadCrsHistory = async (driverId, discipline) => {
  if (!crsList) return;
  crsList.innerHTML = '<li>Loading...</li>';
  try {
    const res = await apiFetch(`/api/crs/history?driver_id=${driverId}&discipline=${discipline}`);
    if (!res.ok) throw new Error('failed');
    const history = await res.json();
    if (!history.length) {
      crsList.innerHTML = '<li>No CRS history.</li>';
      return;
    }
    if (crsLatest) crsLatest.textContent = history[0].score;
    crsList.innerHTML = history
      .slice(0, 5)
      .map((item) => `<li>${item.score} / ${new Date(item.computed_at).toLocaleString()}</li>`)
      .join('');
  } catch (err) {
    crsList.innerHTML = '<li>Unable to load CRS.</li>';
  }
};

const computeCrs = async () => {
  if (!crsForm || !crsStatus) return;
  const driverId = getFormValue(crsForm, '#crsDriverId');
  const discipline = getFormValue(crsForm, '#crsDiscipline') || 'gt';
  if (!driverId) {
    crsStatus.textContent = 'Driver ID required.';
    return;
  }
  crsStatus.textContent = 'Computing CRS...';
  try {
    const res = await apiFetch(`/api/crs/compute?driver_id=${driverId}&discipline=${discipline}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      crsStatus.textContent = err.detail || 'CRS compute failed.';
      return;
    }
    const data = await res.json();
    if (crsLatest) crsLatest.textContent = data.score;
    crsStatus.textContent = 'CRS updated.';
    await loadCrsHistory(driverId, discipline);
  } catch (err) {
    crsStatus.textContent = 'CRS compute failed.';
  }
};

export const initCrs = () => {
  if (crsComputeButton) {
    crsComputeButton.addEventListener('click', computeCrs);
  }
  if (crsHistoryButton) {
    crsHistoryButton.addEventListener('click', () => {
      if (!crsForm) return;
      const driverId = getFormValue(crsForm, '#crsDriverId');
      const discipline = getFormValue(crsForm, '#crsDiscipline') || 'gt';
      if (driverId) {
        loadCrsHistory(driverId, discipline);
      }
    });
  }
};
