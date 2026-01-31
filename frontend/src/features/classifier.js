import { apiFetch } from '../api/client.js';
import { setList } from '../utils/dom.js';
import { fmt } from '../utils/format.js';
import { parseJsonField, parseDateTime } from '../utils/parse.js';
import { getSessionList } from '../utils/forms.js';

const form = document.querySelector('[data-classifier]');
const durationOutput = document.querySelector('[data-output="duration"]');
const gridOutput = document.querySelector('[data-output="grid"]');

const tierValue = document.getElementById('tierValue');
const tierNote = document.getElementById('tierNote');
const difficultyValue = document.getElementById('difficultyValue');
const seriousnessValue = document.getElementById('seriousnessValue');
const realismValue = document.getElementById('realismValue');
const capsApplied = document.getElementById('capsApplied');

const compatFormula = document.getElementById('compatFormula');
const compatGt = document.getElementById('compatGt');
const compatRally = document.getElementById('compatRally');
const compatKarting = document.getElementById('compatKarting');
const compatHistoric = document.getElementById('compatHistoric');

const saveEventButton = document.querySelector('[data-save-event]');
const eventStatus = document.querySelector('[data-event-status]');
const eventList = document.querySelector('[data-event-list]');

const updateRangeOutputs = () => {
  if (!form) return;
  if (durationOutput) durationOutput.textContent = form.duration.value;
  if (gridOutput) gridOutput.textContent = form.grid.value;
};

const buildPayload = () => {
  const pitRules = parseJsonField(form.pitRules.value);
  return {
    discipline: form.discipline.value,
    format: form.format.value,
    duration: Number(form.duration.value),
    grid: Number(form.grid.value),
    classes: Number(form.classes.value),
    schedule: form.schedule.value,
    damage: form.damage.value,
    penalties: form.penalties.value,
    fuel: form.fuel.value,
    tire: form.tire.value,
    weather: form.weather.value,
    stewarding: form.stewarding.value,
    night: form.night.checked,
    team: form.team.checked,
    license: form.license.value,
    official: form.official.checked,
    assists: form.assists.checked,
    track_type: form.trackType.value || null,
    surface_type: form.surfaceType.value || null,
    team_size_max: Number(form.teamSizeMax.value || 1),
    pit_rules: pitRules || {},
    rolling_start: form.rollingStart.checked,
    time_acceleration: form.timeAcceleration.checked,
    session_list: getSessionList()
  };
};

const parseCarClasses = (value) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

const buildEventPayload = () => {
  const pitRules = parseJsonField(form.pitRules.value);
  if (pitRules === null) {
    return { error: 'Pit rules must be valid JSON.' };
  }
  const teamSizeMin = Number.parseInt(form.teamSizeMin.value || '1', 10);
  const teamSizeMax = Number.parseInt(form.teamSizeMax.value || '1', 10);
  if (teamSizeMin > teamSizeMax) {
    return { error: 'Team size min cannot exceed max.' };
  }
  return {
    payload: {
      title: form.eventTitle.value.trim() || 'Untitled event',
      source: form.eventSource.value,
      game: form.eventGame.value || null,
      start_time_utc: parseDateTime(form.startTimeUtc.value),
      event_type: form.eventType.value,
      format_type: form.format.value,
      session_list: getSessionList(),
      team_size_min: teamSizeMin,
      team_size_max: teamSizeMax,
      rolling_start: form.rollingStart.checked,
      pit_rules: pitRules,
      duration_minutes: Number(form.duration.value),
      grid_size_expected: Number(form.grid.value),
      class_count: Number(form.classes.value),
      car_class_list: parseCarClasses(form.carClasses.value || ''),
      schedule_type: form.schedule.value,
      damage_model: form.damage.value,
      penalties: form.penalties.value,
      fuel_usage: form.fuel.value,
      tire_wear: form.tire.value,
      weather: form.weather.value,
      night: form.night.checked,
      time_acceleration: form.timeAcceleration.checked,
      surface_type: form.surfaceType.value || null,
      track_type: form.trackType.value || null,
      stewarding: form.stewarding.value === 'human' ? 'human_review' : form.stewarding.value,
      team_event: form.team.checked,
      license_requirement: form.license.value,
      official_event: form.official.checked,
      assists_allowed: form.assists.checked
    }
  };
};

let controller;
const updateClassification = async () => {
  updateRangeOutputs();
  if (controller) {
    controller.abort();
  }
  controller = new AbortController();

  try {
    const res = await apiFetch('/api/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload()),
      signal: controller.signal
    });

    if (!res.ok) {
      throw new Error('Request failed');
    }

    const data = await res.json();
    if (tierValue) tierValue.textContent = data.event_tier;
    if (tierNote) tierNote.textContent = data.tier_label;
    if (difficultyValue) difficultyValue.textContent = fmt(data.difficulty_score);
    if (seriousnessValue) seriousnessValue.textContent = fmt(data.seriousness_score);
    if (realismValue) realismValue.textContent = fmt(data.realism_score);

    if (compatFormula) compatFormula.textContent = fmt(data.discipline_compatibility.formula);
    if (compatGt) compatGt.textContent = fmt(data.discipline_compatibility.gt);
    if (compatRally) compatRally.textContent = fmt(data.discipline_compatibility.rally);
    const kartingValue =
      data.discipline_compatibility.karting ?? data.discipline_compatibility.offroad ?? 0;
    if (compatKarting) compatKarting.textContent = fmt(kartingValue);
    if (compatHistoric) compatHistoric.textContent = fmt(data.discipline_compatibility.historic);

    if (capsApplied) {
      if (data.caps_applied.length) {
        capsApplied.textContent = `Caps applied: ${data.caps_applied.join(', ')}`;
      } else {
        capsApplied.textContent = 'Caps applied: none';
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      return;
    }
    if (capsApplied) capsApplied.textContent = 'Caps applied: unable to reach API';
  }
};

export const loadEvents = async () => {
  if (!eventList) return;
  eventList.innerHTML = '<li>Loading...</li>';
  try {
    const res = await apiFetch('/api/events');
    if (!res.ok) throw new Error('failed');
    const events = await res.json();
    if (!events.length) {
      eventList.innerHTML = '<li>No events yet.</li>';
      return;
    }
    eventList.innerHTML = events
      .slice(0, 5)
      .map(
        (event) =>
          `<li><strong>${event.title}</strong> - ${event.format_type} / ${event.duration_minutes}m (${event.game || 'Any'})</li>`
      )
      .join('');
  } catch (err) {
    eventList.innerHTML = '<li>Unable to load events.</li>';
  }
};

const saveEvent = async () => {
  if (!form || !eventStatus) return;
  const title = form.eventTitle.value.trim();
  if (!title) {
    eventStatus.textContent = 'Please enter an event title.';
    return;
  }
  const result = buildEventPayload();
  if (result.error) {
    eventStatus.textContent = result.error;
    return;
  }
  eventStatus.textContent = 'Saving event...';
  try {
    const res = await apiFetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result.payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      eventStatus.textContent = err.detail || 'Save failed.';
      return;
    }
    eventStatus.textContent = 'Event saved.';
    await loadEvents();
  } catch (err) {
    eventStatus.textContent = 'Save failed.';
  }
};

export const initClassifier = () => {
  if (form) {
    form.addEventListener('input', updateClassification);
    form.addEventListener('change', updateClassification);
    updateClassification();
  }
  if (saveEventButton) {
    saveEventButton.addEventListener('click', saveEvent);
  }
};
