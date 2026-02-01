import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client.js';

const MetricsBoard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    apiFetch('/api/metrics')
      .then((res) => {
        if (cancelled) return;
        if (res.status === 403) return null;
        if (!res.ok) throw new Error(res.statusText || 'Failed to load metrics');
        return res.json();
      })
      .then((data) => {
        if (!cancelled) setMetrics(data ?? null);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || 'Error');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="admin-metrics-board" aria-busy="true">Loading…</div>;
  if (error) return <div className="admin-metrics-board admin-metrics-board--error">{error}</div>;
  if (!metrics) return null;

  const items = [
    ['Users', metrics.users],
    ['Drivers', metrics.drivers],
    ['Events', metrics.events],
    ['Classifications', metrics.classifications],
    ['Participations', metrics.participations],
  ];

  return (
    <div className="admin-metrics-board" role="status" aria-label="Live metrics">
      <dl className="admin-metrics-board__list">
        {items.map(([label, value]) => (
          <div key={label} className="admin-metrics-board__item">
            <dd className="admin-metrics-board__value">{value ?? 0}</dd>
            <dt className="admin-metrics-board__term">{label}</dt>
          </div>
        ))}
      </dl>
    </div>
  );
};

const formatDate = (d) => {
  if (!d) return '—';
  try {
    const dt = new Date(d);
    return Number.isNaN(dt.getTime()) ? '—' : dt.toLocaleString();
  } catch {
    return '—';
  }
};

const INCIDENT_TYPES = ['Contact', 'Off-track', 'Track limits', 'Unsafe rejoin', 'Blocking', 'Avoidable contact', 'Mechanical', 'Other'];
const PARTICIPATION_STATUSES = ['finished', 'dnf', 'dsq', 'dns'];
const PARTICIPATION_STATES = ['registered', 'withdrawn', 'started', 'completed'];
const DISCIPLINES = ['gt', 'formula', 'rally', 'karting', 'historic'];
const GAMES = ['', 'iRacing', 'ACC', 'rFactor 2', 'AMS2', 'AC', 'F1', 'Other'];
const EVENT_TIERS = ['E0', 'E1', 'E2', 'E3', 'E4', 'E5'];
const SPECIAL_EVENT_OPTIONS = [
  { value: '', label: '—' },
  { value: 'race_of_day', label: 'Race of the day' },
  { value: 'race_of_week', label: 'Race of the week' },
  { value: 'race_of_month', label: 'Race of the month' },
  { value: 'race_of_year', label: 'Race of the year' },
];
const SESSION_TYPES = [
  { value: 'race', label: 'Race' },
  { value: 'training', label: 'Training' },
];
const SCHEDULE_TYPES = ['weekly', 'daily', 'tournament', 'special'];
const EVENT_TYPES = ['circuit', 'rally', 'drift', 'time_attack'];
const FORMAT_TYPES = ['sprint', 'endurance', 'hotlap'];
const DAMAGE_MODELS = ['off', 'reduced', 'full', 'limited'];
const RULES_TOGGLES = ['off', 'reduced', 'realistic', 'real', 'normal', 'strict', 'standard'];
const WEATHER_TYPES = ['fixed', 'dynamic'];
const STEWARDING_TYPES = ['none', 'automated', 'live', 'human_review'];
const LICENSE_REQUIREMENTS = ['none', 'entry', 'rookie', 'intermediate', 'pro'];

const toDatetimeLocal = (iso) => {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${day}T${h}:${min}`;
  } catch {
    return '';
  }
};

const AdminConstructors = () => {
  const [eventForm, setEventForm] = useState({ title: '', source: 'admin', game: '', country: '', city: '', start_time_utc: '', finished_time_utc: '', event_tier: 'E2', special_event: '', session_type: 'race' });
  const [eventLoading, setEventLoading] = useState(false);
  const [eventMsg, setEventMsg] = useState(null);

  const [updateEventId, setUpdateEventId] = useState('');
  const [updateEventForm, setUpdateEventForm] = useState({
    title: '', source: '', game: '', country: '', city: '', start_time_utc: '', finished_time_utc: '', event_tier: '', special_event: '', session_type: 'race',
    schedule_type: 'weekly', event_type: 'circuit', format_type: 'sprint',
    team_size_min: '1', team_size_max: '1', duration_minutes: '0', grid_size_expected: '0', class_count: '1',
    damage_model: 'off', penalties: 'off', fuel_usage: 'off', tire_wear: 'off',
    weather: 'fixed', night: false, time_acceleration: false,
    stewarding: 'none', team_event: false, license_requirement: 'none', official_event: false, assists_allowed: false,
    surface_type: '', track_type: '', rolling_start: false,
  });
  const [updateEventLoading, setUpdateEventLoading] = useState(false);
  const [updateEventFetching, setUpdateEventFetching] = useState(false);
  const [updateEventMsg, setUpdateEventMsg] = useState(null);

  const [partForm, setPartForm] = useState({
    driver_id: '', event_id: '', discipline: 'gt', status: 'finished',
    participation_state: 'registered', position_overall: '', laps_completed: '0',
  });
  const [partLoading, setPartLoading] = useState(false);
  const [partMsg, setPartMsg] = useState(null);

  const [incidentForm, setIncidentForm] = useState({
    participation_id: '', incident_type: 'Contact', severity: '1', lap: '', description: '',
  });
  const [incidentLoading, setIncidentLoading] = useState(false);
  const [incidentMsg, setIncidentMsg] = useState(null);

  const [updatePartForm, setUpdatePartForm] = useState({
    participation_id: '', status: '', participation_state: '', position_overall: '',
    laps_completed: '', started_at: '', finished_at: '',
  });
  const [updatePartLoading, setUpdatePartLoading] = useState(false);
  const [updatePartMsg, setUpdatePartMsg] = useState(null);

  const fetchEventForUpdate = async () => {
    const id = updateEventId?.trim();
    if (!id) return;
    setUpdateEventMsg(null);
    setUpdateEventFetching(true);
    try {
      const [eventRes, classRes] = await Promise.all([
        apiFetch(`/api/events/${encodeURIComponent(id)}`),
        apiFetch(`/api/events/${encodeURIComponent(id)}/classification`),
      ]);
      if (!eventRes.ok) {
        const d = await eventRes.json().catch(() => ({}));
        setUpdateEventMsg(d.detail || 'Event not found');
        return;
      }
      const event = await eventRes.json();
      let eventTier = '';
      if (classRes.ok) {
        const cls = await classRes.json();
        eventTier = cls.event_tier || '';
      }
      setUpdateEventForm({
        title: event.title || '',
        source: event.source || '',
        game: event.game || '',
        country: event.country || '',
        city: event.city || '',
        start_time_utc: toDatetimeLocal(event.start_time_utc),
        finished_time_utc: toDatetimeLocal(event.finished_time_utc),
        event_tier: eventTier,
        session_type: event.session_type || 'race',
        schedule_type: event.schedule_type || 'weekly',
        event_type: event.event_type || 'circuit',
        format_type: event.format_type || 'sprint',
        team_size_min: String(event.team_size_min ?? 1),
        team_size_max: String(event.team_size_max ?? 1),
        duration_minutes: String(event.duration_minutes ?? 0),
        grid_size_expected: String(event.grid_size_expected ?? 0),
        class_count: String(event.class_count ?? 1),
        damage_model: event.damage_model || 'off',
        penalties: event.penalties || 'off',
        fuel_usage: event.fuel_usage || 'off',
        tire_wear: event.tire_wear || 'off',
        weather: event.weather || 'fixed',
        night: Boolean(event.night),
        time_acceleration: Boolean(event.time_acceleration),
        stewarding: event.stewarding || 'none',
        team_event: Boolean(event.team_event),
        license_requirement: event.license_requirement || 'none',
        official_event: Boolean(event.official_event),
        assists_allowed: Boolean(event.assists_allowed),
        surface_type: event.surface_type || '',
        track_type: event.track_type || '',
        rolling_start: Boolean(event.rolling_start),
      });
      setUpdateEventMsg('Event loaded. Edit and submit to update.');
    } catch (err) {
      setUpdateEventMsg(err?.message || 'Failed to load event');
    } finally {
      setUpdateEventFetching(false);
    }
  };

  const updateEventSubmit = (e) => {
    e.preventDefault();
    const id = updateEventId?.trim();
    if (!id) return;
    setUpdateEventLoading(true);
    setUpdateEventMsg(null);
    const body = {};
    const f = updateEventForm;
    if (f.title?.trim()) body.title = f.title.trim();
    if (f.source?.trim()) body.source = f.source.trim();
    if (f.game !== undefined) body.game = f.game?.trim() || null;
    if (f.country !== undefined) body.country = f.country?.trim() || null;
    if (f.city !== undefined) body.city = f.city?.trim() || null;
    if (f.start_time_utc?.trim()) {
      const v = f.start_time_utc.trim();
      body.start_time_utc = v.endsWith('Z') ? v : (/T\d{2}:\d{2}$/.test(v) ? v + ':00.000Z' : v + '.000Z');
    }
    if (f.finished_time_utc !== undefined) {
      const v = f.finished_time_utc?.trim();
      body.finished_time_utc = v ? (v.endsWith('Z') ? v : (/T\d{2}:\d{2}$/.test(v) ? v + ':00.000Z' : v + '.000Z')) : null;
    }
    if (f.event_tier?.trim()) body.event_tier = f.event_tier.trim();
    if (f.special_event !== undefined) body.special_event = f.special_event?.trim() || null;
    if (f.session_type !== undefined) body.session_type = f.session_type || 'race';
    if (f.schedule_type) body.schedule_type = f.schedule_type;
    if (f.event_type) body.event_type = f.event_type;
    if (f.format_type) body.format_type = f.format_type;
    if (f.team_size_min !== undefined) body.team_size_min = parseInt(f.team_size_min, 10);
    if (f.team_size_max !== undefined) body.team_size_max = parseInt(f.team_size_max, 10);
    if (f.duration_minutes !== undefined) body.duration_minutes = parseInt(f.duration_minutes, 10);
    if (f.grid_size_expected !== undefined) body.grid_size_expected = parseInt(f.grid_size_expected, 10);
    if (f.class_count !== undefined) body.class_count = parseInt(f.class_count, 10);
    if (f.damage_model) body.damage_model = f.damage_model;
    if (f.penalties) body.penalties = f.penalties;
    if (f.fuel_usage) body.fuel_usage = f.fuel_usage;
    if (f.tire_wear) body.tire_wear = f.tire_wear;
    if (f.weather) body.weather = f.weather;
    if (f.night !== undefined) body.night = f.night;
    if (f.time_acceleration !== undefined) body.time_acceleration = f.time_acceleration;
    if (f.stewarding) body.stewarding = f.stewarding;
    if (f.team_event !== undefined) body.team_event = f.team_event;
    if (f.license_requirement) body.license_requirement = f.license_requirement;
    if (f.official_event !== undefined) body.official_event = f.official_event;
    if (f.assists_allowed !== undefined) body.assists_allowed = f.assists_allowed;
    if (f.surface_type !== undefined) body.surface_type = f.surface_type?.trim() || null;
    if (f.track_type !== undefined) body.track_type = f.track_type?.trim() || null;
    if (f.rolling_start !== undefined) body.rolling_start = f.rolling_start;
    apiFetch(`/api/events/${encodeURIComponent(id)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail?.[0]?.msg || d.detail || res.statusText))))
      .then(() => setUpdateEventMsg('Event updated'))
      .catch((err) => setUpdateEventMsg(err?.message || 'Error'))
      .finally(() => setUpdateEventLoading(false));
  };

  const createEvent = (e) => {
    e.preventDefault();
    if (!eventForm.title?.trim() || !eventForm.source?.trim()) return;
    setEventLoading(true);
    setEventMsg(null);
    const body = {
      title: eventForm.title.trim(),
      source: eventForm.source.trim(),
      game: eventForm.game?.trim() || null,
      country: eventForm.country?.trim() || null,
      city: eventForm.city?.trim() || null,
      event_tier: (eventForm.event_tier && eventForm.event_tier.trim()) ? eventForm.event_tier.trim() : 'E2',
      special_event: eventForm.special_event?.trim() || null,
      session_type: eventForm.session_type || 'race',
      start_time_utc: (() => {
        const v = eventForm.start_time_utc?.trim();
        if (!v) return null;
        if (v.endsWith('Z')) return v;
        return /T\d{2}:\d{2}$/.test(v) ? v + ':00.000Z' : v + '.000Z';
      })(),
      finished_time_utc: (() => {
        const v = eventForm.finished_time_utc?.trim();
        if (!v) return null;
        if (v.endsWith('Z')) return v;
        return /T\d{2}:\d{2}$/.test(v) ? v + ':00.000Z' : v + '.000Z';
      })(),
    };
    apiFetch('/api/events', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail?.[0]?.msg || d.detail || res.statusText))))
      .then((data) => setEventMsg(`Event created: ${data.id}`))
      .catch((err) => setEventMsg(err?.message || 'Error'))
      .finally(() => setEventLoading(false));
  };

  const createParticipation = (e) => {
    e.preventDefault();
    if (!partForm.driver_id?.trim() || !partForm.event_id?.trim()) return;
    setPartLoading(true);
    setPartMsg(null);
    const body = {
      driver_id: partForm.driver_id.trim(),
      event_id: partForm.event_id.trim(),
      discipline: partForm.discipline,
      status: partForm.status,
      participation_state: partForm.participation_state,
      position_overall: partForm.position_overall ? parseInt(partForm.position_overall, 10) : null,
      laps_completed: parseInt(partForm.laps_completed, 10) || 0,
    };
    apiFetch('/api/participations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail?.[0]?.msg || d.detail || res.statusText))))
      .then((data) => setPartMsg(`Participation created: ${data.id}`))
      .catch((err) => setPartMsg(err?.message || 'Error'))
      .finally(() => setPartLoading(false));
  };

  const createIncident = (e) => {
    e.preventDefault();
    const pid = incidentForm.participation_id?.trim();
    if (!pid) return;
    setIncidentLoading(true);
    setIncidentMsg(null);
    const body = {
      participation_id: pid,
      incident_type: incidentForm.incident_type,
      severity: parseInt(incidentForm.severity, 10) || 1,
      lap: incidentForm.lap ? parseInt(incidentForm.lap, 10) : null,
      description: incidentForm.description?.trim() || null,
    };
    apiFetch(`/api/participations/${encodeURIComponent(pid)}/incidents`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail?.[0]?.msg || d.detail || res.statusText))))
      .then((data) => setIncidentMsg(`Incident created: ${data.id}`))
      .catch((err) => setIncidentMsg(err?.message || 'Error'))
      .finally(() => setIncidentLoading(false));
  };

  const updateParticipation = (e) => {
    e.preventDefault();
    const pid = updatePartForm.participation_id?.trim();
    if (!pid) return;
    setUpdatePartLoading(true);
    setUpdatePartMsg(null);
    const body = {};
    if (updatePartForm.status) body.status = updatePartForm.status;
    if (updatePartForm.participation_state) body.participation_state = updatePartForm.participation_state;
    if (updatePartForm.position_overall !== '') body.position_overall = parseInt(updatePartForm.position_overall, 10);
    if (updatePartForm.laps_completed !== '') body.laps_completed = parseInt(updatePartForm.laps_completed, 10);
    if (updatePartForm.started_at) body.started_at = updatePartForm.started_at;
    if (updatePartForm.finished_at) body.finished_at = updatePartForm.finished_at;
    apiFetch(`/api/admin/participations/${encodeURIComponent(pid)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail?.[0]?.msg || d.detail || res.statusText))))
      .then(() => setUpdatePartMsg('Participation updated'))
      .catch((err) => setUpdatePartMsg(err?.message || 'Error'))
      .finally(() => setUpdatePartLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">Constructors (driver flow)</h3>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Event</h4>
        <form onSubmit={createEvent} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Title</label>
            <input type="text" value={eventForm.title} onChange={(e) => setEventForm((f) => ({ ...f, title: e.target.value }))} placeholder="Event title" required className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Source</label>
            <input type="text" value={eventForm.source} onChange={(e) => setEventForm((f) => ({ ...f, source: e.target.value }))} placeholder="admin" className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Game</label>
            <select value={eventForm.game} onChange={(e) => setEventForm((f) => ({ ...f, game: e.target.value }))} className="admin-constructors__input">
              {GAMES.map((g) => (
                <option key={g || '—'} value={g}>{g || '—'}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Tier</label>
            <select value={eventForm.event_tier} onChange={(e) => setEventForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input" required>
              {EVENT_TIERS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event type (race/training)</label>
            <select value={eventForm.session_type} onChange={(e) => setEventForm((f) => ({ ...f, session_type: e.target.value }))} className="admin-constructors__input">
              {SESSION_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Start time (UTC)</label>
            <input type="datetime-local" value={eventForm.start_time_utc} onChange={(e) => setEventForm((f) => ({ ...f, start_time_utc: e.target.value }))} className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Finished time (UTC)</label>
            <input type="datetime-local" value={eventForm.finished_time_utc} onChange={(e) => setEventForm((f) => ({ ...f, finished_time_utc: e.target.value }))} className="admin-constructors__input" placeholder="optional — from external API or set later" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Race of</label>
            <select value={eventForm.special_event} onChange={(e) => setEventForm((f) => ({ ...f, special_event: e.target.value }))} className="admin-constructors__input">
              {SPECIAL_EVENT_OPTIONS.map((o) => (
                <option key={o.value || '—'} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Country / City</label>
            <input type="text" value={eventForm.country} onChange={(e) => setEventForm((f) => ({ ...f, country: e.target.value }))} placeholder="country" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={eventForm.city} onChange={(e) => setEventForm((f) => ({ ...f, city: e.target.value }))} placeholder="city" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={eventLoading}>{eventLoading ? '…' : 'Create Event'}</button>
          {eventMsg && <p className="admin-constructors__msg" role="status">{eventMsg}</p>}
        </form>
      </section>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Update Event</h4>
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">Event ID</label>
          <input type="text" value={updateEventId} onChange={(e) => setUpdateEventId(e.target.value)} placeholder="event uuid" className="admin-constructors__input" />
          <button type="button" className="btn ghost admin-constructors__btn" onClick={fetchEventForUpdate} disabled={updateEventFetching}>{updateEventFetching ? '…' : 'Fetch'}</button>
        </div>
        {updateEventMsg && <p className="admin-constructors__msg" role="status">{updateEventMsg}</p>}
        <form onSubmit={updateEventSubmit} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Title</label>
            <input type="text" value={updateEventForm.title} onChange={(e) => setUpdateEventForm((f) => ({ ...f, title: e.target.value }))} placeholder="Event title" className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Source</label>
            <input type="text" value={updateEventForm.source} onChange={(e) => setUpdateEventForm((f) => ({ ...f, source: e.target.value }))} className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Game</label>
            <select value={updateEventForm.game} onChange={(e) => setUpdateEventForm((f) => ({ ...f, game: e.target.value }))} className="admin-constructors__input">
              {GAMES.map((g) => (<option key={g || '—'} value={g}>{g || '—'}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Tier</label>
            <select value={updateEventForm.event_tier} onChange={(e) => setUpdateEventForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input">
              <option value="">—</option>
              {EVENT_TIERS.map((t) => (<option key={t} value={t}>{t}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Race of</label>
            <select value={updateEventForm.special_event} onChange={(e) => setUpdateEventForm((f) => ({ ...f, special_event: e.target.value }))} className="admin-constructors__input">
              {SPECIAL_EVENT_OPTIONS.map((o) => (
                <option key={o.value || '—'} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Start time (UTC)</label>
            <input type="datetime-local" value={updateEventForm.start_time_utc} onChange={(e) => setUpdateEventForm((f) => ({ ...f, start_time_utc: e.target.value }))} className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Finished time (UTC)</label>
            <input type="datetime-local" value={updateEventForm.finished_time_utc} onChange={(e) => setUpdateEventForm((f) => ({ ...f, finished_time_utc: e.target.value }))} className="admin-constructors__input" placeholder="optional" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Country / City</label>
            <input type="text" value={updateEventForm.country} onChange={(e) => setUpdateEventForm((f) => ({ ...f, country: e.target.value }))} placeholder="country" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={updateEventForm.city} onChange={(e) => setUpdateEventForm((f) => ({ ...f, city: e.target.value }))} placeholder="city" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event type (race/training) / Schedule / Type / Format</label>
            <select value={updateEventForm.session_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, session_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {SESSION_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <select value={updateEventForm.schedule_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, schedule_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {SCHEDULE_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.event_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, event_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {EVENT_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.format_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, format_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {FORMAT_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Team size / Duration / Grid / Classes</label>
            <input type="number" min="1" max="8" value={updateEventForm.team_size_min} onChange={(e) => setUpdateEventForm((f) => ({ ...f, team_size_min: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" placeholder="team min" />
            <input type="number" min="1" max="8" value={updateEventForm.team_size_max} onChange={(e) => setUpdateEventForm((f) => ({ ...f, team_size_max: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" placeholder="team max" />
            <input type="number" min="0" value={updateEventForm.duration_minutes} onChange={(e) => setUpdateEventForm((f) => ({ ...f, duration_minutes: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" placeholder="duration" />
            <input type="number" min="0" value={updateEventForm.grid_size_expected} onChange={(e) => setUpdateEventForm((f) => ({ ...f, grid_size_expected: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" placeholder="grid" />
            <input type="number" min="1" max="6" value={updateEventForm.class_count} onChange={(e) => setUpdateEventForm((f) => ({ ...f, class_count: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" placeholder="classes" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Damage / Penalties / Fuel / Tire / Weather</label>
            <select value={updateEventForm.damage_model} onChange={(e) => setUpdateEventForm((f) => ({ ...f, damage_model: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {DAMAGE_MODELS.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.penalties} onChange={(e) => setUpdateEventForm((f) => ({ ...f, penalties: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.fuel_usage} onChange={(e) => setUpdateEventForm((f) => ({ ...f, fuel_usage: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.tire_wear} onChange={(e) => setUpdateEventForm((f) => ({ ...f, tire_wear: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.weather} onChange={(e) => setUpdateEventForm((f) => ({ ...f, weather: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {WEATHER_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Stewarding / License</label>
            <select value={updateEventForm.stewarding} onChange={(e) => setUpdateEventForm((f) => ({ ...f, stewarding: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {STEWARDING_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.license_requirement} onChange={(e) => setUpdateEventForm((f) => ({ ...f, license_requirement: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {LICENSE_REQUIREMENTS.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Night / Time accel / Team / Official / Assists / Rolling</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.night} onChange={(e) => setUpdateEventForm((f) => ({ ...f, night: e.target.checked }))} /> Night</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.time_acceleration} onChange={(e) => setUpdateEventForm((f) => ({ ...f, time_acceleration: e.target.checked }))} /> Time accel</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.team_event} onChange={(e) => setUpdateEventForm((f) => ({ ...f, team_event: e.target.checked }))} /> Team</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.official_event} onChange={(e) => setUpdateEventForm((f) => ({ ...f, official_event: e.target.checked }))} /> Official</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.assists_allowed} onChange={(e) => setUpdateEventForm((f) => ({ ...f, assists_allowed: e.target.checked }))} /> Assists</label>
            <label className="admin-constructors__label"><input type="checkbox" checked={updateEventForm.rolling_start} onChange={(e) => setUpdateEventForm((f) => ({ ...f, rolling_start: e.target.checked }))} /> Rolling start</label>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Surface / Track</label>
            <input type="text" value={updateEventForm.surface_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, surface_type: e.target.value }))} placeholder="surface_type" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={updateEventForm.track_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, track_type: e.target.value }))} placeholder="track_type" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={updateEventLoading}>{updateEventLoading ? '…' : 'Update Event'}</button>
        </form>
      </section>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Participation</h4>
        <form onSubmit={createParticipation} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Driver ID</label>
            <input type="text" value={partForm.driver_id} onChange={(e) => setPartForm((f) => ({ ...f, driver_id: e.target.value }))} placeholder="driver uuid" required className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event ID</label>
            <input type="text" value={partForm.event_id} onChange={(e) => setPartForm((f) => ({ ...f, event_id: e.target.value }))} placeholder="event uuid" required className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Discipline</label>
            <select value={partForm.discipline} onChange={(e) => setPartForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input">
              {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Status</label>
            <select value={partForm.status} onChange={(e) => setPartForm((f) => ({ ...f, status: e.target.value }))} className="admin-constructors__input">
              {PARTICIPATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">State</label>
            <select value={partForm.participation_state} onChange={(e) => setPartForm((f) => ({ ...f, participation_state: e.target.value }))} className="admin-constructors__input">
              {PARTICIPATION_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Position / Laps</label>
            <input type="number" min="0" value={partForm.position_overall} onChange={(e) => setPartForm((f) => ({ ...f, position_overall: e.target.value }))} placeholder="position" className="admin-constructors__input admin-constructors__input--short" />
            <input type="number" min="0" value={partForm.laps_completed} onChange={(e) => setPartForm((f) => ({ ...f, laps_completed: e.target.value }))} placeholder="laps" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={partLoading}>{partLoading ? '…' : 'Create Participation'}</button>
          {partMsg && <p className="admin-constructors__msg" role="status">{partMsg}</p>}
        </form>
      </section>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Incident</h4>
        <form onSubmit={createIncident} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Participation ID</label>
            <input type="text" value={incidentForm.participation_id} onChange={(e) => setIncidentForm((f) => ({ ...f, participation_id: e.target.value }))} placeholder="participation uuid" required className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Type / Severity / Lap</label>
            <select value={incidentForm.incident_type} onChange={(e) => setIncidentForm((f) => ({ ...f, incident_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {INCIDENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input type="number" min="1" max="5" value={incidentForm.severity} onChange={(e) => setIncidentForm((f) => ({ ...f, severity: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
            <input type="number" min="0" value={incidentForm.lap} onChange={(e) => setIncidentForm((f) => ({ ...f, lap: e.target.value }))} placeholder="lap" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Description</label>
            <input type="text" value={incidentForm.description} onChange={(e) => setIncidentForm((f) => ({ ...f, description: e.target.value }))} placeholder="optional" className="admin-constructors__input" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={incidentLoading}>{incidentLoading ? '…' : 'Create Incident'}</button>
          {incidentMsg && <p className="admin-constructors__msg" role="status">{incidentMsg}</p>}
        </form>
      </section>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Update Participation</h4>
        <form onSubmit={updateParticipation} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Participation ID</label>
            <input type="text" value={updatePartForm.participation_id} onChange={(e) => setUpdatePartForm((f) => ({ ...f, participation_id: e.target.value }))} placeholder="participation uuid" required className="admin-constructors__input" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Status / State</label>
            <select value={updatePartForm.status} onChange={(e) => setUpdatePartForm((f) => ({ ...f, status: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              <option value="">—</option>
              {PARTICIPATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={updatePartForm.participation_state} onChange={(e) => setUpdatePartForm((f) => ({ ...f, participation_state: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              <option value="">—</option>
              {PARTICIPATION_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Position / Laps</label>
            <input type="number" min="0" value={updatePartForm.position_overall} onChange={(e) => setUpdatePartForm((f) => ({ ...f, position_overall: e.target.value }))} placeholder="position" className="admin-constructors__input admin-constructors__input--short" />
            <input type="number" min="0" value={updatePartForm.laps_completed} onChange={(e) => setUpdatePartForm((f) => ({ ...f, laps_completed: e.target.value }))} placeholder="laps" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Started / Finished (ISO)</label>
            <input type="text" value={updatePartForm.started_at} onChange={(e) => setUpdatePartForm((f) => ({ ...f, started_at: e.target.value }))} placeholder="2025-01-31T12:00:00Z" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={updatePartForm.finished_at} onChange={(e) => setUpdatePartForm((f) => ({ ...f, finished_at: e.target.value }))} placeholder="2025-01-31T14:00:00Z" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={updatePartLoading}>{updatePartLoading ? '…' : 'Update Participation'}</button>
          {updatePartMsg && <p className="admin-constructors__msg" role="status">{updatePartMsg}</p>}
        </form>
      </section>
    </div>
  );
};

const TierRulesPanel = () => {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingTier, setEditingTier] = useState(null);
  const [editForm, setEditForm] = useState({ min_events: '', difficulty_threshold: '', required_license_codes: '' });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  const loadRules = () => {
    setLoading(true);
    setError(null);
    apiFetch('/api/admin/tier-rules')
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed');
        return res.json();
      })
      .then(setRules)
      .catch((err) => setError(err?.message || 'Error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadRules(); }, []);

  const startEdit = (rule) => {
    setEditingTier(rule.tier);
    setEditForm({ min_events: String(rule.min_events), difficulty_threshold: String(rule.difficulty_threshold) });
    setSaveMsg(null);
  };

  const saveRule = (e) => {
    e.preventDefault();
    const tier = editingTier?.trim();
    if (!tier) return;
    setSaveLoading(true);
    setSaveMsg(null);
    const body = {};
    if (editForm.min_events !== '') body.min_events = parseInt(editForm.min_events, 10);
    if (editForm.difficulty_threshold !== '') body.difficulty_threshold = parseFloat(editForm.difficulty_threshold);
    if (editForm.required_license_codes !== undefined) {
      body.required_license_codes = editForm.required_license_codes.trim() ? editForm.required_license_codes.split(',').map((s) => s.trim()).filter(Boolean) : [];
    }
    apiFetch(`/api/admin/tier-rules/${encodeURIComponent(tier)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setSaveMsg('Saved');
        loadRules();
        setEditingTier(null);
      })
      .catch((err) => setSaveMsg(err?.message || 'Error'))
      .finally(() => setSaveLoading(false));
  };

  const ensureRule = (tier) => {
    const existing = rules.find((r) => r.tier === tier);
    if (existing) startEdit(existing);
    else {
      setEditingTier(tier);
      setEditForm({ min_events: '5', difficulty_threshold: '0' });
      setSaveMsg(null);
    }
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">Tier progression (next_tier_progress_percent)</h3>
      <p className="admin-constructors__hint">Rules per tier: min_events with difficulty_score &gt; threshold; required_license_codes (comma-separated). E5 = 100%.</p>
      {loading && <p className="admin-constructors__msg">Loading…</p>}
      {error && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{error}</p>}
      {!loading && !error && (
        <>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Rules</h4>
            <table className="admin-constructors__table" role="grid">
              <thead>
                <tr>
                  <th>Tier</th>
                  <th>min_events</th>
                  <th>difficulty_threshold</th>
                  <th>required_license_codes</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {EVENT_TIERS.map((tier) => {
                  const rule = rules.find((r) => r.tier === tier);
                  const codes = rule?.required_license_codes && Array.isArray(rule.required_license_codes) ? rule.required_license_codes.join(', ') : '—';
                  return (
                    <tr key={tier}>
                      <td>{tier}</td>
                      <td>{rule ? rule.min_events : '—'}</td>
                      <td>{rule ? rule.difficulty_threshold : '—'}</td>
                      <td>{codes}</td>
                      <td>
                        <button type="button" className="btn ghost admin-constructors__btn" onClick={() => ensureRule(tier)}>Edit</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
          {editingTier && (
            <section className="admin-constructors__block">
              <h4 className="admin-constructors__subtitle">Edit tier {editingTier}</h4>
              <form onSubmit={saveRule} className="admin-constructors__form">
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">min_events</label>
                  <input
                    type="number"
                    min="0"
                    value={editForm.min_events}
                    onChange={(e) => setEditForm((f) => ({ ...f, min_events: e.target.value }))}
                    className="admin-constructors__input"
                    placeholder="5"
                  />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">difficulty_threshold</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={editForm.difficulty_threshold}
                    onChange={(e) => setEditForm((f) => ({ ...f, difficulty_threshold: e.target.value }))}
                    className="admin-constructors__input"
                    placeholder="0"
                  />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">required_license_codes (comma-separated)</label>
                  <input
                    type="text"
                    value={editForm.required_license_codes}
                    onChange={(e) => setEditForm((f) => ({ ...f, required_license_codes: e.target.value }))}
                    className="admin-constructors__input"
                    placeholder="GT_E1, GT_ROOKIE"
                  />
                </div>
                <button type="submit" className="btn primary admin-constructors__btn" disabled={saveLoading}>{saveLoading ? '…' : 'Save'}</button>
                <button type="button" className="btn ghost admin-constructors__btn" onClick={() => setEditingTier(null)}>Cancel</button>
                {saveMsg && <span className="admin-constructors__msg" role="status">{saveMsg}</span>}
              </form>
            </section>
          )}
        </>
      )}
    </div>
  );
};

const AdminLookup = () => {
  const [q, setQ] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [partId, setPartId] = useState('');
  const [partData, setPartData] = useState(null);
  const [partLoading, setPartLoading] = useState(false);
  const [partError, setPartError] = useState(null);

  const [incidentId, setIncidentId] = useState('');
  const [incidentData, setIncidentData] = useState(null);
  const [incidentLoading, setIncidentLoading] = useState(false);
  const [incidentError, setIncidentError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setPartData(null);
    setPartError(null);
    setIncidentData(null);
    setIncidentError(null);
    apiFetch(`/api/admin/lookup?q=${encodeURIComponent(query)}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Not found');
        return res.json();
      })
      .then((data) => {
        setResult(data);
      })
      .catch((err) => {
        setError(err?.message || 'Error');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const fetchParticipation = (e) => {
    e.preventDefault();
    const id = partId.trim();
    if (!id) return;
    setPartLoading(true);
    setPartError(null);
    setPartData(null);
    apiFetch(`/api/admin/participations/${encodeURIComponent(id)}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Not found');
        return res.json();
      })
      .then(setPartData)
      .catch((err) => {
        setPartError(err?.message || 'Error');
      })
      .finally(() => {
        setPartLoading(false);
      });
  };

  const fetchIncident = (e) => {
    e.preventDefault();
    const id = incidentId.trim();
    if (!id) return;
    setIncidentLoading(true);
    setIncidentError(null);
    setIncidentData(null);
    apiFetch(`/api/admin/incidents/${encodeURIComponent(id)}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Not found');
        return res.json();
      })
      .then(setIncidentData)
      .catch((err) => {
        setIncidentError(err?.message || 'Error');
      })
      .finally(() => {
        setIncidentLoading(false);
      });
  };

  return (
    <div className="admin-lookup">
      <form className="admin-lookup__form" onSubmit={handleSubmit} data-admin-lookup-form>
        <label className="admin-lookup__label" htmlFor="admin-lookup-q">
          UID / email
        </label>
        <div className="admin-lookup__row">
          <input
            id="admin-lookup-q"
            type="text"
            className="admin-lookup__input"
            placeholder="driver_id or email"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            autoComplete="off"
          />
          <button type="submit" className="btn primary admin-lookup__btn" disabled={loading}>
            {loading ? '…' : 'Search'}
          </button>
        </div>
      </form>
      {error && <p className="admin-lookup__error" role="alert">{error}</p>}

      <AdminConstructors />
      <TierRulesPanel />

      {result && (
        <div className="admin-lookup-result card">
          {result.driver && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Driver</h3>
              <dl className="admin-lookup-result__dl">
                <div><dt>ID</dt><dd>{result.driver.id}</dd></div>
                <div><dt>Name</dt><dd>{result.driver.name}</dd></div>
                <div><dt>Discipline</dt><dd>{result.driver.primary_discipline}</dd></div>
                <div><dt>Games</dt><dd>{result.driver.sim_games?.length ? result.driver.sim_games.join(', ') : '—'}</dd></div>
              </dl>
              <h4 className="admin-lookup-result__subtitle">Last Participations</h4>
              {result.participations?.length > 0 ? (
                <ul className="admin-lookup-result__list admin-lookup-result__participations">
                  {result.participations.map((p) => (
                    <li key={p.id}>
                      <span className="admin-lookup-result__part-id">{p.id}</span>
                      <span className="admin-lookup-result__part-date">{formatDate(p.started_at)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="admin-lookup-result__empty">No participations</p>
              )}
            </section>
          )}

          <section className="admin-lookup-result__block admin-lookup-result__inputs">
            <label className="admin-lookup__label" htmlFor="admin-lookup-part-id">
              Participation by id
            </label>
            <form className="admin-lookup__row" onSubmit={fetchParticipation}>
              <input
                id="admin-lookup-part-id"
                type="text"
                className="admin-lookup__input"
                placeholder="participation id"
                value={partId}
                onChange={(e) => setPartId(e.target.value)}
                autoComplete="off"
              />
              <button type="submit" className="btn primary admin-lookup__btn" disabled={partLoading}>
                {partLoading ? '…' : 'Fetch'}
              </button>
            </form>
            {partError && <p className="admin-lookup__error" role="alert">{partError}</p>}
            {partData && (
              <div className="admin-lookup-result__fetched">
                <h4 className="admin-detail-panel__subtitle">Event</h4>
                <p>{partData.event?.title ?? partData.event?.id} {partData.event?.game ? `(${partData.event.game})` : ''}</p>
                <h4 className="admin-detail-panel__subtitle">Driver</h4>
                <p>{partData.driver?.name} ({partData.driver?.primary_discipline})</p>
                <h4 className="admin-detail-panel__subtitle">Result</h4>
                <dl className="admin-lookup-result__dl">
                  <div><dt>Status</dt><dd>{partData.participation?.status}</dd></div>
                  <div><dt>Position</dt><dd>{partData.participation?.position_overall ?? '—'}</dd></div>
                  <div><dt>Laps</dt><dd>{partData.participation?.laps_completed}</dd></div>
                  <div><dt>Started</dt><dd>{formatDate(partData.participation?.started_at)}</dd></div>
                </dl>
                {partData.incidents?.length > 0 && (
                  <>
                    <h4 className="admin-detail-panel__subtitle">Incidents</h4>
                    <ul className="admin-lookup-result__list admin-lookup-result__participations">
                      {partData.incidents.map((i) => (
                        <li key={i.id}>
                          <span className="admin-lookup-result__part-id">{i.id}</span>
                          {i.created_at != null && (
                            <span className="admin-lookup-result__part-date">{formatDate(i.created_at)}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}

            <label className="admin-lookup__label" htmlFor="admin-lookup-incident-id">
              Incident by id
            </label>
            <form className="admin-lookup__row" onSubmit={fetchIncident}>
              <input
                id="admin-lookup-incident-id"
                type="text"
                className="admin-lookup__input"
                placeholder="incident id"
                value={incidentId}
                onChange={(e) => setIncidentId(e.target.value)}
                autoComplete="off"
              />
              <button type="submit" className="btn primary admin-lookup__btn" disabled={incidentLoading}>
                {incidentLoading ? '…' : 'Fetch'}
              </button>
            </form>
            {incidentError && <p className="admin-lookup__error" role="alert">{incidentError}</p>}
            {incidentData && (
              <div className="admin-lookup-result__fetched">
                <h4 className="admin-detail-panel__subtitle">Incident</h4>
                <dl className="admin-lookup-result__dl">
                  <div><dt>Type</dt><dd>{incidentData.incident?.incident_type}</dd></div>
                  <div><dt>Severity</dt><dd>{incidentData.incident?.severity}</dd></div>
                  <div><dt>Lap</dt><dd>{incidentData.incident?.lap ?? '—'}</dd></div>
                  <div><dt>Description</dt><dd>{incidentData.incident?.description ?? '—'}</dd></div>
                </dl>
                {incidentData.participation && (
                  <>
                    <h4 className="admin-detail-panel__subtitle">Participation</h4>
                    <p>{incidentData.participation.id} — {incidentData.participation.status}</p>
                  </>
                )}
                {incidentData.event && (
                  <>
                    <h4 className="admin-detail-panel__subtitle">Event</h4>
                    <p>{incidentData.event.title} {incidentData.event.game ? `(${incidentData.event.game})` : ''}</p>
                  </>
                )}
                {incidentData.driver && (
                  <>
                    <h4 className="admin-detail-panel__subtitle">Driver</h4>
                    <p>{incidentData.driver.name}</p>
                  </>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

const Operations = () => {
  return (
    <section id="operations" className="section reveal is-hidden" data-admin-only>
      <div className="section-header-row section-header-row--with-metrics">
        <div className="section-header-row__metrics-wrap">
          <MetricsBoard />
        </div>
        <div className="section-header-row__heading-wrap">
          <div className="section-heading">
            <h2>Admin console</h2>
          </div>
        </div>
      </div>
      <div className="admin-console__body">
        <AdminLookup />
      </div>
    </section>
  );
};

export default Operations;
