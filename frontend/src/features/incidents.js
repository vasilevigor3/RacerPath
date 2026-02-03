import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';
import { parseOptionalInt, parseDateTime } from '../utils/parse.js';

const incidentForm = document.querySelector('[data-incident-form]');
const incidentStatus = document.querySelector('[data-incident-status]');
const incidentList = document.querySelector('[data-incident-list]');
const incidentsTotalEls = document.querySelectorAll('[data-incidents-total], [data-incidents-total-card]');
const incidentsListView = document.querySelector('[data-incidents-list-view]');
const incidentDetailPanel = document.querySelector('[data-incident-detail]');
const incidentDetailType = document.querySelector('[data-incident-detail-type]');
const incidentDetailRace = document.querySelector('[data-incident-detail-race]');
const incidentDetailMeta = document.querySelector('[data-incident-detail-meta]');
const incidentDetailDesc = document.querySelector('[data-incident-detail-desc]');
const incidentDetailBack = document.querySelector('[data-incident-detail-back]');

let incidentsCache = [];

function setIncidentsTotal(total) {
  const value = total == null ? '0' : String(total);
  incidentsTotalEls.forEach((el) => { el.textContent = value; });
}

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { dateStyle: 'short' }) + ' ' + d.toLocaleTimeString(undefined, { timeStyle: 'short' });
  } catch (_) {
    return iso;
  }
}

function showIncidentDetail(item) {
  if (!incidentDetailPanel || !incidentDetailType || !incidentDetailRace || !incidentDetailMeta) return;
  const typeLabel = item.incident_type || '—';
  const severity = item.severity ? `S${item.severity}` : 'S1';
  incidentDetailType.textContent = `${typeLabel} · ${severity}`;
  incidentDetailRace.textContent = item.event_title ? `Race: ${item.event_title}` : '—';
  const metaParts = [];
  if (item.lap != null && item.lap !== undefined) metaParts.push(`Lap ${item.lap}`);
  if (item.event_start_time_utc) metaParts.push(formatDate(item.event_start_time_utc));
  if (item.created_at) metaParts.push(`Recorded: ${formatDate(item.created_at)}`);
  incidentDetailMeta.textContent = metaParts.length ? metaParts.join(' · ') : '—';
  incidentDetailDesc.textContent = item.description || '';
  incidentDetailDesc.style.display = item.description ? '' : 'none';
  if (incidentsListView) incidentsListView.classList.add('is-hidden');
  incidentDetailPanel.classList.remove('is-hidden');
}

function hideIncidentDetail() {
  if (incidentDetailPanel) incidentDetailPanel.classList.add('is-hidden');
  if (incidentsListView) incidentsListView.classList.remove('is-hidden');
}

function setupIncidentDetailListeners() {
  if (incidentList) {
    incidentList.addEventListener('click', (e) => {
      const card = e.target.closest('[data-incident-id]');
      if (!card) return;
      const id = card.getAttribute('data-incident-id');
      const item = incidentsCache.find((i) => i.id === id);
      if (item) showIncidentDetail(item);
    });
  }
  if (incidentDetailBack) {
    incidentDetailBack.addEventListener('click', hideIncidentDetail);
  }
}

setupIncidentDetailListeners();

export const loadIncidents = async (driver) => {
  if (!incidentList) return;
  incidentList.innerHTML = '<div role="listitem" class="incident-cards__loading">Loading...</div>';
  setIncidentsTotal(0);
  incidentsCache = [];
  try {
    const url = driver ? `/api/incidents?driver_id=${driver.id}&limit=200` : '/api/incidents?limit=200';
    const countUrl = driver ? `/api/incidents/count?driver_id=${driver.id}` : '/api/incidents/count';
    const [listRes, countRes] = await Promise.all([apiFetch(url), apiFetch(countUrl)]);
    if (!listRes.ok) throw new Error('failed');
    const incidents = await listRes.json();
    incidentsCache = incidents;
    if (countRes.ok) {
      const { total } = await countRes.json();
      setIncidentsTotal(total ?? 0);
    }
    if (!incidents.length) {
      incidentList.innerHTML = '<div role="listitem">No incidents yet.</div>';
      return;
    }
    incidentList.innerHTML = incidents
      .map((item) => {
        const typeLabel = item.incident_type || '—';
        const severity = item.severity ? `S${item.severity}` : 'S1';
        const race = item.event_title || '—';
        const lapHtml = item.lap != null && item.lap !== undefined
          ? `<span class="incident-card__lap">Lap ${item.lap}</span>`
          : '';
        return `<button type="button" class="incident-card" data-incident-id="${item.id}" role="listitem">
          <span class="incident-card__type">${typeLabel} · ${severity}</span>
          <span class="incident-card__race">${race}</span>
          ${lapHtml}
        </button>`;
      })
      .join('');
  } catch (err) {
    incidentList.innerHTML = '<div role="listitem">Unable to load incidents.</div>';
  }
};

const loadParticipationsForPicker = async () => {
  const sel = document.querySelector('#incidentParticipationId');
  if (!sel) return;
  try {
    const res = await apiFetch('/api/participations?limit=100');
    if (!res.ok) return;
    const list = await res.json();
    const keepFirst = sel.querySelector('option[value=""]');
    sel.replaceChildren(keepFirst || document.createElement('option'));
    if (!keepFirst) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '— Select participation —';
      sel.insertBefore(opt, sel.firstChild);
    }
    list.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.driver_id?.slice(0, 8) ?? '—'}… · ${p.event_id?.slice(0, 8) ?? '—'}… · ${p.status ?? ''}`.trim().slice(0, 50) || p.id;
      sel.appendChild(opt);
    });
  } catch (_) {}
};

export const initIncidents = () => {
  if (!incidentForm || !incidentStatus) return;
  loadParticipationsForPicker();
  incidentForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const participationId = getFormValue(incidentForm, '#incidentParticipationId');
    const incidentType = getFormValue(incidentForm, '#incidentType');
    if (!participationId || !incidentType) {
      incidentStatus.textContent = 'Participation and incident type required.';
      return;
    }
    incidentStatus.textContent = 'Saving incident...';
    try {
      const res = await apiFetch(`/api/participations/${participationId}/incidents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          participation_id: participationId,
          incident_type: incidentType,
          severity: parseOptionalInt(getFormValue(incidentForm, '#incidentSeverity')) || 1,
          lap: parseOptionalInt(getFormValue(incidentForm, '#incidentLap')),
          timestamp_utc: parseDateTime(getFormValue(incidentForm, '#incidentTimestamp')),
          description: getFormValue(incidentForm, '#incidentDescription') || null
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        incidentStatus.textContent = err.detail || 'Save failed.';
        return;
      }
      incidentStatus.textContent = 'Incident saved.';
      await loadIncidents();
    } catch (err) {
      incidentStatus.textContent = 'Save failed.';
    }
  });
};
