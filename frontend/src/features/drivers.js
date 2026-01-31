import { apiFetch } from '../api/client.js';
import { getSimGames } from '../utils/forms.js';

const driverForm = document.querySelector('[data-driver-form]');
const driverStatus = document.querySelector('[data-driver-status]');
const driverList = document.querySelector('[data-driver-list]');

export const loadDrivers = async () => {
  if (!driverList) return;
  driverList.innerHTML = '<li>Loading...</li>';
  try {
    const res = await apiFetch('/api/drivers');
    if (!res.ok) throw new Error('failed');
    const drivers = await res.json();
    if (!drivers.length) {
      driverList.innerHTML = '<li>No drivers yet.</li>';
      return;
    }
    driverList.innerHTML = drivers
      .slice(0, 5)
      .map((driver) => {
        const games = driver.sim_games && driver.sim_games.length ? driver.sim_games.join(', ') : 'No games';
        return `<li><strong>${driver.name}</strong> - ${driver.primary_discipline} (${games})</li>`;
      })
      .join('');
  } catch (err) {
    driverList.innerHTML = '<li>Unable to load drivers.</li>';
  }
};

export const initDrivers = () => {
  if (!driverForm || !driverStatus) return;
  driverForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const nameInput = driverForm.querySelector('#driverName');
    const disciplineInput = driverForm.querySelector('#driverDiscipline');
    const name = nameInput ? nameInput.value.trim() : '';
    if (!name) {
      driverStatus.textContent = 'Please enter a driver name.';
      return;
    }
    const simGames = getSimGames(driverForm);
    if (!simGames.length) {
      driverStatus.textContent = 'Select at least one sim game.';
      return;
    }
    driverStatus.textContent = 'Saving driver...';
    try {
      const res = await apiFetch('/api/drivers', {
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
        driverStatus.textContent = err.detail || 'Save failed.';
        return;
      }
      if (nameInput) nameInput.value = '';
      driverStatus.textContent = 'Driver saved.';
      await loadDrivers();
    } catch (err) {
      driverStatus.textContent = 'Save failed.';
    }
  });
};
