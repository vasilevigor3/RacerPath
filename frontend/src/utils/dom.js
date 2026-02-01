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
 * tasks: array of { id, name, ... }
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
      const name = escapeHtml(task.name ?? task.id);
      const taskId = escapeHtml(task.id);
      return `<li class="task-list-item"><button type="button" class="task-list-item__text btn-link" data-task-id="${taskId}">${name}</button></li>`;
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
