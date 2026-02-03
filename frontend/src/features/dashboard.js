import { apiFetch } from '../api/client.js';
import { setList, setLicenseReqsList, setEventListWithRegister, setTaskListClickable, setRecommendationTasksList, setRecommendationRacesList, tickRecommendationCountdowns } from '../utils/dom.js';
import { formatDateTime, formatCountdown } from '../utils/format.js';
import { eventGameMatchesDriverGames } from '../utils/gameAliases.js';
import { driverRigSatisfiesEvent } from '../utils/rigCompat.js';
import { readinessState } from '../state/session.js';
import { updateReadiness } from '../ui/readiness.js';
import { updateDriverSnapshotMeta, resetDriverSnapshot } from './driverSnapshot.js';

const statCrs = document.querySelector('[data-stat-crs]');
const statEvents = document.querySelector('[data-stat-events]');
const statTasks = document.querySelector('[data-stat-tasks]');
const statLicenses = document.querySelector('[data-stat-licenses]');
const statIncidents = document.querySelector('[data-stat-incidents]');
const statRiskFlags = document.querySelector('[data-stat-risk-flags]');
const dashboardParticipationsList = document.querySelector('[data-dashboard-participations]');
const participationScrollEl = document.querySelector('[data-participation-scroll]');
const dashboardParticipationsListView = document.querySelector('[data-dashboard-participations-list-view]');
const participationDetailPanel = document.querySelector('[data-participation-detail]');
const participationDetailEvent = document.querySelector('[data-participation-detail-event]');
const participationDetailMeta = document.querySelector('[data-participation-detail-meta]');
const participationDetailStats = document.querySelector('[data-participation-detail-stats]');
const participationDetailBack = document.querySelector('[data-participation-detail-back]');
const riskFlagsTabList = document.querySelector('[data-risk-flags-tab-list]');
const riskFlagsDetailPanel = document.querySelector('[data-risk-flags-detail]');
const riskFlagsListView = document.querySelector('[data-risk-flags-list-view]');
const tasksCompletedList = document.querySelector('[data-tasks-completed]');
const tasksPendingList = document.querySelector('[data-tasks-pending]');
const tasksInProgressList = document.querySelector('[data-tasks-in-progress]');
const recommendationTasksList = document.querySelector('[data-recommendation-tasks]');
const recommendationRacesList = document.querySelector('[data-recommendation-races]');
const recNextEventTitle = document.querySelector('[data-rec-next-event-title]');
const recNextEventDesc = document.querySelector('[data-rec-next-event-desc]');
const recSkillGapTitle = document.querySelector('[data-rec-skill-gap-title]');
const recSkillGapDesc = document.querySelector('[data-rec-skill-gap-desc]');
const recReadinessTitle = document.querySelector('[data-rec-readiness-title]');
const recReadinessDesc = document.querySelector('[data-rec-readiness-desc]');
const upcomingEventsList = document.querySelector('[data-upcoming-events]');
const dashboardEventsList = document.querySelector('[data-dashboard-events]');
const dashboardPastEventsList = document.querySelector('[data-dashboard-past-events]');
const upcomingEventsScrollEl = document.querySelector('[data-upcoming-events-scroll]');
const pastEventsScrollEl = document.querySelector('[data-past-events-scroll]');
const licenseCurrent = document.querySelector('[data-license-current]');
const licenseNext = document.querySelector('[data-license-next]');
const licenseReqs = document.querySelector('[data-license-reqs]');
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

function renderParticipationCard(item) {
  const state = item.participation_state ?? item.status ?? '—';
  const title = item.event_title || (item.event_id ? `${String(item.event_id).slice(0, 8)}…` : '—');
  const sub = item.position_overall != null ? `P${item.position_overall}` : state;
  const safe = (s) => (s == null ? '' : String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'));
  return `<button type="button" class="participation-card" data-participation-id="${safe(item.id)}" role="listitem">
    <span class="participation-card__title">${safe(title)}</span>
    <span class="participation-card__meta">${safe(item.discipline?.toUpperCase() ?? '—')} · ${safe(sub)}</span>
  </button>`;
}

function showParticipationDetail(item) {
  if (!participationDetailPanel || !participationDetailEvent || !participationDetailMeta || !participationDetailStats) return;
  participationDetailEvent.textContent = item.event_title || '—';
  const metaParts = [];
  if (item.event_start_time_utc) metaParts.push(formatDateTime(item.event_start_time_utc));
  const state = item.participation_state ?? item.status ?? '—';
  metaParts.push(String(state));
  if (item.discipline) metaParts.push(item.discipline.toUpperCase());
  participationDetailMeta.textContent = metaParts.length ? metaParts.join(' · ') : '—';
  const statParts = [];
  if (item.position_overall != null) statParts.push(`Position: ${item.position_overall}`);
  if (item.laps_completed != null) statParts.push(`Laps: ${item.laps_completed}`);
  if (item.incidents_count != null) statParts.push(`Incidents: ${item.incidents_count}`);
  if (item.penalties_count != null) statParts.push(`Penalties: ${item.penalties_count}`);
  if (item.status) statParts.push(`Status: ${item.status}`);
  participationDetailStats.textContent = statParts.length ? statParts.join(' · ') : '—';
  if (dashboardParticipationsListView) dashboardParticipationsListView.classList.add('is-hidden');
  participationDetailPanel.classList.remove('is-hidden');
}

function hideParticipationDetail() {
  if (participationDetailPanel) participationDetailPanel.classList.add('is-hidden');
  if (dashboardParticipationsListView) dashboardParticipationsListView.classList.remove('is-hidden');
}

function setupParticipationDetailListeners() {
  if (dashboardParticipationsList) {
    dashboardParticipationsList.addEventListener('click', (e) => {
      const card = e.target.closest('[data-participation-id]');
      if (!card) return;
      const id = card.getAttribute('data-participation-id');
      const item = lastDriverParticipations.find((p) => p.id === id);
      if (item) showParticipationDetail(item);
    });
  }
  if (participationDetailBack) {
    participationDetailBack.addEventListener('click', hideParticipationDetail);
  }
}
setupParticipationDetailListeners();

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
      dashboardParticipationsList.innerHTML = '<div role="listitem">No participations loaded.</div>';
    }
    hideParticipationDetail();
    lastRiskFlagsWithDetails = [];
    setRiskFlagsTabList([]);
    if (statRiskFlags) statRiskFlags.textContent = '--';
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
  if (dashboardParticipationsList) {
    dashboardParticipationsList.innerHTML = '<div role="listitem" class="participation-cards__loading">Loading...</div>';
  }
  try {
    const res = await apiFetch(`/api/participations?driver_id=${driver.id}`);
    if (res.ok) {
      participations = await res.json();
    }
  } catch (err) {
    participations = [];
  }
  lastDriverParticipations = participations;

  const completedParticipations = participations.filter(
    (p) => String(p.participation_state ?? p.status ?? '').toLowerCase() === 'completed'
  );
  if (statEvents) statEvents.textContent = completedParticipations.length.toString();
  const incidentTotal = participations.reduce((sum, item) => sum + (item.incidents_count || 0), 0);
  if (statIncidents) statIncidents.textContent = incidentTotal.toString();

  if (dashboardParticipationsList) {
    participationDisplayLimit = PARTICIPATION_PAGE_SIZE;
    if (!participations.length) {
      dashboardParticipationsList.innerHTML = '<div role="listitem">No participations loaded.</div>';
    } else {
      const initial = participations.slice(0, participationDisplayLimit);
      dashboardParticipationsList.innerHTML = initial
        .map((item) => renderParticipationCard(item))
        .join('');
    }
  }

  const riskFlagsWithDetails = [];
  if (participations.length === 0) {
    riskFlagsWithDetails.push({
      type: 'no_data',
      message: 'No participation data yet.',
      explanation: 'Complete at least one event to see risk flags and stats.',
      events: []
    });
  } else {
    const avgIncidents = incidentTotal / participations.length;
    const dnfCount = participations.filter((item) => item.status === 'dnf' || item.status === 'dsq').length;
    const dnfRate = dnfCount / participations.length;
    const dnfParticipations = participations.filter((item) => item.status === 'dnf' || item.status === 'dsq');
    const highIncidentParticipations = participations.filter((p) => (p.incidents_count || 0) > 0);
    if (avgIncidents > 1.5) {
      riskFlagsWithDetails.push({
        type: 'high_incidents',
        message: 'High incident rate - prioritize clean races.',
        explanation: `Your average incidents per race is ${avgIncidents.toFixed(1)} (above 1.5). Cleaner driving will improve your CRS and license progress.`,
        events: highIncidentParticipations.map((p) => ({
          event_id: p.event_id,
          event_title: p.event_title || (p.event_id != null ? String(p.event_id).slice(0, 8) : '') || '—'
        }))
      });
    }
    if (dnfRate > 0.2) {
      riskFlagsWithDetails.push({
        type: 'high_dnf',
        message: 'DNF rate above 20% - focus on finishing.',
        explanation: `${Math.round(dnfRate * 100)}% of your races ended in DNF/DSQ (${dnfCount} of ${participations.length}). Finishing races consistently improves your standing.`,
        events: dnfParticipations.map((p) => ({
          event_id: p.event_id,
          event_title: p.event_title || (p.event_id != null ? String(p.event_id).slice(0, 8) : '') || '—'
        }))
      });
    }
    if (avgIncidents <= 1.5 && dnfRate <= 0.2) {
      riskFlagsWithDetails.push({
        type: 'no_critical',
        message: 'No critical risks detected.',
        explanation: 'Your incident rate and finish rate are within safe limits. Keep up the consistency.',
        events: []
      });
    }
  }
  lastRiskFlagsWithDetails = riskFlagsWithDetails;
  const riskFlags = riskFlagsWithDetails.map((r) => r.message);
  try {
    setRiskFlagsTabList(riskFlagsWithDetails);
  } catch (tabErr) {
    console.warn('setRiskFlagsTabList failed:', tabErr);
  }
  if (statRiskFlags) {
    const actualRiskCount = riskFlagsWithDetails.filter(
      (r) => r.type !== 'no_data' && r.type !== 'no_critical'
    ).length;
    statRiskFlags.textContent = actualRiskCount.toString();
  }
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

function taskEscapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

const TIER_ORDER = ['E0', 'E1', 'E2', 'E3', 'E4', 'E5'];

/** Build list of human-readable requirement strings from task definition (columns + requirements JSON). */
function getTaskRequirementsList(task) {
  const req = task?.requirements && typeof task.requirements === 'object' ? task.requirements : {};
  const v = (key, col) => {
    const val = task?.[col] ?? task?.[key] ?? req[key];
    if (val === undefined || val === null) return null;
    return val;
  };
  const lines = [];
  if (v('min_event_tier', 'min_event_tier')) lines.push(`Min event tier: ${v('min_event_tier', 'min_event_tier')}`);
  if (v('max_event_tier', 'max_event_tier')) lines.push(`Max event tier: ${v('max_event_tier', 'max_event_tier')}`);
  if (v('min_duration_minutes', 'min_duration_minutes') != null) lines.push(`Min session duration: ${v('min_duration_minutes', 'min_duration_minutes')} min`);
  if (v('max_incidents', 'max_incidents') != null) lines.push(`Max incidents: ${v('max_incidents', 'max_incidents')}`);
  if (v('max_penalties', 'max_penalties') != null) lines.push(`Max penalties: ${v('max_penalties', 'max_penalties')}`);
  if (v('require_night', 'require_night')) lines.push('Night session: yes');
  if (v('require_dynamic_weather', 'require_dynamic_weather')) lines.push('Dynamic weather: yes');
  if (v('require_team_event', 'require_team_event')) lines.push('Team event: yes');
  if (v('require_clean_finish', 'require_clean_finish')) lines.push('Clean finish (no incidents/penalties): yes');
  if (v('allow_non_finish', 'allow_non_finish')) lines.push('DNF allowed: yes');
  if (v('max_position_overall', 'max_position_overall') != null) lines.push(`Position overall no worse than: ${v('max_position_overall', 'max_position_overall')}`);
  if (v('min_position_overall', 'min_position_overall') != null) lines.push(`Position overall no better than: ${v('min_position_overall', 'min_position_overall')}`);
  if (v('min_laps_completed', 'min_laps_completed') != null) lines.push(`Min laps completed: ${v('min_laps_completed', 'min_laps_completed')}`);
  if (v('repeatable', 'repeatable')) lines.push('Repeatable task: yes');
  if (v('max_completions', 'max_completions') != null) lines.push(`Max completions: ${v('max_completions', 'max_completions')}`);
  if (v('cooldown_hours', 'cooldown_hours') != null) lines.push(`Cooldown between completions: ${v('cooldown_hours', 'cooldown_hours')} h`);
  if (v('diversity_window_days', 'diversity_window_days') != null) lines.push(`Diversity window: ${v('diversity_window_days', 'diversity_window_days')} days`);
  if (v('max_same_event_count', 'max_same_event_count') != null) lines.push(`Max completions from same event: ${v('max_same_event_count', 'max_same_event_count')}`);
  if (v('require_event_diversity', 'require_event_diversity')) lines.push('Event diversity required: yes');
  if (v('max_same_signature_count', 'max_same_signature_count') != null) lines.push(`Max completions from same track type: ${v('max_same_signature_count', 'max_same_signature_count')}`);
  if (v('signature_cooldown_hours', 'signature_cooldown_hours') != null) lines.push(`Track type cooldown: ${v('signature_cooldown_hours', 'signature_cooldown_hours')} h`);
  if (v('diminishing_returns', 'diminishing_returns')) {
    const step = v('diminishing_step', 'diminishing_step');
    const floor = v('diminishing_floor', 'diminishing_floor');
    lines.push(`Diminishing score multiplier${step != null ? `, step ${step}` : ''}${floor != null ? `, floor ${floor}` : ''}`);
  }
  return lines;
}

function driverTierAllowsTask(driver, task) {
  if (!task?.min_event_tier) return true;
  const driverTier = driver?.tier || 'E0';
  const driverIdx = TIER_ORDER.indexOf(driverTier);
  const taskIdx = TIER_ORDER.indexOf(task.min_event_tier);
  if (driverIdx === -1) return true;
  if (taskIdx === -1) return true;
  return driverIdx >= taskIdx;
}

async function showTaskDetail(task, driver) {
  const listView = document.querySelector('[data-tasks-list-view]');
  const panel = document.querySelector('[data-task-detail-panel]');
  const content = document.querySelector('[data-task-detail-content]');
  const actionsEl = document.querySelector('[data-task-detail-actions]');
  const takeBtn = document.querySelector('[data-task-detail-take]');
  const declineBtn = document.querySelector('[data-task-detail-decline]');
  const eventRelatedMsg = document.querySelector('[data-task-detail-event-related-msg]');
  if (!listView || !panel || !content) return;

  const completedIds = new Set(
    lastTaskCompletions.filter((c) => c.status === 'completed').map((c) => c.task_id)
  );
  const pendingTaskIds = new Set(
    lastTaskCompletions.filter((c) => c.status === 'pending' || c.status === 'in_progress').map((c) => c.task_id)
  );
  const completionForTask = lastTaskCompletions.find((c) => (c.status === 'pending' || c.status === 'in_progress') && c.task_id === task.id);
  const failureReasons = completionForTask?.evaluation_failure_reasons;
  const isInProgressFailed = completionForTask?.status === 'in_progress' && Array.isArray(failureReasons) && failureReasons.length > 0;
  const isCompleted = completedIds.has(task.id);
  const isTaken = pendingTaskIds.has(task.id);
  const isEventRelated = task.event_related !== false;
  const canTake = !isCompleted && !isTaken && driverTierAllowsTask(driver, task) && !isEventRelated;
  const canDecline = isTaken || canTake;

  const taskCode = task.code ?? task.id ?? '—';
  const statusText = isCompleted ? 'Completed' : isTaken ? (isInProgressFailed ? 'In progress (not met)' : 'In progress') : 'Not taken';
  const requirementsList = getTaskRequirementsList(task);
  const requirementsHtml = requirementsList.length
    ? `<div><dt>Requirements</dt><dd><ul class="task-requirements-list">${requirementsList.map((r) => `<li>${taskEscapeHtml(r)}</li>`).join('')}</ul></dd></div>`
    : '<div><dt>Requirements</dt><dd>—</dd></div>';
  content.innerHTML = `
    <dl class="task-detail-dl">
      <div><dt>Code</dt><dd>${taskEscapeHtml(taskCode)}</dd></div>
      <div><dt>Name</dt><dd>${taskEscapeHtml(task.name ?? '—')}</dd></div>
      <div><dt>Discipline</dt><dd>${taskEscapeHtml(task.discipline ?? '—')}</dd></div>
      <div><dt>Description</dt><dd>${taskEscapeHtml(task.description ?? '—')}</dd></div>
      ${task.min_event_tier ? `<div><dt>Min event tier</dt><dd>${taskEscapeHtml(task.min_event_tier)}</dd></div>` : ''}
      <div><dt>Status</dt><dd>${statusText}</dd></div>
      ${requirementsHtml}
      ${isInProgressFailed ? `<div><dt>Why not met</dt><dd><ul class="task-failure-reasons">${failureReasons.map((r) => `<li>${taskEscapeHtml(r)}</li>`).join('')}</ul></dd></div>` : ''}
    </dl>
  `;

  if (eventRelatedMsg) {
    if (isEventRelated && !isCompleted && !isTaken) {
      eventRelatedMsg.classList.remove('is-hidden');
      const code = (task.code || '').trim();
      if (code && driver?.id) {
        try {
          const res = await apiFetch(`/api/events?driver_id=${encodeURIComponent(driver.id)}&task_code=${encodeURIComponent(code)}&rig_filter=false`);
          const events = res.ok ? await res.json() : [];
          const names = (Array.isArray(events) ? events : []).map((e) => e.title || e.id).filter(Boolean);
          eventRelatedMsg.textContent = names.length
            ? `Task is assigned automatically when you participate in: ${names.join(', ')}.`
            : 'Task is assigned automatically when you participate in a matching event.';
        } catch {
          eventRelatedMsg.textContent = 'Task is assigned automatically when you participate in a matching event.';
        }
      } else {
        eventRelatedMsg.textContent = 'Task is assigned automatically when you participate in a matching event.';
      }
    } else {
      eventRelatedMsg.classList.add('is-hidden');
      eventRelatedMsg.textContent = '';
    }
  }

  if (takeBtn) {
    takeBtn.style.display = canTake ? '' : 'none';
    takeBtn.dataset.taskId = task.id;
    takeBtn.dataset.driverId = driver?.id ?? '';
  }
  if (declineBtn) {
    declineBtn.style.display = canDecline ? '' : 'none';
    declineBtn.dataset.taskId = task.id;
    declineBtn.dataset.driverId = driver?.id ?? '';
  }
  if (actionsEl) actionsEl.classList.toggle('is-hidden', !canTake && !canDecline);

  listView.classList.add('is-hidden');
  panel.classList.remove('is-hidden');
}

function hideTaskDetail() {
  const listView = document.querySelector('[data-tasks-list-view]');
  const panel = document.querySelector('[data-task-detail-panel]');
  if (listView) listView.classList.remove('is-hidden');
  if (panel) panel.classList.add('is-hidden');
}

async function taskAction(driverId, taskId, status) {
  try {
    const res = await apiFetch('/api/tasks/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ driver_id: driverId, task_id: taskId, status }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = Array.isArray(err.detail) ? err.detail.map((d) => d.msg).join(', ') : (err.detail || 'Action failed.');
      if (typeof window !== 'undefined' && window.alert) window.alert(msg);
      return;
    }
    hideTaskDetail();
    if (lastDriverForTasks) await loadTasksOverview(lastDriverForTasks);
  } catch (err) {
    if (typeof window !== 'undefined' && window.alert) window.alert('Action failed.');
  }
}

function initTaskDetailDelegation() {
  if (document.body.dataset.taskDetailDelegation) return;
  document.body.dataset.taskDetailDelegation = '1';
  document.body.addEventListener('click', (e) => {
    const taskRow = e.target.closest('.task-list-item__text[data-task-id]');
    if (taskRow) {
      e.preventDefault();
      const taskId = taskRow.getAttribute('data-task-id');
      const driver = lastDriverForTasks;
      if (!taskId || !driver) return;
      const task = lastTaskDefinitions.find((t) => t.id === taskId);
      if (task) showTaskDetail(task, driver);
      return;
    }
    if (e.target.closest('[data-task-detail-back]')) {
      e.preventDefault();
      hideTaskDetail();
      return;
    }
    const takeBtn = e.target.closest('[data-task-detail-take]');
    if (takeBtn && takeBtn.dataset.taskId) {
      e.preventDefault();
      taskAction(takeBtn.dataset.driverId, takeBtn.dataset.taskId, 'pending');
      return;
    }
    const declineBtn = e.target.closest('[data-task-detail-decline]');
    if (declineBtn && declineBtn.dataset.taskId) {
      e.preventDefault();
      taskAction(declineBtn.dataset.driverId, declineBtn.dataset.taskId, 'failed');
      return;
    }
  });
}

export const loadTasksOverview = async (driver) => {
  if (!driver) {
    lastDriverForTasks = null;
    lastTaskDefinitions = [];
    lastTaskCompletions = [];
    hideTaskDetail();
    if (tasksCompletedList) setList(tasksCompletedList, [], 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, [], 'No pending tasks.');
    if (tasksInProgressList) setList(tasksInProgressList, [], 'No tasks in progress.');
    if (statTasks) statTasks.textContent = '0';
    readinessState.tasksCompleted = 0;
    readinessState.tasksTotal = 0;
    updateReadiness();
    return;
  }
  lastDriverForTasks = driver;
  const discipline = driver.primary_discipline || 'gt';
  try {
    const [completionsRes, definitionsRes] = await Promise.all([
      apiFetch(`/api/tasks/completions?driver_id=${driver.id}`),
      apiFetch('/api/tasks/definitions')
    ]);
    const completions = completionsRes.ok ? await completionsRes.json() : [];
    const definitions = definitionsRes.ok ? await definitionsRes.json() : [];
    lastTaskCompletions = completions;
    lastTaskDefinitions = definitions;

    const completedIds = new Set(completions.filter((c) => c.status === 'completed').map((c) => c.task_id));
    const inProgressIds = new Set(completions.filter((c) => c.status === 'pending' || c.status === 'in_progress').map((c) => c.task_id));
    const filteredDefinitions = definitions.filter((task) => task.discipline === discipline);
    const completedTasks = filteredDefinitions.filter((task) => completedIds.has(task.id));
    // In progress only if has pending/in_progress and NOT already completed (avoid same task in both lists)
    const inProgressTasks = filteredDefinitions.filter((task) => inProgressIds.has(task.id) && !completedIds.has(task.id));
    const pendingTasks = filteredDefinitions.filter((task) => !completedIds.has(task.id) && !inProgressIds.has(task.id));

    if (tasksPendingList) setTaskListClickable(tasksPendingList, pendingTasks.slice(0, 15), 'No pending tasks.');
    if (tasksInProgressList) setTaskListClickable(tasksInProgressList, inProgressTasks, 'No tasks in progress.');
    if (tasksCompletedList) setTaskListClickable(tasksCompletedList, completedTasks, 'No tasks completed yet.');
    if (statTasks) statTasks.textContent = completedTasks.length.toString();
    readinessState.tasksCompleted = completedTasks.length;
    readinessState.tasksTotal = filteredDefinitions.length;
    updateReadiness();
  } catch (err) {
    if (tasksCompletedList) setList(tasksCompletedList, [], 'No tasks completed yet.');
    if (tasksPendingList) setList(tasksPendingList, [], 'No pending tasks.');
    if (tasksInProgressList) setList(tasksInProgressList, [], 'No tasks in progress.');
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

const COMPLETE_TASK_PREFIX = 'Complete task:';
const RACE_OF_PREFIXES = ['Race of the day:', 'Race of the week:', 'Race of the month:', 'Race of the year:'];

export const loadDashboardRecommendations = async (driver) => {
  const tasksEl = document.querySelector('[data-recommendation-tasks]');
  const racesEl = document.querySelector('[data-recommendation-races]');
  if (!tasksEl || !racesEl) return;
  if (recommendationCountdownInterval) {
    clearInterval(recommendationCountdownInterval);
    recommendationCountdownInterval = null;
  }
  const setEmpty = () => {
    if (tasksEl) setList(tasksEl, ['Log in and create a driver profile to see next steps.'], '');
    if (racesEl) setList(racesEl, ['—'], '');
  };
  if (!driver) {
    setEmpty();
    updateRecommendationCards(null);
    return;
  }
  try {
    const discipline = driver.primary_discipline || 'gt';
    const res = await apiFetch(`/api/recommendations/latest?driver_id=${driver.id}&discipline=${discipline}`);
    if (!res.ok) {
      if (tasksEl) setList(tasksEl, ['No recommendations yet.'], '');
      if (racesEl) setList(racesEl, ['—'], '');
      updateRecommendationCards(null);
      return;
    }
    let data;
    try {
      data = await res.json();
    } catch (parseErr) {
      if (tasksEl) setList(tasksEl, ['Unable to load recommendations.'], '');
      if (racesEl) setList(racesEl, ['—'], '');
      updateRecommendationCards(null);
      return;
    }
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      if (recommendationCountdownInterval) {
        clearInterval(recommendationCountdownInterval);
        recommendationCountdownInterval = null;
      }
      const items = data.items || [];
      const taskItems = items.filter((i) => typeof i === 'string' && i.startsWith(COMPLETE_TASK_PREFIX));
      const raceItems = items.filter((i) => typeof i === 'string' && RACE_OF_PREFIXES.some((p) => i.startsWith(p)));
      setRecommendationTasksList(tasksEl, taskItems, lastTaskDefinitions, 'No tasks to complete.');
      setRecommendationRacesList(racesEl, raceItems, data.special_events || [], '—', formatCountdown);
      recommendationCountdownInterval = setInterval(() => {
        tickRecommendationCountdowns(racesEl, formatCountdown);
      }, 1000);
      updateRecommendationCards(data);
    } else {
      if (tasksEl) setList(tasksEl, ['No recommendations yet.'], '');
      if (racesEl) setList(racesEl, ['—'], '');
      updateRecommendationCards(null);
    }
  } catch (err) {
    console.warn('loadDashboardRecommendations failed:', err);
    setEmpty();
    updateRecommendationCards(null);
  }
};

export const loadLicenseProgress = async (driver) => {
  if (!licenseCurrent || !licenseNext || !licenseReqs) return;
  if (!driver) {
    lastDriverLicenseLevel = null;
    lastDriverForLicense = null;
    lastLicenseLevels = [];
    licenseCurrent.textContent = '--';
    licenseNext.textContent = '--';
    delete licenseCurrent.dataset.licenseCode;
    delete licenseNext.dataset.licenseCode;
    setList(licenseReqs, [], 'Create a driver profile to see license progress.');
    return;
  }
  lastDriverForLicense = driver;
  try {
    const discipline = driver.primary_discipline || 'gt';
    const [latestRes, reqRes, levelsRes] = await Promise.all([
      apiFetch(`/api/licenses/latest?driver_id=${driver.id}&discipline=${discipline}`),
      apiFetch(`/api/licenses/requirements?discipline=${discipline}&driver_id=${driver.id}`),
      apiFetch(`/api/licenses/levels?discipline=${discipline}`)
    ]);
    const latest = latestRes.ok ? await latestRes.json() : null;
    const requirements = reqRes.ok ? await reqRes.json() : null;
    const levelsData = levelsRes.ok ? await levelsRes.json().catch(() => []) : [];
    lastLicenseLevels = Array.isArray(levelsData) ? levelsData : [];
    lastDriverLicenseLevel = latest?.level_code ?? null;
    if (latest) {
      licenseCurrent.textContent = latest.level_code;
      licenseCurrent.dataset.licenseCode = latest.level_code;
    } else {
      licenseCurrent.textContent = 'None';
      delete licenseCurrent.dataset.licenseCode;
    }
    if (requirements) {
      const nextCode = requirements.next_level || '--';
      licenseNext.textContent = nextCode;
      if (nextCode && nextCode !== '--') licenseNext.dataset.licenseCode = nextCode;
      else delete licenseNext.dataset.licenseCode;
      setLicenseReqsList(licenseReqs, requirements.requirements || [], 'No requirements loaded.');
    } else {
      licenseNext.textContent = '--';
      delete licenseNext.dataset.licenseCode;
      setList(licenseReqs, ['Maintain performance to keep license.'], '');
    }
  } catch (err) {
    lastDriverLicenseLevel = null;
    lastLicenseLevels = [];
    licenseCurrent.textContent = '--';
    licenseNext.textContent = '--';
    delete licenseCurrent.dataset.licenseCode;
    delete licenseNext.dataset.licenseCode;
    setList(licenseReqs, [], 'Unable to load license progress.');
  }
};

let lastRiskFlagsWithDetails = [];

let lastDriverForEvents = null;
let lastDriverForActiveRace = null;
let lastDashboardEventsData = [];
let lastDashboardPastEventsData = [];
let lastUpcomingEventsData = [];
const EVENT_PAGE_SIZE = 3;
let upcomingEventsCache = [];
let upcomingEventsTotalCount = 0;
let upcomingEventsLoadingMore = false;
let lastUpcomingEventsDriver = null;
let pastEventsCache = [];
let pastEventsTotalCount = 0;
let pastEventsLoadingMore = false;
let lastPastEventsDriver = null;
const PARTICIPATION_PAGE_SIZE = 3;
let participationDisplayLimit = PARTICIPATION_PAGE_SIZE;
let lastShownEventId = null;
let lastShownEvent = null;
let lastDriverParticipations = [];
let lastDriverLicenseLevel = null;
let lastDriverForLicense = null;
let lastLicenseLevels = [];
let lastDriverForTasks = null;
let lastTaskDefinitions = [];
let lastTaskCompletions = [];

const EVENT_STATUS_LABELS = {
  waiting_start: 'Waiting to start',
  started: 'Started',
  finished: 'Finished',
  completed: 'Completed',
  in_progress: 'In progress',
};

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
  // Normalize so rig check is stable (no undefined vs null flip-flop)
  const driverRigOpts = driver && typeof driver === 'object' ? (driver.rig_options ?? null) : null;
  const eventRigOpts = event && typeof event === 'object' && event.rig_options ? event.rig_options : null;
  const eventTier = (event.event_tier ?? 'E2').toUpperCase();
  const driverTier = (driver?.tier ?? 'E0').toUpperCase();
  const tierMatch = eventTier === driverTier;
  const reqLicense = (event.license_requirement ?? 'none').toLowerCase();
  const reqRank = LICENSE_REQUIREMENT_RANK[reqLicense] ?? 0;
  const driverLicenseRank = reqRank === 0 ? 1 : (LICENSE_REQUIREMENT_RANK[(lastDriverLicenseLevel ?? '').toLowerCase()] ?? 0);
  const licenseOk = reqRank === 0 || driverLicenseRank >= reqRank;
  const MAX_WITHDRAWALS = 3;
  const participationForEvent = lastDriverParticipations.find((p) => p.event_id === event.id);
  const state = participationForEvent ? String(participationForEvent.participation_state || '').toLowerCase() : '';
  const withdrawCount = participationForEvent ? (Number(participationForEvent.withdraw_count) || 0) : 0;
  const isWithdrawn = state === 'withdrawn';
  const isRegistered = state === 'registered';
  const canReRegister = participationForEvent && isWithdrawn && withdrawCount < MAX_WITHDRAWALS;
  const eventHasRigReq = eventRigOpts && (eventRigOpts.wheel_type || eventRigOpts.pedals_class || eventRigOpts.manual_with_clutch === true);
  const driverRigUnknown = eventHasRigReq && (!driver || driver.rig_options === undefined);
  const rigOk = driverRigUnknown ? false : driverRigSatisfiesEvent(driverRigOpts, eventRigOpts);
  const startMs = event.start_time_utc ? new Date(event.start_time_utc).getTime() : NaN;
  const isPastEvent = !Number.isNaN(startMs) && startMs < Date.now();
  const canRegister = !isPastEvent && tierMatch && licenseOk && rigOk && (!participationForEvent || canReRegister);
  const maxWithdrawalsReached = participationForEvent && isWithdrawn && withdrawCount >= MAX_WITHDRAWALS;
  const cannotRegisterReason = isPastEvent ? 'past' : !tierMatch ? 'tier' : !licenseOk ? 'license' : (!rigOk && !driverRigUnknown) ? 'rig' : null;
  const rigLoading = driverRigUnknown;
  const canWithdraw = participationForEvent && isRegistered;
  const status = getEventStatus(event);
  const statusLabel = status ? EVENT_STATUS_LABELS[status] : '—';
  const ro = eventRigOpts || {};
  const rigParts = [];
  if (ro.wheel_type) rigParts.push(`Wheel: ${ro.wheel_type.replace(/_/g, ' ')}`);
  if (ro.pedals_class) rigParts.push(`Pedals: ${ro.pedals_class}`);
  if (ro.manual_with_clutch === true) rigParts.push('Clutch: yes');
  const rigLabel = rigParts.length ? rigParts.join(', ') : '—';
  const difficultyLabel = event.difficulty_score != null ? String(Number(event.difficulty_score)) : '—';
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
      <div><dt>Rig</dt><dd>${escapeHtml(rigLabel)}</dd></div>
      <div><dt>Difficulty score</dt><dd>${escapeHtml(difficultyLabel)}</dd></div>
      ${event.country ? `<div><dt>Country</dt><dd>${escapeHtml(event.country)}</dd></div>` : ''}
      ${event.city ? `<div><dt>City</dt><dd>${escapeHtml(event.city)}</dd></div>` : ''}
    </dl>
  `;
  const withdrawBtn = document.querySelector('[data-event-detail-withdraw]');
  const maxWithdrawalsMsg = document.querySelector('[data-event-detail-max-withdrawals]');
  const noRegisterMsg = document.querySelector('[data-event-detail-no-register-message]');
  const showNoRegisterMsg = !canRegister && !maxWithdrawalsReached && (rigLoading || cannotRegisterReason);
  const showActions = canRegister || canWithdraw || maxWithdrawalsReached || showNoRegisterMsg;
  if (noRegisterMsg) {
    if (rigLoading) noRegisterMsg.textContent = 'Loading…';
    else if (cannotRegisterReason === 'past') noRegisterMsg.textContent = 'Registration is closed. This event has already started or finished.';
    else if (cannotRegisterReason) {
      noRegisterMsg.textContent = cannotRegisterReason === 'tier' ? 'This event does not match your tier. You cannot register.'
        : cannotRegisterReason === 'license' ? 'You do not meet the license requirement for this event. You cannot register.'
          : 'Your rig does not meet this event\'s requirements. You cannot register.';
    } else noRegisterMsg.textContent = '';
    noRegisterMsg.classList.toggle('is-hidden', !showNoRegisterMsg);
  }
  if (registerBtn) {
    registerBtn.disabled = !canRegister;
    registerBtn.dataset.eventId = event.id;
    registerBtn.dataset.driverId = driver?.id ?? '';
    registerBtn.classList.toggle('is-hidden', !canRegister);
  }
  if (withdrawBtn) {
    withdrawBtn.dataset.participationId = participationForEvent && canWithdraw ? participationForEvent.id : '';
    withdrawBtn.classList.toggle('is-hidden', !canWithdraw);
  }
  if (maxWithdrawalsMsg) {
    maxWithdrawalsMsg.textContent = `You have reached the maximum number of withdrawals (${MAX_WITHDRAWALS}) for this event. You cannot register again.`;
    maxWithdrawalsMsg.classList.toggle('is-hidden', !maxWithdrawalsReached);
  }
  if (actionsEl) actionsEl.classList.toggle('is-hidden', !showActions);
  lastShownEventId = event.id;
  lastShownEvent = event;
  listView.classList.add('is-hidden');
  panel.classList.remove('is-hidden');
}

function hideEventDetail() {
  lastShownEventId = null;
  lastShownEvent = null;
  const listView = document.querySelector('[data-events-list-view]');
  const panel = document.querySelector('[data-event-detail-panel]');
  if (listView) listView.classList.remove('is-hidden');
  if (panel) panel.classList.add('is-hidden');
}

function showLicenseDetail(level) {
  const listView = document.querySelector('[data-licenses-list-view]');
  const panel = document.querySelector('[data-license-detail-panel]');
  const content = document.querySelector('[data-license-detail-content]');
  if (!listView || !panel || !content) return;
  const codes = level.required_task_codes && Array.isArray(level.required_task_codes) ? level.required_task_codes : [];
  const requiredTasksHtml = codes.length
    ? codes
        .map((code) => `<button type="button" class="btn-link license-task-code-link" data-license-task-code="${escapeHtml(code)}">${escapeHtml(code)}</button>`)
        .join(', ')
    : '—';
  content.innerHTML = `
    <dl class="event-detail-dl license-detail-dl">
      <div><dt>Code</dt><dd>${escapeHtml(level.code ?? '—')}</dd></div>
      <div><dt>Name</dt><dd>${escapeHtml(level.name ?? '—')}</dd></div>
      <div><dt>Description</dt><dd>${escapeHtml(level.description ?? '—')}</dd></div>
      <div><dt>Min CRS</dt><dd>${level.min_crs != null ? Number(level.min_crs) : '—'}</dd></div>
      <div><dt>Required tasks</dt><dd>${requiredTasksHtml}</dd></div>
    </dl>
  `;
  listView.classList.add('is-hidden');
  panel.classList.remove('is-hidden');
}

function hideLicenseDetail() {
  const listView = document.querySelector('[data-licenses-list-view]');
  const panel = document.querySelector('[data-license-detail-panel]');
  if (listView) listView.classList.remove('is-hidden');
  if (panel) panel.classList.add('is-hidden');
}

function escapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function setRiskFlagsTabList(items) {
  const listEl = riskFlagsTabList || document.querySelector('[data-risk-flags-tab-list]');
  if (!listEl) return;
  if (!items || items.length === 0) {
    listEl.innerHTML = '<li>Log in to see risk flags.</li>';
    return;
  }
  listEl.innerHTML = items
    .map(
      (item, i) =>
        `<li class="risk-flag-item"><button type="button" class="btn-link risk-flag-item__text" data-risk-index="${i}">${escapeHtml(item.message)}</button></li>`
    )
    .join('');
}

function showRiskFlagDetail(index) {
  const item = lastRiskFlagsWithDetails[index];
  if (!item || !riskFlagsDetailPanel || !riskFlagsListView) return;
  const titleEl = riskFlagsDetailPanel.querySelector('[data-risk-flags-detail-title]');
  const explanationEl = riskFlagsDetailPanel.querySelector('[data-risk-flags-detail-explanation]');
  const eventsEl = riskFlagsDetailPanel.querySelector('[data-risk-flags-detail-events]');
  if (titleEl) titleEl.textContent = item.message;
  if (explanationEl) explanationEl.textContent = item.explanation;
  if (eventsEl) {
    if (!item.events || item.events.length === 0) {
      eventsEl.innerHTML = '<li>—</li>';
    } else {
      eventsEl.innerHTML = item.events
        .map(
          (e) =>
            `<li><button type="button" class="btn-link risk-flag-event-link" data-event-id="${escapeHtml(String(e.event_id ?? ''))}">${escapeHtml(String(e.event_title ?? '—'))}</button></li>`
        )
        .join('');
    }
  }
  riskFlagsListView.classList.add('is-hidden');
  riskFlagsDetailPanel.classList.remove('is-hidden');
}

function hideRiskFlagDetail() {
  if (riskFlagsListView) riskFlagsListView.classList.remove('is-hidden');
  if (riskFlagsDetailPanel) riskFlagsDetailPanel.classList.add('is-hidden');
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
      await loadTasksOverview(lastDriverForEvents);
    }
  } catch (err) {
    if (typeof window !== 'undefined' && window.alert) window.alert('Register failed.');
  }
};

const withdrawFromEvent = async (participationId) => {
  if (!participationId) return;
  try {
    const res = await apiFetch(`/api/participations/${encodeURIComponent(participationId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ participation_state: 'withdrawn' }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = Array.isArray(err.detail) ? err.detail : (err.detail || 'Withdraw failed.');
      if (typeof window !== 'undefined' && window.alert) window.alert(typeof msg === 'string' ? msg : msg.detail || 'Withdraw failed.');
      return;
    }
    hideEventDetail();
    if (lastDriverForEvents) {
      await loadDashboardStats(lastDriverForEvents);
      await loadDashboardEvents(lastDriverForEvents);
      await loadTasksOverview(lastDriverForEvents);
    }
  } catch (err) {
    if (typeof window !== 'undefined' && window.alert) window.alert('Withdraw failed.');
  }
};

function initDashboardEventsRegisterDelegation() {
  if (document.body.dataset.dashboardEventsRegisterDelegation) return;
  document.body.dataset.dashboardEventsRegisterDelegation = '1';
  document.body.addEventListener('click', async (e) => {
    const riskItem = e.target.closest('[data-risk-index]');
    if (riskItem) {
      const list = e.target.closest('[data-risk-flags-tab-list]');
      if (list) {
        e.preventDefault();
        const index = parseInt(riskItem.getAttribute('data-risk-index'), 10);
        if (!Number.isNaN(index)) showRiskFlagDetail(index);
        return;
      }
    }
    const riskDetailBack = e.target.closest('[data-risk-flags-detail-back]');
    if (riskDetailBack) {
      e.preventDefault();
      hideRiskFlagDetail();
      document.querySelector('[data-tab-button="overview"]')?.click();
      return;
    }
    const licenseCodeBtn = e.target.closest('[data-license-code]');
    if (licenseCodeBtn) {
      e.preventDefault();
      const code = licenseCodeBtn.getAttribute('data-license-code');
      if (code && lastLicenseLevels.length) {
        const level = lastLicenseLevels.find((l) => (l.code || '').toUpperCase() === (code || '').toUpperCase());
        if (level) showLicenseDetail(level);
      }
      return;
    }
    const licenseDetailBack = e.target.closest('[data-license-detail-back]');
    if (licenseDetailBack) {
      e.preventDefault();
      hideLicenseDetail();
      return;
    }
    const licenseTaskCodeBtn = e.target.closest('[data-license-task-code]');
    if (licenseTaskCodeBtn) {
      e.preventDefault();
      const code = licenseTaskCodeBtn.getAttribute('data-license-task-code');
      const driver = lastDriverForTasks || lastDriverForLicense;
      if (!code || !driver) return;
      const findTaskByCode = (defs) => (defs || []).find((t) => (t.code || '').toLowerCase() === (code || '').toLowerCase());
      let task = findTaskByCode(lastTaskDefinitions);
      if (!task && lastTaskDefinitions.length === 0) {
        try {
          const res = await apiFetch('/api/tasks/definitions');
          if (res.ok) {
            const defs = await res.json();
            lastTaskDefinitions = defs;
            task = findTaskByCode(defs);
          }
        } catch (_) {}
      }
      if (task) {
        const tasksTab = document.querySelector('[data-tab-button="tasks"]');
        if (tasksTab) tasksTab.click();
        showTaskDetail(task, driver);
      }
      return;
    }
    const riskEventLink = e.target.closest('.risk-flag-event-link');
    if (riskEventLink) {
      e.preventDefault();
      const eventId = riskEventLink.getAttribute('data-event-id');
      const driver = lastDriverForEvents;
      if (eventId && driver) {
        try {
          const res = await apiFetch(`/api/events/${encodeURIComponent(eventId)}`);
          if (!res.ok) return;
          const event = await res.json();
          const eventsTab = document.querySelector('[data-tab-button="events"]');
          if (eventsTab) eventsTab.click();
          showEventDetail(event, driver);
        } catch (_) {}
      }
      return;
    }
    const recTasksList = e.target.closest('[data-recommendation-tasks]');
    const recTaskItem = recTasksList ? e.target.closest('.rec-item[data-task-id]') : null;
    if (recTaskItem && recTasksList) {
      e.preventDefault();
      const taskId = recTaskItem.getAttribute('data-task-id');
      const driver = lastDriverForTasks;
      if (!taskId || !driver) return;
      const task = lastTaskDefinitions.find((t) => t.id === taskId);
      if (task) {
        const tasksTab = document.querySelector('[data-tab-button="tasks"]');
        if (tasksTab) tasksTab.click();
        showTaskDetail(task, driver);
      }
      return;
    }
    const recRacesList = e.target.closest('[data-recommendation-races]');
    const recRaceItem = recRacesList ? e.target.closest('.rec-item[data-event-id]') : null;
    if (recRaceItem && recRacesList) {
      e.preventDefault();
      const eventId = recRaceItem.getAttribute('data-event-id');
      const driver = lastDriverForEvents;
      if (!eventId || !driver) return;
      try {
        const res = await apiFetch(`/api/events/${encodeURIComponent(eventId)}`);
        if (!res.ok) return;
        const event = await res.json();
        const eventsTab = document.querySelector('[data-tab-button="events"]');
        if (eventsTab) eventsTab.click();
        showEventDetail(event, driver);
      } catch (_) {}
      return;
    }
    const list = e.target.closest('[data-dashboard-events]');
    const upcomingList = e.target.closest('[data-upcoming-events]');
    const pastList = e.target.closest('[data-dashboard-past-events]');
    const textBtn = (list || upcomingList || pastList) ? e.target.closest('.event-list-item__text') : null;
    const cardBtn = (list || pastList) ? e.target.closest('.event-card') : null;
    const eventBtn = textBtn || cardBtn;
    if (eventBtn && (list || upcomingList || pastList)) {
      e.preventDefault();
      const eventId = eventBtn.getAttribute('data-event-id');
      const driverId = eventBtn.getAttribute('data-driver-id');
      const driver = lastDriverForEvents || (driverId && { id: driverId }) || null;
      if (!eventId || !driver) return;
      if (upcomingList) {
        const eventsTab = document.querySelector('[data-tab-button="events"]');
        if (eventsTab) eventsTab.click();
      }
      try {
        const res = await apiFetch(`/api/events/${encodeURIComponent(eventId)}`);
        if (!res.ok) return;
        const event = await res.json();
        showEventDetail(event, lastDriverForEvents || driver);
      } catch (_) {}
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
      return;
    }
    const withdrawBtn = e.target.closest('.btn-withdraw-event-panel:not(.is-hidden)');
    if (withdrawBtn) {
      e.preventDefault();
      const participationId = withdrawBtn.dataset.participationId;
      if (participationId) withdrawFromEvent(participationId);
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

function renderEventCard(event, driver) {
  const sessionLabel = event.session_type === 'training' ? 'Training' : 'Race';
  const timeLabel = event.start_time_utc ? formatDateTime(event.start_time_utc) : '';
  const title = escapeHtml(event.title || '—');
  const meta = [sessionLabel, event.format_type || ''].filter(Boolean).join(' · ') + (timeLabel ? ` · ${escapeHtml(timeLabel)}` : '');
  const driverId = driver ? escapeHtml(driver.id) : '';
  return `<button type="button" class="event-card" data-event-id="${escapeHtml(event.id)}" data-driver-id="${driverId}" role="listitem">
    <span class="event-card__title">${title}</span>
    <span class="event-card__meta">${meta}</span>
  </button>`;
}

async function fetchUpcomingNextPage() {
  if (!lastUpcomingEventsDriver || upcomingEventsLoadingMore || upcomingEventsCache.length >= upcomingEventsTotalCount) return;
  upcomingEventsLoadingMore = true;
  const offset = upcomingEventsCache.length;
  try {
    const url = `/api/events/upcoming?driver_id=${lastUpcomingEventsDriver.id}&discipline=${lastUpcomingEventsDriver.primary_discipline || 'gt'}&limit=${EVENT_PAGE_SIZE}&offset=${offset}`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    upcomingEventsCache.push(...page);
    const html = page.map((ev) => renderEventCard(ev, lastUpcomingEventsDriver)).join('');
    if (dashboardEventsList && html) dashboardEventsList.insertAdjacentHTML('beforeend', html);
  } finally {
    upcomingEventsLoadingMore = false;
  }
}

async function fetchPastNextPage() {
  if (!lastPastEventsDriver || pastEventsLoadingMore || pastEventsCache.length >= pastEventsTotalCount) return;
  pastEventsLoadingMore = true;
  const offset = pastEventsCache.length;
  try {
    const url = `/api/events/past?driver_id=${lastPastEventsDriver.id}&limit=${EVENT_PAGE_SIZE}&offset=${offset}`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    pastEventsCache.push(...page);
    const html = page.map((ev) => renderEventCard(ev, lastPastEventsDriver)).join('');
    if (dashboardPastEventsList && html) dashboardPastEventsList.insertAdjacentHTML('beforeend', html);
  } finally {
    pastEventsLoadingMore = false;
  }
}

async function resetUpcomingEventsToFirstPage() {
  if (!dashboardEventsList || !lastUpcomingEventsDriver) return;
  try {
    const url = `/api/events/upcoming?driver_id=${lastUpcomingEventsDriver.id}&discipline=${lastUpcomingEventsDriver.primary_discipline || 'gt'}&limit=${EVENT_PAGE_SIZE}&offset=0`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    upcomingEventsCache = page;
    dashboardEventsList.innerHTML = page.length
      ? page.map((ev) => renderEventCard(ev, lastUpcomingEventsDriver)).join('')
      : '<div role="listitem">No upcoming events.</div>';
    if (upcomingEventsScrollEl) upcomingEventsScrollEl.scrollTop = 0;
  } catch (_) {}
}

async function resetPastEventsToFirstPage() {
  if (!dashboardPastEventsList || !lastPastEventsDriver) return;
  try {
    const url = `/api/events/past?driver_id=${lastPastEventsDriver.id}&limit=${EVENT_PAGE_SIZE}&offset=0`;
    const res = await apiFetch(url);
    if (!res.ok) return;
    const page = await res.json();
    pastEventsCache = page;
    dashboardPastEventsList.innerHTML = page.length
      ? page.map((ev) => renderEventCard(ev, lastPastEventsDriver)).join('')
      : '<div role="listitem">No past events.</div>';
    if (pastEventsScrollEl) pastEventsScrollEl.scrollTop = 0;
  } catch (_) {}
}

function setupEventsScrollLoad() {
  if (upcomingEventsScrollEl) {
    upcomingEventsScrollEl.addEventListener('scroll', () => {
      const { scrollTop, clientHeight, scrollHeight } = upcomingEventsScrollEl;
      if (scrollHeight <= clientHeight) return;
      if (scrollTop + clientHeight < scrollHeight - 30) return;
      fetchUpcomingNextPage();
    });
  }
  if (pastEventsScrollEl) {
    pastEventsScrollEl.addEventListener('scroll', () => {
      const { scrollTop, clientHeight, scrollHeight } = pastEventsScrollEl;
      if (scrollHeight <= clientHeight) return;
      if (scrollTop + clientHeight < scrollHeight - 30) return;
      fetchPastNextPage();
    });
  }
}
setupEventsScrollLoad();

function resetParticipationsToFirstPage() {
  participationDisplayLimit = PARTICIPATION_PAGE_SIZE;
  if (!dashboardParticipationsList || !lastDriverParticipations.length) return;
  const initial = lastDriverParticipations.slice(0, participationDisplayLimit);
  dashboardParticipationsList.innerHTML = initial.map((item) => renderParticipationCard(item)).join('');
  if (participationScrollEl) participationScrollEl.scrollTop = 0;
}

function setupParticipationScrollLoad() {
  if (!participationScrollEl || !dashboardParticipationsList) return;
  participationScrollEl.addEventListener('scroll', () => {
    const { scrollTop, clientHeight, scrollHeight } = participationScrollEl;
    if (scrollHeight <= clientHeight) return;
    if (scrollTop + clientHeight < scrollHeight - 30) return;
    if (participationDisplayLimit >= lastDriverParticipations.length) return;
    const nextLimit = Math.min(participationDisplayLimit + PARTICIPATION_PAGE_SIZE, lastDriverParticipations.length);
    const slice = lastDriverParticipations.slice(participationDisplayLimit, nextLimit);
    const html = slice.map((item) => renderParticipationCard(item)).join('');
    if (html) dashboardParticipationsList.insertAdjacentHTML('beforeend', html);
    participationDisplayLimit = nextLimit;
  });
}
setupParticipationScrollLoad();

window.addEventListener('cabinet-tab-change', (e) => {
  if (e.detail?.tab === 'events') {
    resetUpcomingEventsToFirstPage();
    resetPastEventsToFirstPage();
  }
  if (e.detail?.tab === 'overview') {
    resetParticipationsToFirstPage();
  }
});

export const loadDashboardEvents = async (driver) => {
  if (!dashboardEventsList && !upcomingEventsList) return;
  if (!driver) {
    lastDriverForEvents = null;
    lastDashboardEventsData = [];
    lastDashboardPastEventsData = [];
    lastUpcomingEventsData = [];
    upcomingEventsCache = [];
    pastEventsCache = [];
    lastUpcomingEventsDriver = null;
    lastPastEventsDriver = null;
    hideEventDetail();
    loadActiveRace(null);
    if (dashboardEventsList) {
      dashboardEventsList.innerHTML = '<div role="listitem">Log in to load events.</div>';
    }
    if (upcomingEventsList) setList(upcomingEventsList, [], 'Log in to load events.');
    if (dashboardPastEventsList) {
      dashboardPastEventsList.innerHTML = '<div role="listitem">No past events.</div>';
    }
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
    if (forRecent) {
      const participation = lastDriverParticipations.find((p) => p.event_id === event.id);
      const partState = participation ? String(participation.participation_state || '').toLowerCase() : '';
      if (partState === 'completed') {
        statusSuffix = ` • ${EVENT_STATUS_LABELS.completed}`;
      } else if (partState === 'started') {
        statusSuffix = ` • ${EVENT_STATUS_LABELS.in_progress}`;
      } else if (event.start_time_utc) {
        const status = getEventStatus(event);
        if (status) statusSuffix = ` • ${EVENT_STATUS_LABELS[status]}`;
      }
    }
    return `${event.title} · ${sessionLabel} · ${event.format_type}${gameLabel}${timeLabel}${statusSuffix}`;
  };
  try {
    const discipline = driver.primary_discipline || 'gt';
    const [eventsRes, upcomingCountRes, pastCountRes, upcomingPageRes, pastPageRes] = await Promise.all([
      apiFetch(`/api/events?driver_id=${driver.id}&same_tier=${sameTier}&rig_filter=${sameTier}`),
      apiFetch(`/api/events/upcoming/count?driver_id=${driver.id}`),
      apiFetch(`/api/events/past/count?driver_id=${driver.id}`),
      apiFetch(`/api/events/upcoming?driver_id=${driver.id}&discipline=${discipline}&limit=${EVENT_PAGE_SIZE}&offset=0`),
      apiFetch(`/api/events/past?driver_id=${driver.id}&limit=${EVENT_PAGE_SIZE}&offset=0`),
    ]);
    if (!eventsRes.ok) throw new Error('failed');
    const events = await eventsRes.json();

    const waitingOrUpcoming = events.filter((e) => {
      if (!e.start_time_utc) return false;
      const startMs = new Date(e.start_time_utc).getTime();
      return !Number.isNaN(startMs) && startMs > now;
    });
    lastDashboardEventsData = [...waitingOrUpcoming].sort(
      (a, b) => new Date(a.start_time_utc).getTime() - new Date(b.start_time_utc).getTime()
    );

    const RECENT_DAYS_MS = 30 * 24 * 60 * 60 * 1000;
    const cutoffMs = now - RECENT_DAYS_MS;
    lastDashboardPastEventsData = events
      .filter((e) => {
        if (!e.start_time_utc) return false;
        const startMs = new Date(e.start_time_utc).getTime();
        return !Number.isNaN(startMs) && startMs < now && startMs >= cutoffMs;
      })
      .sort((a, b) => new Date(b.start_time_utc).getTime() - new Date(a.start_time_utc).getTime());


    lastUpcomingEventsDriver = driver;
    lastPastEventsDriver = driver;
    if (upcomingCountRes.ok) {
      const { total } = await upcomingCountRes.json();
      upcomingEventsTotalCount = total ?? 0;
    }
    if (pastCountRes.ok) {
      const { total } = await pastCountRes.json();
      pastEventsTotalCount = total ?? 0;
    }

    let upcomingPage = [];
    if (upcomingPageRes.ok) upcomingPage = await upcomingPageRes.json();
    upcomingEventsCache = Array.isArray(upcomingPage) ? upcomingPage : [];
    if (dashboardEventsList) {
      if (!upcomingEventsCache.length) {
        dashboardEventsList.innerHTML = '<div role="listitem">No upcoming events.</div>';
      } else {
        dashboardEventsList.innerHTML = upcomingEventsCache.map((ev) => renderEventCard(ev, driver)).join('');
      }
    }

    let pastPage = [];
    if (pastPageRes.ok) pastPage = await pastPageRes.json();
    pastEventsCache = Array.isArray(pastPage) ? pastPage : [];
    if (dashboardPastEventsList) {
      if (!pastEventsCache.length) {
        dashboardPastEventsList.innerHTML = '<div role="listitem">No past events.</div>';
      } else {
        dashboardPastEventsList.innerHTML = pastEventsCache.map((ev) => renderEventCard(ev, driver)).join('');
      }
    }

    const noEventsFromApi = !events || events.length === 0;
    const hintNoEvents = noEventsFromApi && driver.sim_games && driver.sim_games.length
      ? 'No events for your selected games. Add ACC (or your sim) in Profile → Sim games to see test events.'
      : null;
    lastUpcomingEventsData = upcomingEventsCache;
    if (upcomingEventsList) {
      const emptyText = hintNoEvents || (driver.sim_games && driver.sim_games.length
        ? 'No upcoming events for your games.'
        : 'No upcoming events. Add sim games to see events.');
      setEventListWithRegister(upcomingEventsList, lastUpcomingEventsData, driver, emptyText, formatEventItem);
    }
    loadActiveRace(driver);
  } catch (err) {
    if (dashboardEventsList) {
      dashboardEventsList.innerHTML = '<div role="listitem">Unable to load events.</div>';
    }
    if (dashboardPastEventsList) {
      dashboardPastEventsList.innerHTML = '<div role="listitem">Unable to load events.</div>';
    }
    if (upcomingEventsList) {
      setList(upcomingEventsList, [], 'Unable to load events.');
    }
  }
};

if (typeof document !== 'undefined') {
  initDashboardEventsRegisterDelegation();
  initTaskDetailDelegation();
}
