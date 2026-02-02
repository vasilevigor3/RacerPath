import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';
import { parseOptionalInt, parseDateTime } from '../utils/parse.js';

const incidentForm = document.querySelector('[data-incident-form]');
const incidentStatus = document.querySelector('[data-incident-status]');
const incidentList = document.querySelector('[data-incident-list]');
const incidentsTotalEls = document.querySelectorAll('[data-incidents-total], [data-incidents-total-card]');

function setIncidentsTotal(total) {
  const value = total == null ? '0' : String(total);
  incidentsTotalEls.forEach((el) => { el.textContent = value; });
}

export const loadIncidents = async (driver) => {
  if (!incidentList) return;
  incidentList.innerHTML = '<li>Loading...</li>';
  setIncidentsTotal(0);
  try {
    const url = driver ? `/api/incidents?driver_id=${driver.id}` : '/api/incidents';
    const countUrl = driver ? `/api/incidents/count?driver_id=${driver.id}` : '/api/incidents/count';
    const [listRes, countRes] = await Promise.all([apiFetch(url), apiFetch(countUrl)]);
    if (!listRes.ok) throw new Error('failed');
    const incidents = await listRes.json();
    if (countRes.ok) {
      const { total } = await countRes.json();
      setIncidentsTotal(total ?? 0);
    }
    if (!incidents.length) {
      incidentList.innerHTML = '<li>No incidents yet.</li>';
      return;
    }
    incidentList.innerHTML = incidents
      .slice(0, 6)
      .map((item) => {
        const lapLabel = item.lap !== null && item.lap !== undefined ? `Lap ${item.lap}` : 'Lap n/a';
        const severity = item.severity ? `S${item.severity}` : 'S1';
        return `<li>${item.incident_type} • ${severity} • ${lapLabel}</li>`;
      })
      .join('');
  } catch (err) {
    incidentList.innerHTML = '<li>Unable to load incidents.</li>';
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
