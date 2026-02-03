import { apiFetch } from '../api/client.js';
import { getApiKey, getCurrentUserName, setCurrentDriverId, getMyDrivers } from '../state/session.js';
import { getSimGames } from '../utils/forms.js';
import { loadProfile } from './profile.js';
import { DISCIPLINES } from '../constants/uiData.js';

const myDriverForm = document.querySelector('[data-my-driver-form]');
const myDriverStatus = document.querySelector('[data-my-driver-status]');

/** When adding another career, show only disciplines the user doesn't have yet. */
export const updateOnboardingDisciplineOptions = () => {
  const select = document.querySelector('#myDriverDiscipline');
  if (!select) return;
  const myDrivers = getMyDrivers();
  const used = new Set(myDrivers.map((d) => d.primary_discipline));
  const available = DISCIPLINES.filter((d) => !used.has(d.value));
  select.innerHTML = '';
  available.forEach((d) => {
    const opt = document.createElement('option');
    opt.value = d.value;
    opt.textContent = d.label;
    select.appendChild(opt);
  });
  if (available.length && !select.value) select.value = available[0].value;
};

export const initOnboarding = () => {
  if (!myDriverForm || !myDriverStatus) return;
  myDriverForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!getApiKey()) {
      myDriverStatus.textContent = 'Log in first.';
      return;
    }
    const nameInput = myDriverForm.querySelector('#myDriverName');
    const disciplineInput = myDriverForm.querySelector('#myDriverDiscipline');
    let name = nameInput ? nameInput.value.trim() : '';
    if (!name && getCurrentUserName()) {
      name = getCurrentUserName();
    }
    if (!name) {
      myDriverStatus.textContent = 'Driver name required.';
      return;
    }
    const simGames = getSimGames(myDriverForm);
    if (!simGames.length) {
      myDriverStatus.textContent = 'Select at least one sim game.';
      return;
    }
    myDriverStatus.textContent = 'Creating driver...';
    try {
      const res = await apiFetch('/api/drivers/me', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          primary_discipline: disciplineInput ? disciplineInput.value : 'gt',
          sim_games: simGames
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        myDriverStatus.textContent = err.detail || 'Driver create failed.';
        return;
      }
      const created = await res.json();
      if (created && created.id) setCurrentDriverId(created.id);
      if (nameInput) nameInput.value = '';
      myDriverStatus.textContent = 'Driver profile created.';
      await loadProfile();
    } catch (err) {
      myDriverStatus.textContent = 'Driver create failed.';
    }
  });
};
