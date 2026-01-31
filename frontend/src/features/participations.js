import { apiFetch } from '../api/client.js';
import { getFormValue } from '../utils/dom.js';
import { parseOptionalInt, parseOptionalFloat, parseJsonField, parseDateTime } from '../utils/parse.js';

const participationForm = document.querySelector('[data-participation-form]');
const participationStatus = document.querySelector('[data-participation-status]');
const participationList = document.querySelector('[data-participation-list]');

export const loadParticipations = async () => {
  if (!participationList) return;
  participationList.innerHTML = '<li>Loading...</li>';
  try {
    const res = await apiFetch('/api/participations');
    if (!res.ok) throw new Error('failed');
    const participations = await res.json();
    if (!participations.length) {
      participationList.innerHTML = '<li>No participations yet.</li>';
      return;
    }
    participationList.innerHTML = participations
      .slice(0, 5)
      .map(
        (item) =>
          `<li>${item.discipline} - ${item.status} / ${item.driver_id.slice(0, 8)}...</li>`
      )
      .join('');
  } catch (err) {
    participationList.innerHTML = '<li>Unable to load participations.</li>';
  }
};

const prefillEventIdFromStorage = () => {
  try {
    const preferred = sessionStorage.getItem('operations.preferredEventId');
    if (!preferred) return;
    const sel = document.querySelector('#participationEventId');
    if (!sel) return;
    const found = Array.from(sel.options).some((o) => o.value === preferred);
    if (found) {
      sel.value = preferred;
    } else {
      const opt = document.createElement('option');
      opt.value = preferred;
      opt.textContent = `${preferred.slice(0, 8)}…`;
      sel.appendChild(opt);
      sel.value = preferred;
    }
    sessionStorage.removeItem('operations.preferredEventId');
  } catch (_) {}
};

const loadDriversForPicker = async () => {
  const sel = document.querySelector('#participationDriverId');
  if (!sel) return;
  try {
    const res = await apiFetch('/api/drivers?limit=200');
    if (!res.ok) return;
    const list = await res.json();
    sel.replaceChildren(sel.querySelector('option[value=""]') || document.createElement('option'));
    const first = sel.options[0];
    if (!first) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '— Select driver —';
      sel.appendChild(opt);
    }
    list.forEach((d) => {
      const opt = document.createElement('option');
      opt.value = d.id;
      opt.textContent = `${d.id.slice(0, 8)}… ${d.primary_discipline ?? ''}`.trim() || d.id;
      sel.appendChild(opt);
    });
  } catch (_) {}
};

const loadEventsForPicker = async () => {
  const sel = document.querySelector('#participationEventId');
  if (!sel) return;
  try {
    const res = await apiFetch('/api/events?limit=200');
    if (!res.ok) return;
    const list = await res.json();
    const keepFirst = sel.querySelector('option[value=""]');
    sel.replaceChildren(keepFirst || document.createElement('option'));
    if (!keepFirst) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '— Select event —';
      sel.insertBefore(opt, sel.firstChild);
    }
    list.forEach((e) => {
      const opt = document.createElement('option');
      opt.value = e.id;
      opt.textContent = `${e.title ?? e.id} — ${e.format_type ?? ''}`.trim().slice(0, 60) || e.id;
      sel.appendChild(opt);
    });
    prefillEventIdFromStorage();
  } catch (_) {}
};

export const initParticipations = () => {
  if (!participationForm || !participationStatus) return;
  prefillEventIdFromStorage();
  window.addEventListener('hashchange', prefillEventIdFromStorage);
  loadDriversForPicker();
  loadEventsForPicker();
  participationForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const driverId = getFormValue(participationForm, '#participationDriverId');
    const eventId = getFormValue(participationForm, '#participationEventId');
    if (!driverId || !eventId) {
      participationStatus.textContent = 'Driver and event required.';
      return;
    }
    const rawMetricsValue = getFormValue(participationForm, '#participationRawMetrics');
    const rawMetrics = parseJsonField(rawMetricsValue);
    if (rawMetrics === null) {
      participationStatus.textContent = 'Raw metrics must be valid JSON.';
      return;
    }
    participationStatus.textContent = 'Saving participation...';
    try {
      const res = await apiFetch('/api/participations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          driver_id: driverId,
          event_id: eventId,
          discipline: getFormValue(participationForm, '#participationDiscipline') || 'gt',
          status: getFormValue(participationForm, '#participationStatus') || 'finished',
          position_overall: parseOptionalInt(getFormValue(participationForm, '#participationPositionOverall')),
          position_class: parseOptionalInt(getFormValue(participationForm, '#participationPositionClass')),
          laps_completed: parseOptionalInt(getFormValue(participationForm, '#participationLaps')) || 0,
          incidents_count: parseOptionalInt(getFormValue(participationForm, '#participationIncidents')) || 0,
          penalties_count: parseOptionalInt(getFormValue(participationForm, '#participationPenalties')) || 0,
          pace_delta: parseOptionalFloat(getFormValue(participationForm, '#participationPaceDelta')),
          consistency_score: parseOptionalFloat(
            getFormValue(participationForm, '#participationConsistency')
          ),
          raw_metrics: rawMetrics || {},
          started_at: parseDateTime(getFormValue(participationForm, '#participationStartedAt')),
          finished_at: parseDateTime(getFormValue(participationForm, '#participationFinishedAt'))
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        participationStatus.textContent = err.detail || 'Save failed.';
        return;
      }
      participationStatus.textContent = 'Participation saved.';
      await loadParticipations();
    } catch (err) {
      participationStatus.textContent = 'Save failed.';
    }
  });
};
