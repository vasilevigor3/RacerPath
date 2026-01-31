import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';

const recForm = document.querySelector('[data-rec-form]');
const recStatus = document.querySelector('[data-rec-status]');
const recSummary = document.querySelector('[data-rec-summary]');
const recList = document.querySelector('[data-rec-list]');
const recComputeButton = document.querySelector('[data-rec-compute]');
const recLatestButton = document.querySelector('[data-rec-latest]');

const loadRecommendation = async (driverId, discipline) => {
  if (!recList) return;
  recList.innerHTML = '<li>Loading...</li>';
  try {
    const res = await apiFetch(`/api/recommendations/latest?driver_id=${driverId}&discipline=${discipline}`);
    if (!res.ok) throw new Error('failed');
    const data = await res.json();
    if (recSummary) recSummary.textContent = data.summary;
    recList.innerHTML = data.items.map((item) => `<li>${item}</li>`).join('');
  } catch (err) {
    if (recSummary) recSummary.textContent = 'No recommendation yet.';
    if (recList) recList.innerHTML = '<li>No recommendations.</li>';
  }
};

const computeRecommendation = async () => {
  if (!recForm || !recStatus) return;
  const driverId = getFormValue(recForm, '#recDriverId');
  const discipline = getFormValue(recForm, '#recDiscipline') || 'gt';
  if (!driverId) {
    recStatus.textContent = 'Driver ID required.';
    return;
  }
  recStatus.textContent = 'Computing recommendation...';
  try {
    const res = await apiFetch(
      `/api/recommendations/compute?driver_id=${driverId}&discipline=${discipline}`,
      { method: 'POST' }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      recStatus.textContent = err.detail || 'Recommendation failed.';
      return;
    }
    const data = await res.json();
    if (recSummary) recSummary.textContent = data.summary;
    if (recList) recList.innerHTML = data.items.map((item) => `<li>${item}</li>`).join('');
    recStatus.textContent = 'Recommendation updated.';
  } catch (err) {
    recStatus.textContent = 'Recommendation failed.';
  }
};

export const initRecommendations = () => {
  if (recComputeButton) {
    recComputeButton.addEventListener('click', computeRecommendation);
  }
  if (recLatestButton) {
    recLatestButton.addEventListener('click', () => {
      if (!recForm) return;
      const driverId = getFormValue(recForm, '#recDriverId');
      const discipline = getFormValue(recForm, '#recDiscipline') || 'gt';
      if (driverId) {
        loadRecommendation(driverId, discipline);
      }
    });
  }
};
