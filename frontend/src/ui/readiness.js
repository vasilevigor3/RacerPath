import { getApiKey, readinessState } from '../state/session.js';

const readinessScore = document.querySelector('[data-readiness-score]');
const readinessFill = document.querySelector('[data-readiness-fill]');
const readinessNote = document.querySelector('[data-readiness-note]');

export const resetReadiness = (message) => {
  if (readinessScore) readinessScore.textContent = '--';
  if (readinessFill) readinessFill.style.width = '0%';
  if (readinessNote) readinessNote.textContent = message;
};

export const updateReadiness = () => {
  if (!readinessScore || !readinessFill || !readinessNote) return;
  if (!getApiKey()) {
    resetReadiness('Log in to see readiness.');
    return;
  }
  if (!readinessState.hasDriver) {
    resetReadiness('Create a driver profile to unlock readiness.');
    return;
  }
  const taskRatio = readinessState.tasksTotal
    ? readinessState.tasksCompleted / readinessState.tasksTotal
    : 0;
  const score = Math.max(
    0,
    Math.min(
      100,
      Math.round(
        readinessState.crsScore * 0.5 +
          taskRatio * 100 * 0.3 +
          readinessState.profileCompletion * 0.2
      )
    )
  );
  readinessScore.textContent = `${score}`;
  readinessFill.style.width = `${score}%`;

  let note = 'Keep racing to improve readiness.';
  if (readinessState.profileCompletion < 60) {
    note = 'Profile incomplete. Finish core fields to boost readiness.';
  } else if (taskRatio < 0.4) {
    note = 'Complete more tasks to unlock higher readiness.';
  } else if (readinessState.crsScore < 70) {
    note = 'Raise CRS with clean, consistent races.';
  } else if (score >= 80) {
    note = 'Strong readiness. Target higher-tier events.';
  }
  readinessNote.textContent = note;
};
