import { apiFetch } from '../api/client.js';
import { setList, setEventListWithRegister, setRecommendationListWithCountdown, tickRecommendationCountdowns } from '../utils/dom.js';
import { formatDateTime, formatCountdown } from '../utils/format.js';
import { eventGameMatchesDriverGames } from '../utils/gameAliases.js';
import { readinessState } from '../state/session.js';
import { updateReadiness } from '../ui/readiness.js';
import { updateDriverSnapshotMeta, resetDriverSnapshot } from './driverSnapshot.js';

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
const currentRaceCard = document.querySelector('[data-current-race-card]');
const currentRaceEvent = document.querySelector('[data-current-race-event]');
const currentRacePosition = document.querySelector('[data-current-race-position]');
const currentRaceLaps = document.querySelector('[data-current-race-laps]');
const currentRacePenalties = document.querySelector('[data-current-race-penalties]');
const currentRaceIncidents = document.querySelector('[data-current-race-incidents]');
let recommendationCountdownInterval = null;
let activeRacePollInterval = null;
const ACTIVE_RACE_POLL_MS = 5000;

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
    lastDriverParticipations = [];
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
  lastDriverParticipations = participations;

  if (statEvents) statEvents.textContent = participations.length.toString();
  const incidentTotal = participations.reduce((sum, item) => sum + (item.incidents_count || 0), 0);
  if (statIncidents) statIncidents.textContent = incidentTotal.toString();

  if (dashboardParticipationsList) {
    const items = participations.slice(0, 10).map((item) => {
      const state = item.participation_state ?? item.status ?? '—';
      return `${item.discipline?.toUpperCase() ?? '—'} - ${state} / ${(item.event_id || '').slice(0, 8)}...`;
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
    updateReadiness();
  } catch (err) {
    if (tasksCompletedList) setList(tasksCompletedList, [], 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, [], 'No pending tasks.');
    if (statTasks) statTasks.textContent = '0';
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
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
  if (recommendationCountdownInterval) {
    clearInterval(recommendationCountdownInterval);
    recommendationCountdownInterval = null;
  }
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
    let data;
    try {
      data = await res.json();
    } catch (parseErr) {
      setList(recommendationList, ['Unable to load recommendations (invalid response).'], '');
      updateRecommendationCards(null);
      return;
    }
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      if (recommendationCountdownInterval) {
        clearInterval(recommendationCountdownInterval);
        recommendationCountdownInterval = null;
      }
      setRecommendationListWithCountdown(
        recommendationList,
        data.items || [],
        data.special_events || [],
        'No recommendations yet.',
        formatCountdown
      );
      recommendationCountdownInterval = setInterval(() => {
        tickRecommendationCountdowns(recommendationList, formatCountdown);
      }, 1000);
      updateRecommendationCards(data);
    } else {
      setList(recommendationList, ['No recommendations yet. Compute one in Dashboards.'], '');
      updateRecommendationCards(null);
    }
  } catch (err) {
    console.warn('loadDashboardRecommendations failed:', err);
    setList(recommendationList, ['Unable to load recommendations.'], '');
    updateRecommendationCards(null);
  }
};

export const loadLicenseProgress = async (driver) => {
  if (!licenseCurrent || !licenseNext || !licenseReqs) return;
  if (!driver) {
    lastDriverLicenseLevel = null;
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
    lastDriverLicenseLevel = latest?.level_code ?? null;
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
    lastDriverLicenseLevel = null;
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

let lastDriverForEvents = null;
let lastDriverForActiveRace = null;
let lastDashboardEventsData = [];
let lastDriverParticipations = [];
let lastDriverLicenseLevel = null;

const EVENT_STATUS_LABELS = { waiting_start: 'Waiting to start', started: 'Started', finished: 'Finished' };

const LICENSE_REQUIREMENT_RANK = { none: 0, entry: 1, rookie: 2, intermediate: 3, pro: 4 };

const getEventStatus = (event, now = Date.now()) => {
  if (!event?.start_time_utc) return null;
  const startMs = new Date(event.start_time_utc).getTime();
  if (Number.isNaN(startMs)) return null;
  if (now < startMs) return 'waiting_start';
  if (event.finished_time_utc != null) {
    const finishedMs = new Date(event.finished_time_utc).getTime();
    if (!Number.isNaN(finishedMs) && now >= finishedMs) return 'finished';
  }
  return 'started';
};

function showEventDetail(event, driver) {
  const listView = document.querySelector('[data-events-list-view]');
  const panel = document.querySelector('[data-event-detail-panel]');
  const content = document.querySelector('[data-event-detail-content]');
  const registerBtn = document.querySelector('[data-event-detail-register]');
  const actionsEl = document.querySelector('[data-event-detail-actions]');
  if (!listView || !panel || !content) return;
  const eventTier = (event.event_tier ?? 'E2').toUpperCase();
  const driverTier = (driver?.tier ?? 'E0').toUpperCase();
  const tierMatch = eventTier === driverTier;
  const reqLicense = (event.license_requirement ?? 'none').toLowerCase();
  const reqRank = LICENSE_REQUIREMENT_RANK[reqLicense] ?? 0;
  const driverLicenseRank = reqRank === 0 ? 1 : (LICENSE_REQUIREMENT_RANK[(lastDriverLicenseLevel ?? '').toLowerCase()] ?? 0);
  const licenseOk = reqRank === 0 || driverLicenseRank >= reqRank;
  const alreadyRegistered = lastDriverParticipations.some((p) => p.event_id === event.id);
  const canRegister = tierMatch && licenseOk && !alreadyRegistered;
  const status = getEventStatus(event);
  const statusLabel = status ? EVENT_STATUS_LABELS[status] : '—';
  content.innerHTML = `
    <dl class="event-detail-dl">
      <div><dt>Title</dt><dd>${escapeHtml(event.title ?? '—')}</dd></div>
      <div><dt>Session</dt><dd>${escapeHtml(event.session_type === 'training' ? 'Training' : 'Race')}</dd></div>
      <div><dt>Format</dt><dd>${escapeHtml(event.format_type ?? '—')}</dd></div>
      <div><dt>Game</dt><dd>${escapeHtml(event.game ?? '—')}</dd></div>
      <div><dt>Start (UTC)</dt><dd>${event.start_time_utc ? formatDateTime(event.start_time_utc) : '—'}</dd></div>
      <div><dt>Finish (UTC)</dt><dd>${event.finished_time_utc ? formatDateTime(event.finished_time_utc) : '—'}</dd></div>
      <div><dt>Status</dt><dd>${escapeHtml(statusLabel)}</dd></div>
      <div><dt>Tier</dt><dd>${escapeHtml(eventTier)}</dd></div>
      ${event.country ? `<div><dt>Country</dt><dd>${escapeHtml(event.country)}</dd></div>` : ''}
      ${event.city ? `<div><dt>City</dt><dd>${escapeHtml(event.city)}</dd></div>` : ''}
    </dl>
  `;
  if (registerBtn) {
    registerBtn.disabled = !canRegister;
    registerBtn.dataset.eventId = event.id;
    registerBtn.dataset.driverId = driver?.id ?? '';
  }
  if (actionsEl) {
    actionsEl.classList.toggle('is-hidden', !canRegister);
  }
  listView.classList.add('is-hidden');
  panel.classList.remove('is-hidden');
}

function hideEventDetail() {
  const listView = document.querySelector('[data-events-list-view]');
  const panel = document.querySelector('[data-event-detail-panel]');
  if (listView) listView.classList.remove('is-hidden');
  if (panel) panel.classList.add('is-hidden');
}

function escapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const registerOnEvent = async (driverId, eventId) => {
  const driver = lastDriverForEvents;
  if (!driver || driver.id !== driverId) return;
  const discipline = driver.primary_discipline || 'gt';
  try {
    const res = await apiFetch('/api/participations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        driver_id: driverId,
        event_id: eventId,
        discipline,
        participation_state: 'registered',
        status: 'dns',
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = Array.isArray(err.detail) ? err.detail.map((d) => d.msg).join(', ') : (err.detail || 'Register failed.');
      if (typeof window !== 'undefined' && window.alert) window.alert(msg);
      return;
    }
    hideEventDetail();
    if (lastDriverForEvents) {
      await loadDashboardStats(lastDriverForEvents);
      await loadDashboardEvents(lastDriverForEvents);
    }
  } catch (err) {
    if (typeof window !== 'undefined' && window.alert) window.alert('Register failed.');
  }
};

function initDashboardEventsRegisterDelegation() {
  if (document.body.dataset.dashboardEventsRegisterDelegation) return;
  document.body.dataset.dashboardEventsRegisterDelegation = '1';
  document.body.addEventListener('click', (e) => {
    const list = e.target.closest('[data-dashboard-events]');
    const textBtn = list ? e.target.closest('.event-list-item__text') : null;
    if (textBtn && list) {
      e.preventDefault();
      const eventId = textBtn.getAttribute('data-event-id');
      const driver = lastDriverForEvents;
      if (!eventId || !driver) return;
      const event = lastDashboardEventsData.find((ev) => ev.id === eventId);
      if (event) showEventDetail(event, driver);
      return;
    }
    const backBtn = e.target.closest('[data-event-detail-back]');
    if (backBtn) {
      e.preventDefault();
      hideEventDetail();
      return;
    }
    const registerBtn = e.target.closest('.btn-register-event-panel:not([disabled])');
    if (registerBtn) {
      e.preventDefault();
      const eventId = registerBtn.dataset.eventId;
      const driverId = registerBtn.dataset.driverId;
      if (eventId && driverId) registerOnEvent(driverId, eventId);
    }
  });
}

const setCurrentRaceCard = (data) => {
  if (!currentRaceCard) return;
  if (!data) {
    currentRaceCard.style.display = 'none';
    return;
  }
  currentRaceCard.style.display = '';
  if (currentRaceEvent) currentRaceEvent.textContent = data.event_title || 'Current race';
  if (currentRacePosition) {
    const pos = data.position_overall ?? data.position_class;
    currentRacePosition.textContent = `Position: ${pos != null ? pos : '—'}`;
  }
  if (currentRaceLaps) currentRaceLaps.textContent = `Laps: ${data.laps_completed ?? 0}`;
  if (currentRacePenalties) currentRacePenalties.textContent = `Penalties: ${data.penalties_count ?? 0}`;
  if (currentRaceIncidents) currentRaceIncidents.textContent = `Incidents: ${data.incidents_count ?? 0}`;
};

const fetchActiveRace = async (driver) => {
  if (!driver) return null;
  const res = await apiFetch(`/api/participations/active?driver_id=${driver.id}`);
  if (!res.ok || res.status === 204) return null;
  const data = await res.json().catch(() => null);
  return data || null;
};

export const loadActiveRace = async (driver) => {
  if (activeRacePollInterval) {
    clearInterval(activeRacePollInterval);
    activeRacePollInterval = null;
  }
  lastDriverForActiveRace = driver;
  if (!driver || !currentRaceCard) {
    setCurrentRaceCard(null);
    return;
  }
  const data = await fetchActiveRace(driver);
  setCurrentRaceCard(data ?? null);
  if (data) {
    activeRacePollInterval = setInterval(async () => {
      if (lastDriverForActiveRace?.id !== driver.id) return;
      const next = await fetchActiveRace(driver);
      if (!next) {
        if (activeRacePollInterval) clearInterval(activeRacePollInterval);
        activeRacePollInterval = null;
        setCurrentRaceCard(null);
        return;
      }
      setCurrentRaceCard(next);
    }, ACTIVE_RACE_POLL_MS);
  }
};

export const loadDashboardEvents = async (driver) => {
  if (!dashboardEventsList && !upcomingEventsList) return;
  if (!driver) {
    lastDriverForEvents = null;
    lastDashboardEventsData = [];
    hideEventDetail();
    loadActiveRace(null);
    if (dashboardEventsList) setList(dashboardEventsList, [], 'Log in to load events.');
    if (upcomingEventsList) setList(upcomingEventsList, [], 'Log in to load events.');
    return;
  }
  lastDriverForEvents = driver;
  const sameTierCheckbox = document.querySelector('[data-events-same-tier]');
  const sameTier = sameTierCheckbox?.checked ?? false;
  if (sameTierCheckbox && !sameTierCheckbox.dataset.listenerAttached) {
    sameTierCheckbox.dataset.listenerAttached = '1';
    sameTierCheckbox.addEventListener('change', () => {
      if (lastDriverForEvents) loadDashboardEvents(lastDriverForEvents);
    });
  }
  const now = Date.now();
  const formatEventItem = (event, forRecent = false) => {
    const sessionLabel = event.session_type === 'training' ? 'Training' : 'Race';
    const gameLabel = event.game ? ` / ${event.game}` : '';
    const timeLabel = event.start_time_utc ? ` • ${formatDateTime(event.start_time_utc)}` : '';
    let statusSuffix = '';
    if (forRecent && event.start_time_utc) {
      const status = getEventStatus(event);
      if (status) statusSuffix = ` • ${EVENT_STATUS_LABELS[status]}`;
    }
    return `${event.title} · ${sessionLabel} · ${event.format_type}${gameLabel}${timeLabel}${statusSuffix}`;
  };
  try {
    const eventsUrl = `/api/events?driver_id=${driver.id}&same_tier=${sameTier}`;
    const [eventsRes, upcomingRes] = await Promise.all([
      apiFetch(eventsUrl),
      apiFetch(`/api/events/upcoming?driver_id=${driver.id}&discipline=${driver.primary_discipline || 'gt'}`),
    ]);
    if (!eventsRes.ok) throw new Error('failed');
    const events = await eventsRes.json();

    const waitingOrUpcoming = events.filter((e) => {
      if (!e.start_time_utc) return false;
      const startMs = new Date(e.start_time_utc).getTime();
      return !Number.isNaN(startMs) && startMs > now;
    });
    const dashboardEventsData = [...waitingOrUpcoming]
      .sort((a, b) => new Date(a.start_time_utc).getTime() - new Date(b.start_time_utc).getTime())
      .slice(0, 5);
    lastDashboardEventsData = dashboardEventsData;

    let upcomingItems = [];
    if (upcomingRes.ok) {
      const upcomingEvents = await upcomingRes.json();
      upcomingItems = (Array.isArray(upcomingEvents) ? upcomingEvents : []).map((e) => formatEventItem(e, true));
    }

    if (dashboardEventsList) {
      const emptyText = driver.sim_games && driver.sim_games.length
        ? 'No upcoming events (waiting to start).'
        : 'Add sim games to see events.';
      setEventListWithRegister(dashboardEventsList, dashboardEventsData, driver, emptyText, formatEventItem);
    }
    if (upcomingEventsList) {
      const emptyText = driver.sim_games && driver.sim_games.length
        ? 'No upcoming events for your games.'
        : 'No upcoming events. Add sim games to see events.';
      setList(upcomingEventsList, upcomingItems, emptyText);
    }
    loadActiveRace(driver);
  } catch (err) {
    if (dashboardEventsList) {
      setList(dashboardEventsList, [], 'Unable to load events.');
    }
    if (upcomingEventsList) {
      setList(upcomingEventsList, [], 'Unable to load events.');
    }
  }
};

if (typeof document !== 'undefined') {
  initDashboardEventsRegisterDelegation();
}
