import { apiFetch } from '../api/client.js';
import { setList } from '../utils/dom.js';
import { formatDateTime } from '../utils/format.js';
import { parseOptionalInt } from '../utils/parse.js';
import { isAdminUser } from '../state/session.js';

const userList = document.querySelector('[data-admin-user-list]');
const eventList = document.querySelector('[data-admin-event-list]');
const statsList = document.querySelector('[data-admin-live-stats]');
const refreshButton = document.querySelector('[data-admin-refresh-events]');
const eventsFilterForm = document.querySelector('[data-admin-events-filter]');
const eventClassificationBlock = document.querySelector('[data-admin-event-classification]');
const recentParticipationsList = document.querySelector('[data-admin-recent-participations]');
const recentIncidentsList = document.querySelector('[data-admin-recent-incidents]');
const playerForm = document.querySelector('[data-admin-player-form]');
const playerStatus = document.querySelector('[data-admin-player-status]');
const playerSummary = document.querySelector('[data-admin-player-summary]');
const playerParticipations = document.querySelector('[data-admin-player-participations]');
const adminUserSearchForm = document.querySelector('[data-admin-user-search-form]');
const adminUserSearchInput = document.querySelector('[data-admin-user-search-input]');
const adminUserSearchOutput = document.querySelector('[data-admin-user-search-output]');
const adminParticipationSearchForm = document.querySelector('[data-admin-participation-search-form]');
const adminParticipationSearchInput = document.querySelector('[data-admin-participation-search-input]');
const adminParticipationSearchOutput = document.querySelector('[data-admin-participation-search-output]');
const profileForm = document.querySelector('[data-admin-player-profile-form]');
const profileStatus = document.querySelector('[data-admin-player-profile-status]');
const playerCrsBlock = document.querySelector('[data-admin-player-crs]');

let currentAdminPlayer = null;
let adminUsersCache = [];

const safeSetList = (element, items, emptyText) => {
  if (!element) return;
  setList(element, items, emptyText);
};

const renderAdminUserList = (users = []) => {
  if (!userList) return;

  if (!users.length) {
    userList.textContent = 'No accounts yet.';
    return;
  }

  const fragment = document.createDocumentFragment();

  users.forEach(user => {
    const li = document.createElement('li');
    li.className = 'admin-user-row';
    li.dataset.adminUserId = user.id;
    li.dataset.adminUserDriverId = user.driver_id ?? '';

    const email = user.email ?? '—';
    const role = user.role ?? '—';
    const completion = user.completion_percent != null ? `${user.completion_percent}%` : '—';
    const driverLabel = user.driver_id ? `Driver ${user.driver_id.slice(0, 8)}…` : '—';

    const span = document.createElement('span');
    span.textContent = `${email} · ${role} · ${completion}`;
    li.appendChild(span);
    if (user.driver_id) {
      const link = document.createElement('button');
      link.type = 'button';
      link.className = 'btn link';
      link.textContent = driverLabel;
      link.title = user.driver_id;
      li.appendChild(link);
    } else {
      const muted = document.createElement('span');
      muted.className = 'muted';
      muted.textContent = ' — no driver';
      li.appendChild(muted);
    }

    fragment.appendChild(li);
  });

  userList.replaceChildren(fragment);
};

const loadAdminUsers = async () => {
  if (!isAdminUser() || !userList) return [];
  userList.innerHTML = '<li>Loading users...</li>';
  try {
    const res = await apiFetch('/api/admin/users');
    if (!res.ok) throw new Error('failed');
    const users = await res.json();
    adminUsersCache = users;
    renderAdminUserList(users);
    return users;
  } catch (err) {
    userList.innerHTML = '<li>Unable to load users.</li>';
    return [];
  }
};

const getEventsFilter = () => {
  if (!eventsFilterForm) return {};
  const game = eventsFilterForm.querySelector('#adminEventsGame')?.value?.trim() || '';
  const dateFrom = eventsFilterForm.querySelector('#adminEventsDateFrom')?.value || '';
  const dateTo = eventsFilterForm.querySelector('#adminEventsDateTo')?.value || '';
  return { game, dateFrom, dateTo };
};

const loadAdminEvents = async (filterOverrides = {}) => {
  if (!isAdminUser() || !eventList) return [];
  const { game, dateFrom, dateTo } = { ...getEventsFilter(), ...filterOverrides };
  eventList.innerHTML = '<li>Loading events...</li>';
  if (eventClassificationBlock) eventClassificationBlock.innerHTML = '';
  try {
    const params = new URLSearchParams();
    if (game) params.set('game', game);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const res = await apiFetch(`/api/events?${params.toString()}`);
    if (!res.ok) throw new Error('failed');
    const events = await res.json();
    eventList.replaceChildren();
    if (!events.length) {
      eventList.innerHTML = '<li>No events.</li>';
      return events;
    }
    events.slice(0, 50).forEach((event) => {
      const li = document.createElement('li');
      li.className = 'admin-event-row';
      li.dataset.adminEventId = event.id;
      const span = document.createElement('span');
      const sessionLabel = event.session_type === 'training' ? 'Training' : 'Race';
      span.textContent = `${event.title ?? event.id} — ${sessionLabel} — ${event.format_type ?? '—'} (${event.game ?? '—'})`;
      li.appendChild(span);
      eventList.appendChild(li);
    });
    return events;
  } catch (err) {
    eventList.innerHTML = '<li>Unable to load events.</li>';
    return [];
  }
};

const loadEventClassification = async (eventId) => {
  if (!eventClassificationBlock) return;
  eventClassificationBlock.innerHTML = '<span class="muted">Loading classification…</span>';
  try {
    const res = await apiFetch(`/api/events/${eventId}/classification`);
    if (!res.ok) {
      eventClassificationBlock.innerHTML = '<span class="muted">No classification.</span>';
      return;
    }
    const c = await res.json();
    const html = renderOutputGrid([
      ['Tier', c.tier_label ?? c.event_tier],
      ['Difficulty', c.difficulty_score],
      ['Seriousness', c.seriousness_score],
      ['Realism', c.realism_score],
      ['Created', formatDateTime(c.created_at)]
    ]) + `<p><button type="button" class="btn primary" data-admin-create-participation-for-event data-event-id="${eventId}">Create participation</button></p>`;
    eventClassificationBlock.innerHTML = html;
    const btn = eventClassificationBlock.querySelector('[data-admin-create-participation-for-event]');
    if (btn) {
      btn.addEventListener('click', () => {
        try {
          sessionStorage.setItem('operations.preferredEventId', btn.dataset.eventId || '');
        } catch (_) {}
        window.location.hash = 'operations';
      });
    }
  } catch {
    eventClassificationBlock.innerHTML = '<span class="muted">Classification unavailable.</span>';
  }
};

const updateAdminStats = (metrics) => {
  if (!statsList) return;
  if (metrics && typeof metrics.users === 'number') {
    const entries = [
      `Users: ${metrics.users}`,
      `Drivers: ${metrics.drivers ?? 0}`,
      `Events: ${metrics.events ?? 0}`,
      `Participations: ${metrics.participations ?? 0}`
    ];
    safeSetList(statsList, entries, 'No admin metrics yet.');
    return;
  }
  safeSetList(statsList, [], 'No admin metrics yet.');
};

const formatValue = (value) => {
  if (Array.isArray(value)) return value.length ? value.join(', ') : '—';
  if (value === null || value === undefined || value === '') return '—';
  return value;
};

const renderOutputGrid = (rows) => {
  return `<div class="admin-output-grid">${rows
    .map(([label, value]) => `<div><span>${label}</span><div>${formatValue(value)}</div></div>`)
    .join('')}</div>`;
};

const setOutput = (element, html, emptyText) => {
  if (!element) return;
  element.innerHTML = html || `<span class="muted">${emptyText}</span>`;
};

const loadAdminPlayerByDriverId = async (driverId) => {
  if (!playerStatus) return false;
  if (!driverId) {
    playerStatus.textContent = 'Enter a player or driver ID.';
    return false;
  }
  try {
    playerStatus.textContent = 'Loading player...';
    const res = await apiFetch(`/api/drivers/${driverId}`);
    if (!res.ok) {
      playerStatus.textContent = 'Driver not found.';
      setOutput(playerSummary, '', 'Provide an ID to inspect a driver.');
      return false;
    }
    const driver = await res.json();
    const [profile, inspectRes] = await Promise.all([
      loadPlayerProfile(driver.user_id),
      apiFetch(`/api/admin/driver/inspect?q=${encodeURIComponent(driver.id)}`)
    ]);
    currentAdminPlayer = { driver, profile };
    if (inspectRes.ok) {
      const inspected = await inspectRes.json();
      const summaryHtml = renderOutputGrid([
        ['Driver ID', inspected.driver_id],
        ['Email', inspected.driver_email],
        ['Primary discipline', inspected.primary_discipline],
        ['Sim games', inspected.sim_games]
      ]);
      setOutput(playerSummary, summaryHtml, 'Provide an ID to inspect a driver.');
      const participationItems = (inspected.participations || []).map(
        (item) => `${item.id} — ${formatDateTime(item.started_at)}`
      );
      setList(playerParticipations, participationItems, 'No participations loaded.');
    } else {
      setOutput(playerSummary, '', 'Unable to load player summary.');
      setList(playerParticipations, [], 'No participations loaded.');
    }
    fillProfileForm(profile);
    await loadPlayerCrsLicenses(driver.id, driver.primary_discipline || 'gt');
    playerStatus.textContent = 'Player loaded.';
    return true;
  } catch (err) {
    playerStatus.textContent = 'Unable to load player.';
    setOutput(playerSummary, '', 'Provide an ID to inspect a driver.');
    if (playerCrsBlock) playerCrsBlock.innerHTML = '';
    return false;
  }
};

const loadPlayerCrsLicenses = async (driverId, discipline) => {
  if (!playerCrsBlock) return;
  playerCrsBlock.innerHTML = '<span class="muted">Loading CRS &amp; licenses…</span>';
  try {
    const [licRes, crsRes] = await Promise.all([
      apiFetch(`/api/licenses?driver_id=${encodeURIComponent(driverId)}`),
      apiFetch(`/api/crs/latest?driver_id=${encodeURIComponent(driverId)}&discipline=${encodeURIComponent(discipline)}`)
    ]);
    const parts = [];
    if (licRes.ok) {
      const licenses = await licRes.json();
      if (Array.isArray(licenses) && licenses.length) {
        parts.push(
          '<p class="card-title">Licenses</p>',
          '<ul class="list">',
          licenses.map((l) => `<li>${l.discipline ?? '—'} · ${l.level_code ?? '—'} (${formatDateTime(l.awarded_at)})</li>`).join(''),
          '</ul>'
        );
      }
    }
    if (crsRes.ok) {
      const crs = await crsRes.json();
      parts.push(
        '<p class="card-title">Latest CRS</p>',
        renderOutputGrid([
          ['Discipline', crs.discipline],
          ['Score', crs.score],
          ['Computed at', formatDateTime(crs.computed_at)]
        ])
      );
    }
    if (parts.length) {
      playerCrsBlock.innerHTML = `<div class="admin-output-crs-inner">${parts.join('')}</div>`;
    } else {
      playerCrsBlock.innerHTML = '<span class="muted">No CRS or licenses.</span>';
    }
  } catch {
    playerCrsBlock.innerHTML = '<span class="muted">CRS &amp; licenses unavailable.</span>';
  }
};

const renderParticipationOutput = (data) => {
  const header = renderOutputGrid([
    ['Driver ID', data.driver_id],
    ['Driver email', data.driver_email],
    ['Primary discipline', data.primary_discipline],
    ['Sim games', data.sim_games]
  ]);
  if (!data.participations || !data.participations.length) {
    return `${header}<span class="muted">No participations found.</span>`;
  }
  const items = data.participations.map((item) => {
    const rows = [
      ['ID', item.id],
      ['Event ID', item.event_id],
      ['Game', item.game],
      ['Discipline', item.discipline],
      ['Status', item.status],
      ['Position overall', item.position_overall],
      ['Position class', item.position_class],
      ['Laps completed', item.laps_completed],
      ['Incidents', item.incidents_count],
      ['Penalties', item.penalties_count],
      ['Pace delta', item.pace_delta],
      ['Consistency score', item.consistency_score],
      ['Started at', formatDateTime(item.started_at)],
      ['Finished at', formatDateTime(item.finished_at)],
      ['Created at', formatDateTime(item.created_at)],
      ['Raw metrics', item.raw_metrics ? JSON.stringify(item.raw_metrics) : '—']
    ];
    return `<div class="admin-output-item">${renderOutputGrid(rows)}</div>`;
  });
  return `${header}<div class="admin-output-list">${items.join('')}</div>`;
};

const loadPlayerProfile = async (userId) => {
  if (!userId) return null;
  try {
    const res = await apiFetch(`/api/admin/profiles/${userId}`);
    if (!res.ok) throw new Error('failed');
    return await res.json();
  } catch (err) {
    return null;
  }
};

const fillProfileForm = (profile) => {
  if (!profileForm) return;
  const disciplineInput = profileForm.querySelector('#adminProfileDiscipline');
  const platformsInput = profileForm.querySelector('#adminProfilePlatforms');
  const experienceInput = profileForm.querySelector('#adminProfileExperience');
  const ageInput = profileForm.querySelector('#adminProfileAge');
  if (disciplineInput) disciplineInput.value = profile?.primary_discipline || '';
  if (platformsInput) platformsInput.value = (profile?.sim_platforms || []).join(', ');
  if (experienceInput) experienceInput.value = profile?.experience_years ?? '';
  if (ageInput) ageInput.value = profile?.age ?? '';
};

const parsePlatforms = (value) =>
  (value || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const loadAdminMetrics = async () => {
  if (!isAdminUser()) return null;
  try {
    const res = await apiFetch('/api/metrics');
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
};

const loadAdminRecentParticipations = async () => {
  if (!isAdminUser() || !recentParticipationsList) return [];
  try {
    const res = await apiFetch('/api/participations?limit=20');
    if (!res.ok) return [];
    const list = await res.json();
    const items = list.map((p) => `${p.driver_id?.slice(0, 8) ?? '—'}… · ${p.event_id?.slice(0, 8) ?? '—'}… · ${p.status ?? '—'}`);
    safeSetList(recentParticipationsList, items, 'No participations.');
    return list;
  } catch {
    safeSetList(recentParticipationsList, [], 'Unable to load.');
    return [];
  }
};

const loadAdminRecentIncidents = async () => {
  if (!isAdminUser() || !recentIncidentsList) return [];
  try {
    const res = await apiFetch('/api/incidents?limit=20');
    if (!res.ok) return [];
    const list = await res.json();
    const items = list.map((i) => `${i.incident_type ?? '—'} · severity ${i.severity ?? '—'} · ${i.participation_id?.slice(0, 8) ?? '—'}…`);
    safeSetList(recentIncidentsList, items, 'No incidents.');
    return list;
  } catch {
    safeSetList(recentIncidentsList, [], 'Unable to load.');
    return [];
  }
};

export const refreshAdminPanel = async () => {
  if (!isAdminUser()) return;
  const [users, events, metrics] = await Promise.all([
    loadAdminUsers(),
    loadAdminEvents(),
    loadAdminMetrics()
  ]);
  if (metrics) {
    updateAdminStats(metrics);
  } else {
    updateAdminStats({
      users: users?.length ?? 0,
      drivers: 0,
      events: events?.length ?? 0,
      participations: 0
    });
  }
  await Promise.all([loadAdminRecentParticipations(), loadAdminRecentIncidents()]);
};

export const initAdminPanel = () => {
  if (refreshButton) {
    refreshButton.addEventListener('click', () => {
      refreshAdminPanel();
    });
  }
  if (eventsFilterForm) {
    eventsFilterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      loadAdminEvents();
    });
  }
  if (eventList) {
    eventList.addEventListener('click', (e) => {
      const li = e.target.closest('li[data-admin-event-id]');
      if (!li) return;
      const eventId = li.dataset.adminEventId;
      if (eventId) loadEventClassification(eventId);
    });
  }
  if (userList) {
    userList.addEventListener('click', async (event) => {
      const item = event.target.closest('li[data-admin-user-id]');
      if (!item) return;
      const driverId = item.dataset.adminUserDriverId;
      if (!driverId) {
        if (playerStatus) playerStatus.textContent = 'User has no driver profile.';
        return;
      }
      await loadAdminPlayerByDriverId(driverId);
    });
  }
  if (adminUserSearchForm) {
    adminUserSearchForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = adminUserSearchInput ? adminUserSearchInput.value.trim() : '';
      if (!email) {
        setOutput(adminUserSearchOutput, '', 'Enter an email to search.');
        return;
      }
      setOutput(adminUserSearchOutput, '', 'Searching...');
      try {
        const res = await apiFetch(`/api/admin/search/user?email=${encodeURIComponent(email)}`);
        if (!res.ok) {
          setOutput(adminUserSearchOutput, '', 'Not found.');
          return;
        }
        const data = await res.json();
        const output = renderOutputGrid([
          ['Driver ID', data.driver_id],
          ['Email', data.email],
          ['Primary discipline', data.primary_discipline],
          ['Sim games', data.sim_games]
        ]);
        setOutput(adminUserSearchOutput, output, 'Not found.');
      } catch (err) {
        setOutput(adminUserSearchOutput, '', 'Search failed.');
      }
    });
  }
  if (adminParticipationSearchForm) {
    adminParticipationSearchForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const query = adminParticipationSearchInput ? adminParticipationSearchInput.value.trim() : '';
      if (!query) {
        setOutput(adminParticipationSearchOutput, '', 'Enter a driver ID or email.');
        return;
      }
      setOutput(adminParticipationSearchOutput, '', 'Searching...');
      try {
        const res = await apiFetch(`/api/admin/search/participations?q=${encodeURIComponent(query)}`);
        if (!res.ok) {
          setOutput(adminParticipationSearchOutput, '', 'Not found.');
          return;
        }
        const data = await res.json();
        setOutput(adminParticipationSearchOutput, renderParticipationOutput(data), 'Not found.');
      } catch (err) {
        setOutput(adminParticipationSearchOutput, '', 'Search failed.');
      }
    });
  }
  if (playerForm) {
    playerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!playerStatus) return;
      const input = playerForm.querySelector('#adminPlayerId');
      const playerId = input ? input.value.trim() : '';
      if (!playerId) {
        playerStatus.textContent = 'Enter a player or driver ID.';
        return;
      }
      await loadAdminPlayerByDriverId(playerId);
    });
  }
  if (profileForm) {
    profileForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!profileStatus) return;
      if (!currentAdminPlayer) {
        profileStatus.textContent = 'Load a player first.';
        return;
      }
      const userId = currentAdminPlayer.driver.user_id;
      if (!userId) {
        profileStatus.textContent = 'Player has no profile.';
        return;
      }
      profileStatus.textContent = 'Saving profile...';
      try {
        const discipline = profileForm.querySelector('#adminProfileDiscipline')?.value || null;
        const platforms = parsePlatforms(profileForm.querySelector('#adminProfilePlatforms')?.value || '');
        const experience = parseOptionalInt(profileForm.querySelector('#adminProfileExperience')?.value);
        const age = parseOptionalInt(profileForm.querySelector('#adminProfileAge')?.value);
        const res = await apiFetch(`/api/admin/profiles/${userId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            primary_discipline: discipline || null,
            sim_platforms: platforms,
            experience_years: experience,
            age,
          })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          profileStatus.textContent = err.detail || 'Save failed.';
          return;
        }
        const profile = await res.json();
        currentAdminPlayer.profile = profile;
        await loadAdminPlayerByDriverId(currentAdminPlayer.driver.id);
        profileStatus.textContent = 'Profile updated.';
      } catch (err) {
        profileStatus.textContent = 'Save failed.';
      }
    });
  }
};
