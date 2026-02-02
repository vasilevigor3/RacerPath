const escapeHtml = (s) => {
  if (typeof s !== 'string') return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
};

export const setList = (listEl, items, emptyText) => {
  if (!listEl) return;
  if (!items || items.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  listEl.innerHTML = items.map((item) => `<li>${escapeHtml(item)}</li>`).join('');
};

/**
 * Render license requirements as clickable rows; each item "CODE: ..." opens license detail.
 * requirements: array of strings (e.g. "E2: min CRS 100, tasks: ...")
 */
export const setLicenseReqsList = (listEl, requirements, emptyText) => {
  if (!listEl) return;
  if (!requirements || requirements.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  listEl.innerHTML = requirements
    .map((raw) => {
      const text = typeof raw === 'string' ? raw : String(raw);
      const colonIdx = text.indexOf(':');
      const code = colonIdx >= 0 ? text.slice(0, colonIdx).trim() : text.trim();
      const codeAttr = escapeHtml(code || '');
      const textAttr = escapeHtml(text);
      return `<li class="license-req-item"><button type="button" class="btn-link license-req-item__text" data-license-code="${codeAttr}">${textAttr}</button></li>`;
    })
    .join('');
};

/**
 * Render events as clickable rows; click opens event detail panel (no inline Register button).
 * events: array of { id, title, event_tier, ... }
 * driver: { id }
 * formatEventItem(event, forRecent): returns display string
 */
export const setEventListWithRegister = (listEl, events, driver, emptyText, formatEventItem) => {
  if (!listEl) return;
  if (!events || events.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  listEl.innerHTML = events
    .map((event) => {
      const text = formatEventItem(event, true);
      const eventId = escapeHtml(event.id);
      return `<li class="event-list-item"><button type="button" class="event-list-item__text btn-link" data-event-id="${eventId}" data-driver-id="${escapeHtml(driver?.id ?? '')}">${escapeHtml(text)}</button></li>`;
    })
    .join('');
};

/**
 * Render tasks as clickable rows; click opens task detail panel.
 * tasks: array of { id, code, name, ... } — display "CODE - Name"
 * emptyText: string when empty
 */
export const setTaskListClickable = (listEl, tasks, emptyText) => {
  if (!listEl) return;
  if (!tasks || tasks.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  listEl.innerHTML = tasks
    .map((task) => {
      const code = task.code ?? task.id ?? '';
      const name = task.name ?? task.id ?? '—';
      const label = code ? `${escapeHtml(code)} - ${escapeHtml(name)}` : escapeHtml(name);
      const taskId = escapeHtml(task.id);
      return `<li class="task-list-item"><button type="button" class="task-list-item__text btn-link" data-task-id="${taskId}">${label}</button></li>`;
    })
    .join('');
};

/** Slot label prefix -> slot value for matching items to special_events */
const RACE_OF_PREFIX_TO_SLOT = {
  'Race of the day:': 'race_of_day',
  'Race of the week:': 'race_of_week',
  'Race of the month:': 'race_of_month',
  'Race of the year:': 'race_of_year'
};

const COMPLETE_TASK_PREFIX = 'Complete task: ';

/**
 * Set "Next actions" Tasks column: items "Complete task: {name}" as clickable rows with data-task-id.
 * taskDefinitions: array of { id, name, ... } to resolve name -> id.
 */
export const setRecommendationTasksList = (listEl, taskItemStrings, taskDefinitions, emptyText) => {
  if (!listEl) return;
  if (!taskItemStrings || taskItemStrings.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  const byName = (taskDefinitions || []).reduce((acc, t) => {
    if (t.name) acc[t.name] = t;
    return acc;
  }, {});
  listEl.innerHTML = taskItemStrings
    .map((raw) => {
      const text = typeof raw === 'string' ? raw : String(raw);
      if (!text.startsWith(COMPLETE_TASK_PREFIX)) return '';
      const name = text.slice(COMPLETE_TASK_PREFIX.length).trim();
      const task = byName[name];
      const taskId = task ? task.id : '';
      const label = escapeHtml(text);
      if (taskId) {
        return `<li class="rec-item rec-item--clickable" data-task-id="${escapeHtml(taskId)}"><button type="button" class="rec-item__text btn-link">${label}</button></li>`;
      }
      return `<li class="rec-item">${label}</li>`;
    })
    .filter(Boolean)
    .join('') || `<li>${escapeHtml(emptyText)}</li>`;
};

/**
 * Set "Next actions" Race of d/w/m/y column: only "Race of day/week/month/year" items with countdown; click opens event.
 */
export const setRecommendationRacesList = (listEl, raceItemStrings, special_events, emptyText, formatCountdownFn) => {
  if (!listEl) return;
  if (!formatCountdownFn) formatCountdownFn = () => '';
  if (!raceItemStrings || raceItemStrings.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  const bySlot = (special_events || []).reduce((acc, se) => {
    if (se.slot && se.start_time_utc) acc[se.slot] = se;
    return acc;
  }, {});
  listEl.innerHTML = raceItemStrings
    .map((item) => {
      const text = typeof item === 'string' ? item : '';
      let slot = null;
      for (const [prefix] of Object.entries(RACE_OF_PREFIX_TO_SLOT)) {
        if (text.startsWith(prefix)) {
          slot = RACE_OF_PREFIX_TO_SLOT[prefix];
          break;
        }
      }
      const special = slot ? bySlot[slot] : null;
      const startUtc = special && special.start_time_utc != null
        ? (typeof special.start_time_utc === 'string' ? special.start_time_utc : (special.start_time_utc?.iso ? special.start_time_utc.iso() : String(special.start_time_utc)))
        : '';
      const countdown = startUtc
        ? `<span class="rec-countdown" data-start-utc="${escapeHtml(startUtc)}">${escapeHtml(formatCountdownFn(startUtc))}</span>`
        : '';
      const inner = `${escapeHtml(text)}${countdown ? `<br><small class="rec-countdown-wrap">${countdown}</small>` : ''}`;
      if (special && special.event_id) {
        const eventId = escapeHtml(String(special.event_id));
        return `<li class="rec-item rec-item--clickable" data-event-id="${eventId}"><button type="button" class="rec-item__text btn-link">${inner}</button></li>`;
      }
      return `<li class="rec-item">${inner}</li>`;
    })
    .join('');
};

/**
 * Set recommendation list with optional countdown timers for "Race of X" items.
 * special_events: [{ slot, label, start_time_utc, ... }]
 * Call tickRecommendationCountdowns() periodically to update countdowns.
 */
export const setRecommendationListWithCountdown = (listEl, items, special_events, emptyText, formatCountdownFn) => {
  if (!listEl) return;
  if (!formatCountdownFn) formatCountdownFn = () => '';
  if (!items || items.length === 0) {
    listEl.innerHTML = `<li>${escapeHtml(emptyText)}</li>`;
    return;
  }
  const bySlot = (special_events || []).reduce((acc, se) => {
    if (se.slot && se.start_time_utc) acc[se.slot] = se;
    return acc;
  }, {});
  listEl.innerHTML = items
    .map((item) => {
      const text = typeof item === 'string' ? item : '';
      let slot = null;
      for (const [prefix, s] of Object.entries(RACE_OF_PREFIX_TO_SLOT)) {
        if (text.startsWith(prefix)) {
          slot = s;
          break;
        }
      }
      const special = slot ? bySlot[slot] : null;
      const startUtc = special && special.start_time_utc != null
        ? (typeof special.start_time_utc === 'string' ? special.start_time_utc : (special.start_time_utc?.iso ? special.start_time_utc.iso() : String(special.start_time_utc)))
        : '';
      const countdown = startUtc
        ? `<span class="rec-countdown" data-start-utc="${escapeHtml(startUtc)}">${escapeHtml(formatCountdownFn(startUtc))}</span>`
        : '';
      const inner = `${escapeHtml(text)}${countdown ? `<br><small class="rec-countdown-wrap">${countdown}</small>` : ''}`;
      if (special && special.event_id) {
        const eventId = escapeHtml(String(special.event_id));
        return `<li class="rec-item rec-item--clickable" data-event-id="${eventId}"><button type="button" class="rec-item__text btn-link">${inner}</button></li>`;
      }
      return `<li class="rec-item">${inner}</li>`;
    })
    .join('');
};

/** Update all .rec-countdown elements with current countdown text. Call every second. */
export const tickRecommendationCountdowns = (listEl, formatCountdownFn) => {
  if (!listEl || !formatCountdownFn) return;
  listEl.querySelectorAll('.rec-countdown').forEach((el) => {
    const startUtc = el.getAttribute('data-start-utc');
    if (startUtc) el.textContent = formatCountdownFn(startUtc);
  });
};

export const getFormValue = (formEl, selector) => {
  const input = formEl ? formEl.querySelector(selector) : null;
  return input ? input.value.trim() : '';
};
