import { apiFetch } from '../api/client.js';
import { setList } from '../utils/dom.js';
import { formatDateTime } from '../utils/format.js';
import { readinessState } from '../state/session.js';
import { updateReadiness } from '../ui/readiness.js';
import {
  updateDriverSnapshotMeta,
  updateDriverSnapshotChallenges,
  updateDriverSnapshotRisks,
  resetDriverSnapshot
} from './driverSnapshot.js';

const statCrs = document.querySelector('[data-stat-crs]');
const statEvents = document.querySelector('[data-stat-events]');
const statTasks = document.querySelector('[data-stat-tasks]');
const statLicenses = document.querySelector('[data-stat-licenses]');
const statIncidents = document.querySelector('[data-stat-incidents]');
const dashboardParticipationsList = document.querySelector('[data-dashboard-participations]');
const riskFlagsList = document.querySelector('[data-risk-flags]');
const tasksCompletedList = document.querySelector('[data-tasks-completed]');
const tasksPendingList = document.querySelector('[data-tasks-pending]');
const recommendationList = document.querySelector('[data-recommendation-list]');
const recNextEventTitle = document.querySelector('[data-rec-next-event-title]');
const recNextEventDesc = document.querySelector('[data-rec-next-event-desc]');
const recSkillGapTitle = document.querySelector('[data-rec-skill-gap-title]');
const recSkillGapDesc = document.querySelector('[data-rec-skill-gap-desc]');
const recReadinessTitle = document.querySelector('[data-rec-readiness-title]');
const recReadinessDesc = document.querySelector('[data-rec-readiness-desc]');
const upcomingEventsList = document.querySelector('[data-upcoming-events]');
const dashboardEventsList = document.querySelector('[data-dashboard-events]');
const licenseCurrent = document.querySelector('[data-license-current]');
const licenseNext = document.querySelector('[data-license-next]');
const licenseReqs = document.querySelector('[data-license-reqs]');
const activityFeed = document.querySelector('[data-activity-feed]');

const getParticipationMinutes = (participation) => {
  if (!participation) return null;
  if (participation.duration_minutes !== null && participation.duration_minutes !== undefined) {
    return participation.duration_minutes;
  }
  if (!participation.started_at || !participation.finished_at) return null;
  const start = new Date(participation.started_at);
  const end = new Date(participation.finished_at);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  const minutes = Math.abs(Math.round((end - start) / 60000));
  return minutes;
};

export const loadDashboardStats = async (driver) => {
  if (!driver) {
    readinessState.hasDriver = false;
    readinessState.crsScore = 0;
    if (statCrs) statCrs.textContent = '--';
    if (statEvents) statEvents.textContent = '0';
    if (statTasks) statTasks.textContent = '0';
    if (statLicenses) statLicenses.textContent = '0';
    if (statIncidents) statIncidents.textContent = '0';
    if (dashboardParticipationsList) {
      setList(dashboardParticipationsList, [], 'No participations loaded.');
    }
    if (riskFlagsList) {
      setList(riskFlagsList, ['Create a driver profile to unlock stats.'], 'No risks yet.');
    }
    resetDriverSnapshot();
    updateReadiness();
    return;
  }

  readinessState.hasDriver = true;
  const discipline = driver.primary_discipline || 'gt';

  try {
    const res = await apiFetch(`/api/crs/latest?driver_id=${driver.id}&discipline=${discipline}`);
    if (res.ok) {
      const crs = await res.json();
      if (crs) {
        if (statCrs) statCrs.textContent = Math.round(crs.score);
        readinessState.crsScore = crs.score || 0;
      } else {
        if (statCrs) statCrs.textContent = '--';
        readinessState.crsScore = 0;
      }
    } else {
      if (statCrs) statCrs.textContent = '--';
      readinessState.crsScore = 0;
    }
  } catch (err) {
    if (statCrs) statCrs.textContent = '--';
    readinessState.crsScore = 0;
  }

  let participations = [];
  try {
    const res = await apiFetch(`/api/participations?driver_id=${driver.id}`);
    if (res.ok) {
      participations = await res.json();
    }
  } catch (err) {
    participations = [];
  }

  if (statEvents) statEvents.textContent = participations.length.toString();
  const incidentTotal = participations.reduce((sum, item) => sum + (item.incidents_count || 0), 0);
  if (statIncidents) statIncidents.textContent = incidentTotal.toString();

  if (dashboardParticipationsList) {
    const items = participations.slice(0, 5).map((item) => {
      return `${item.discipline.toUpperCase()} - ${item.status} / ${item.event_id.slice(0, 8)}...`;
    });
    setList(dashboardParticipationsList, items, 'No participations loaded.');
  }

  const riskFlags = [];
  if (participations.length === 0) {
    riskFlags.push('No participation data yet.');
  } else {
    const avgIncidents = incidentTotal / participations.length;
    const dnfRate =
      participations.filter((item) => item.status === 'dnf' || item.status === 'dsq').length /
      participations.length;
    if (avgIncidents > 1.5) riskFlags.push('High incident rate - prioritize clean races.');
    if (dnfRate > 0.2) riskFlags.push('DNF rate above 20% - focus on finishing.');
    if (avgIncidents <= 1.5 && dnfRate <= 0.2) riskFlags.push('No critical risks detected.');
  }
  if (riskFlagsList) setList(riskFlagsList, riskFlags, 'No risks yet.');
  updateDriverSnapshotRisks(riskFlags);
  updateDriverSnapshotMeta({
    name: driver.name,
    discipline: driver.primary_discipline,
    description: riskFlags[0] || 'Focus on clean finishes and consistent races.',
    readinessPercent: readinessState.profileCompletion,
    readinessMetaText:
      riskFlags.length > 0
        ? riskFlags[0]
        : 'Keep pushing through tasks to keep the momentum.',
    crsScore: readinessState.crsScore,
    tasksCompleted: readinessState.tasksCompleted,
    tasksTotal: readinessState.tasksTotal
  });

  try {
    const res = await apiFetch(`/api/licenses?driver_id=${driver.id}`);
    if (res.ok) {
      const licenses = await res.json();
      if (statLicenses) statLicenses.textContent = licenses.length.toString();
    } else if (statLicenses) {
      statLicenses.textContent = '0';
    }
  } catch (err) {
    if (statLicenses) statLicenses.textContent = '0';
  }

  updateReadiness();
};

export const loadTasksOverview = async (driver) => {
  if (!driver) {
    if (tasksCompletedList) setList(tasksCompletedList, [], 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, [], 'No pending tasks.');
    if (statTasks) statTasks.textContent = '0';
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    updateReadiness();
    return;
  }
  const discipline = driver.primary_discipline || 'gt';
  try {
    const [completionsRes, definitionsRes] = await Promise.all([
      apiFetch(`/api/tasks/completions?driver_id=${driver.id}`),
      apiFetch('/api/tasks/definitions')
    ]);
    const completions = completionsRes.ok ? await completionsRes.json() : [];
    const definitions = definitionsRes.ok ? await definitionsRes.json() : [];
    const completedIds = new Set(completions.map((item) => item.task_id));
    const filteredDefinitions = definitions.filter((task) => task.discipline === discipline);
    const completedNames = filteredDefinitions
      .filter((task) => completedIds.has(task.id))
      .map((task) => task.name);
    const pendingNames = filteredDefinitions
      .filter((task) => !completedIds.has(task.id))
      .map((task) => task.name);

    if (tasksCompletedList) setList(tasksCompletedList, completedNames, 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, pendingNames.slice(0, 6), 'No pending tasks.');
    if (statTasks) statTasks.textContent = completedNames.length.toString();
    readinessState.tasksCompleted = completedNames.length;
    readinessState.tasksTotal = filteredDefinitions.length;
    updateDriverSnapshotChallenges(pendingNames);
    updateReadiness();
  } catch (err) {
    if (tasksCompletedList) setList(tasksCompletedList, [], 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, [], 'No pending tasks.');
    if (statTasks) statTasks.textContent = '0';
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    updateDriverSnapshotChallenges([]);
    updateReadiness();
  }
};

const READINESS_LABELS = { ready: 'Ready', almost_ready: 'Almost ready', not_ready: 'Not ready' };

const updateRecommendationCards = (data) => {
  const set = (el, text) => { if (el) el.textContent = text ?? '—'; };
  if (!data) {
    set(recNextEventTitle, '—');
    set(recNextEventDesc, 'Load profile to see recommended event.');
    set(recSkillGapTitle, '—');
    set(recSkillGapDesc, 'Load profile to see next skill focus.');
    set(recReadinessTitle, '—');
    set(recReadinessDesc, 'Load profile to see readiness.');
    return;
  }
  const items = data.items || [];
  const nextEvent = items.find((i) => typeof i === 'string' && i.startsWith('Race next:'));
  const skillItem = items.find(
    (i) => typeof i === 'string' && (i.startsWith('Complete task:') || i.startsWith('Risk:'))
  );
  set(recNextEventTitle, nextEvent ? nextEvent.replace(/^Race next:\s*/, '').trim() : '—');
  set(recNextEventDesc, nextEvent ? 'Add to your plan from events.' : 'No recommended event yet.');
  if (skillItem) {
    const isTask = skillItem.startsWith('Complete task:');
    set(recSkillGapTitle, isTask ? skillItem.replace(/^Complete task:\s*/, '').trim() : 'Risk');
    set(recSkillGapDesc, skillItem);
  } else {
    set(recSkillGapTitle, '—');
    set(recSkillGapDesc, 'No skill gap highlighted.');
  }
  set(recReadinessTitle, READINESS_LABELS[data.readiness_status] ?? data.readiness_status ?? '—');
  set(recReadinessDesc, data.summary || '');
};

export const loadDashboardRecommendations = async (driver) => {
  if (!recommendationList) return;
  if (!driver) {
    setList(recommendationList, ['Log in and create a driver profile to see next steps.'], '');
    updateRecommendationCards(null);
    return;
  }
  try {
    const discipline = driver.primary_discipline || 'gt';
    const res = await apiFetch(`/api/recommendations/latest?driver_id=${driver.id}&discipline=${discipline}`);
    if (!res.ok) {
      setList(recommendationList, ['No recommendations yet. Compute one in Dashboards.'], '');
      updateRecommendationCards(null);
      return;
    }
    const data = await res.json();
    if (data) {
      setList(recommendationList, data.items || [], 'No recommendations yet.');
      updateRecommendationCards(data);
    } else {
      setList(recommendationList, ['No recommendations yet. Compute one in Dashboards.'], '');
      updateRecommendationCards(null);
    }
  } catch (err) {
    setList(recommendationList, ['Unable to load recommendations.'], '');
    updateRecommendationCards(null);
  }
};

export const loadLicenseProgress = async (driver) => {
  if (!licenseCurrent || !licenseNext || !licenseReqs) return;
  if (!driver) {
    licenseCurrent.textContent = '--';
    licenseNext.textContent = '--';
    setList(licenseReqs, [], 'Create a driver profile to see license progress.');
    return;
  }
  try {
    const discipline = driver.primary_discipline || 'gt';
    const [latestRes, reqRes] = await Promise.all([
      apiFetch(`/api/licenses/latest?driver_id=${driver.id}&discipline=${discipline}`),
      apiFetch(`/api/licenses/requirements?discipline=${discipline}&driver_id=${driver.id}`)
    ]);
    const latest = latestRes.ok ? await latestRes.json() : null;
    const requirements = reqRes.ok ? await reqRes.json() : null;
    if (latest) {
      licenseCurrent.textContent = latest.level_code;
    } else {
      licenseCurrent.textContent = 'None';
    }
    if (requirements) {
      licenseNext.textContent = requirements.next_level || '--';
      setList(licenseReqs, requirements.requirements || [], 'No requirements loaded.');
    } else {
      licenseNext.textContent = '--';
      setList(licenseReqs, ['Maintain performance to keep license.'], '');
    }
  } catch (err) {
    licenseCurrent.textContent = '--';
    licenseNext.textContent = '--';
    setList(licenseReqs, [], 'Unable to load license progress.');
  }
};

export const loadActivityFeed = async (driver) => {
  if (!activityFeed) return;
  if (!driver) {
    setList(activityFeed, [], 'Create a driver profile to see activity.');
    return;
  }
  try {
    const res = await apiFetch(`/api/participations?driver_id=${driver.id}`);
    if (!res.ok) throw new Error('failed');
    const participations = await res.json();
    const items = participations.slice(0, 6).map((participation) => {
      const duration = getParticipationMinutes(participation);
      const durationLabel = duration ? `${duration}m` : 'Duration n/a';
      const incidentLabel = participation.incidents_count ? ` / ${participation.incidents_count} incidents` : '';
      const title = participation.event_title || participation.event_id.slice(0, 8);
      const statusLabel = participation.status ? participation.status.toUpperCase() : 'FINISHED';
      return `${title} • ${statusLabel} • ${durationLabel}${incidentLabel}`;
    });
    setList(activityFeed, items, 'No activity yet.');
  } catch (err) {
    setList(activityFeed, [], 'Unable to load activity.');
  }
};

export const loadDashboardEvents = async (driver) => {
  if (!dashboardEventsList && !upcomingEventsList) return;
  if (!driver) {
    if (dashboardEventsList) setList(dashboardEventsList, [], 'Log in to load events.');
    if (upcomingEventsList) setList(upcomingEventsList, [], 'Log in to load events.');
    return;
  }
  try {
    const res = await apiFetch('/api/events');
    if (!res.ok) throw new Error('failed');
    let events = await res.json();

    // Filter: only events for driver's selected sim games (if any)
    if (driver.sim_games && driver.sim_games.length) {
      events = events.filter((event) => event.game && driver.sim_games.includes(event.game));
    }

    const withStart = events
      .filter((event) => event.start_time_utc)
      .sort((a, b) => new Date(a.start_time_utc) - new Date(b.start_time_utc));
    const now = new Date();
    const upcoming = withStart.filter((event) => new Date(event.start_time_utc) > now).slice(0, 3);
    const fallback = events.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));

    const formatEventItem = (event) => {
      const gameLabel = event.game ? ` / ${event.game}` : '';
      const timeLabel = event.start_time_utc ? ` • ${formatDateTime(event.start_time_utc)}` : '';
      return `${event.title} - ${event.format_type}${gameLabel}${timeLabel}`;
    };

    const dashboardItems = (withStart.length ? withStart : fallback).slice(0, 5).map(formatEventItem);
    const upcomingItems = upcoming.map(formatEventItem);

    if (dashboardEventsList) {
      const emptyText = driver.sim_games && driver.sim_games.length
        ? 'No events for your games yet.'
        : 'Add sim games to see events.';
      setList(dashboardEventsList, dashboardItems, emptyText);
    }
    if (upcomingEventsList) {
      const emptyText = driver.sim_games && driver.sim_games.length
        ? 'No upcoming events for your games.'
        : 'No upcoming events. Add sim games to see events.';
      setList(upcomingEventsList, upcomingItems, emptyText);
    }
  } catch (err) {
    if (dashboardEventsList) {
      setList(dashboardEventsList, [], 'Unable to load events.');
    }
    if (upcomingEventsList) {
      setList(upcomingEventsList, [], 'Unable to load events.');
    }
  }
};
