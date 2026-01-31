import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';

const licenseForm = document.querySelector('[data-license-form]');
const licenseStatus = document.querySelector('[data-license-status]');
const licenseList = document.querySelector('[data-license-list]');
const licenseAwardButton = document.querySelector('[data-license-award]');
const licenseListButton = document.querySelector('[data-license-load]');

const loadLicenses = async (driverId, discipline) => {
  if (!licenseList) return;
  licenseList.innerHTML = '<li>Loading...</li>';
  try {
    const url = discipline
      ? `/api/licenses?driver_id=${driverId}&discipline=${discipline}`
      : `/api/licenses?driver_id=${driverId}`;
    const res = await apiFetch(url);
    if (!res.ok) throw new Error('failed');
    const data = await res.json();
    if (!data.length) {
      licenseList.innerHTML = '<li>No licenses yet.</li>';
      return;
    }
    licenseList.innerHTML = data
      .map((item) => `<li>${item.level_code} / ${new Date(item.awarded_at).toLocaleDateString()}</li>`)
      .join('');
  } catch (err) {
    licenseList.innerHTML = '<li>Unable to load licenses.</li>';
  }
};

const awardLicense = async () => {
  if (!licenseForm || !licenseStatus) return;
  const driverId = getFormValue(licenseForm, '#licenseDriverId');
  const discipline = getFormValue(licenseForm, '#licenseDiscipline') || 'gt';
  if (!driverId) {
    licenseStatus.textContent = 'Driver ID required.';
    return;
  }
  licenseStatus.textContent = 'Awarding license...';
  try {
    const res = await apiFetch(`/api/licenses/award?driver_id=${driverId}&discipline=${discipline}`, {
      method: 'POST'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      licenseStatus.textContent = err.detail || 'No eligible license.';
      return;
    }
    licenseStatus.textContent = 'License awarded.';
    await loadLicenses(driverId, discipline);
  } catch (err) {
    licenseStatus.textContent = 'License award failed.';
  }
};

export const initLicenses = () => {
  if (licenseAwardButton) {
    licenseAwardButton.addEventListener('click', awardLicense);
  }
  if (licenseListButton) {
    licenseListButton.addEventListener('click', () => {
      if (!licenseForm) return;
      const driverId = getFormValue(licenseForm, '#licenseDriverId');
      const discipline = getFormValue(licenseForm, '#licenseDiscipline') || 'gt';
      if (driverId) {
        loadLicenses(driverId, discipline);
      }
    });
  }
};
