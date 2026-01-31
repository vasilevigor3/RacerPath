import { setList } from '../utils/dom.js';
import { fmt } from '../utils/format.js';

const snapshotSection = document.querySelector('[data-driver-snapshot-section]');
const titleEl = document.querySelector('[data-driver-snapshot-name]');
const subtitleEl = document.querySelector('[data-driver-snapshot-description]');
const subtitleHeading = document.querySelector('[data-driver-snapshot-subtitle]');
const pillCrs = document.querySelector('[data-driver-snapshot-pill-crs]');
const pillProfile = document.querySelector('[data-driver-snapshot-pill-profile]');
const pillTasks = document.querySelector('[data-driver-snapshot-pill-tasks]');
const progressFill = document.querySelector('[data-driver-snapshot-progress]');
const progressMeta = document.querySelector('[data-driver-snapshot-progress-meta]');
const challengesList = document.querySelector('[data-driver-snapshot-challenges]');
const risksList = document.querySelector('[data-driver-snapshot-risks]');

const fallbackDescription = 'Behavior and consistency dominate readiness, not just pace.';

const ensureSection = () => {
  if (!snapshotSection) return;
  snapshotSection.classList.remove('is-hidden');
};

export const updateDriverSnapshotChallenges = (items) => {
  if (!challengesList) return;
  setList(challengesList, items.slice(0, 5), 'No active challenges yet.');
};

export const updateDriverSnapshotRisks = (items) => {
  if (!risksList) return;
  setList(risksList, items.slice(0, 5), 'No risks detected.');
};

export const updateDriverSnapshotMeta = ({
  name,
  discipline,
  description,
  readinessPercent,
  readinessMetaText,
  crsScore,
  tasksCompleted,
  tasksTotal
}) => {
  ensureSection();
  if (titleEl) {
    const disciplinePart = discipline ? ` - ${discipline}` : '';
    titleEl.textContent = `${name || 'Driver'}${disciplinePart}`;
  }
  if (subtitleEl) {
    subtitleEl.textContent = description || fallbackDescription;
  }
  if (subtitleHeading) {
    subtitleHeading.textContent = description || fallbackDescription;
  }
  if (pillCrs) {
    const value = crsScore !== null && crsScore !== undefined ? fmt(crsScore) : '--';
    pillCrs.textContent = `CRS ${value}`;
  }
  if (pillProfile) {
    const value = readinessPercent ?? 0;
    pillProfile.textContent = `Profile ${Math.round(value)}%`;
  }
  if (pillTasks) {
    const total = tasksTotal || 0;
    const completed = tasksCompleted || 0;
    pillTasks.textContent = `Tasks ${completed}/${total || '--'}`;
  }
  if (progressFill) {
    const width = Math.max(0, Math.min(100, readinessPercent || 0));
    progressFill.style.width = `${width}%`;
  }
  if (progressMeta) {
    progressMeta.textContent = readinessMetaText || 'Keep working through challenges to improve readiness.';
  }
};

export const resetDriverSnapshot = () => {
  if (snapshotSection) snapshotSection.classList.add('is-hidden');
  if (titleEl) titleEl.textContent = '--';
  if (subtitleEl) subtitleEl.textContent = fallbackDescription;
  if (subtitleHeading) subtitleHeading.textContent = fallbackDescription;
  if (pillCrs) pillCrs.textContent = 'CRS --';
  if (pillProfile) pillProfile.textContent = 'Profile --%';
  if (pillTasks) pillTasks.textContent = 'Tasks 0/0';
  if (progressFill) progressFill.style.width = '0%';
  if (progressMeta) progressMeta.textContent = 'Complete your profile to unlock readiness.';
  updateDriverSnapshotChallenges([]);
  updateDriverSnapshotRisks([]);
};
