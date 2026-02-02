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

/** For datetime-local input: ISO string -> "YYYY-MM-DDTHH:mm" or "" */
const toDatetimeLocal = (iso) => {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    return d.toISOString().slice(0, 16);
  } catch {
    return '';
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

const TABS = ['drivers', 'events', 'classifications', 'participations', 'tasks', 'licenses', 'tier', 'schema'];
const TAB_LABELS = { drivers: 'Drivers', events: 'Events', classifications: 'Classifications', participations: 'Participations', tasks: 'Tasks', licenses: 'Licenses', tier: 'Tier rules', schema: 'Project schema' };

const ProjectSchemaPanel = () => {
  return (
    <div className="admin-constructors card admin-schema">
      <h3 className="admin-constructors__title">Project schema</h3>
      <p className="admin-constructors__hint">Arrows: “from → to” = “to depends on from”. Create in order: User → Driver; Event → Classification; then Participation (Driver + Event with Classification); Incident needs Participation.</p>
      <div className="admin-schema__diagram" role="img" aria-label="Entity dependency diagram">
        <div className="admin-schema__row">
          <div className="admin-schema__node" title="Auth / registration">
            <span className="admin-schema__node-label">User</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="Requires User">
            <span className="admin-schema__node-label">Driver</span>
          </div>
        </div>
        <div className="admin-schema__row">
          <div className="admin-schema__node" title="Created first">
            <span className="admin-schema__node-label">Event</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="1 event = 1 classification">
            <span className="admin-schema__node-label">Classification</span>
          </div>
        </div>
        <div className="admin-schema__row admin-schema__row--merge">
          <div className="admin-schema__group">
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">Driver</span>
            </div>
            <span className="admin-schema__plus">+</span>
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">Event</span>
            </div>
            <span className="admin-schema__plus">+</span>
            <div className="admin-schema__node admin-schema__node--small">
              <span className="admin-schema__node-label">Classification</span>
            </div>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="Participation requires Driver and Event (with Classification)">
            <span className="admin-schema__node-label">Participation</span>
          </div>
        </div>
        <div className="admin-schema__row">
          <div className="admin-schema__node">
            <span className="admin-schema__node-label">Participation</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="Requires Participation">
            <span className="admin-schema__node-label">Incident</span>
          </div>
        </div>
        <div className="admin-schema__row">
          <div className="admin-schema__node admin-schema__node--standalone" title="Standalone">
            <span className="admin-schema__node-label">LicenseLevel</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__group">
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">Driver</span>
            </div>
            <span className="admin-schema__plus">+</span>
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">LicenseLevel</span>
            </div>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="DriverLicense = Driver + LicenseLevel">
            <span className="admin-schema__node-label">DriverLicense</span>
          </div>
        </div>
        <div className="admin-schema__row">
          <div className="admin-schema__node admin-schema__node--standalone" title="Standalone">
            <span className="admin-schema__node-label">TaskDefinition</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__group">
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">Driver</span>
            </div>
            <span className="admin-schema__plus">+</span>
            <div className="admin-schema__node">
              <span className="admin-schema__node-label">TaskDefinition</span>
            </div>
            <span className="admin-schema__plus">(±Part.)</span>
          </div>
          <span className="admin-schema__arrow" aria-hidden>→</span>
          <div className="admin-schema__node" title="TaskCompletion: Driver + TaskDefinition, optional Participation">
            <span className="admin-schema__node-label">TaskCompletion</span>
          </div>
        </div>
        <div className="admin-schema__row">
          <div className="admin-schema__node admin-schema__node--standalone" title="Per tier E0–E5">
            <span className="admin-schema__node-label">TierProgressionRule</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminConstructors = ({ tab }) => {
  const [raceOfDayLoading, setRaceOfDayLoading] = useState(false);
  const [raceOfDayMsg, setRaceOfDayMsg] = useState(null);

  const [eventForm, setEventForm] = useState({ title: '', source: 'admin', game: '', country: '', city: '', start_time_utc: '', finished_time_utc: '', event_tier: 'E2', special_event: '', session_type: 'race' });
  const [eventLoading, setEventLoading] = useState(false);
  const [eventMsg, setEventMsg] = useState(null);

  const [updateEventId, setUpdateEventId] = useState('');
  const [updateEventForm, setUpdateEventForm] = useState({
    classification_id: '',
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
      let classificationId = '';
      if (classRes.ok) {
        const cls = await classRes.json();
        eventTier = cls.event_tier || '';
        classificationId = cls.id || '';
      }
      setUpdateEventForm({
        classification_id: classificationId,
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

  const showEvents = tab === undefined || tab === 'events';
  const showParticipations = tab === undefined || tab === 'participations';

  return (
    <div className="admin-constructors card">
      {!tab && <h3 className="admin-constructors__title">Constructors (driver flow)</h3>}

      {showEvents && (
      <>
      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Race of the day</h4>
        <p className="admin-constructors__hint">Delete current Race of the day event(s) with all participations and create a new one (E0, start in ~2h).</p>
        <button
          type="button"
          className="btn secondary admin-constructors__btn"
          disabled={raceOfDayLoading}
          onClick={async () => {
            setRaceOfDayMsg(null);
            setRaceOfDayLoading(true);
            try {
              const res = await apiFetch('/api/admin/race-of-day/restart', { method: 'POST' });
              const data = res.ok ? await res.json().catch(() => ({})) : null;
              if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                setRaceOfDayMsg(err?.detail || 'Restart failed.');
                return;
              }
              setRaceOfDayMsg(
                data
                  ? `Restarted: deleted ${data.deleted_count ?? 0} event(s), created "${data.new_event_title ?? ''}" (id=${(data.new_event_id ?? '').slice(0, 8)}…, start=${data.new_event_start_utc ?? ''}).`
                  : 'Restarted.'
              );
            } catch (e) {
              setRaceOfDayMsg('Restart failed.');
            } finally {
              setRaceOfDayLoading(false);
            }
          }}
        >
          {raceOfDayLoading ? '…' : 'Restart Race of the day'}
        </button>
        {raceOfDayMsg && <p className="admin-constructors__msg" role="status">{raceOfDayMsg}</p>}
      </section>
      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Event</h4>
        <p className="admin-constructors__hint">Classification is created automatically when event is created (1 event = 1 classification).</p>
        <form onSubmit={createEvent} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Title</label>
            <input type="text" value={eventForm.title} onChange={(e) => setEventForm((f) => ({ ...f, title: e.target.value }))} placeholder="Event title" required className="admin-constructors__input admin-constructors__input--title" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Source</label>
            <input type="text" value={eventForm.source} onChange={(e) => setEventForm((f) => ({ ...f, source: e.target.value }))} placeholder="admin" className="admin-constructors__input admin-constructors__input--narrow" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Game</label>
            <select value={eventForm.game} onChange={(e) => setEventForm((f) => ({ ...f, game: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {GAMES.map((g) => (
                <option key={g || '—'} value={g}>{g || '—'}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Tier</label>
            <select value={eventForm.event_tier} onChange={(e) => setEventForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required>
              {EVENT_TIERS.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event type (race/training)</label>
            <select value={eventForm.session_type} onChange={(e) => setEventForm((f) => ({ ...f, session_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {SESSION_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Start time (UTC)</label>
            <input type="datetime-local" value={eventForm.start_time_utc} onChange={(e) => setEventForm((f) => ({ ...f, start_time_utc: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Finished time (UTC)</label>
            <input type="datetime-local" value={eventForm.finished_time_utc} onChange={(e) => setEventForm((f) => ({ ...f, finished_time_utc: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" placeholder="optional — from external API or set later" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Race of</label>
            <select value={eventForm.special_event} onChange={(e) => setEventForm((f) => ({ ...f, special_event: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {SPECIAL_EVENT_OPTIONS.map((o) => (
                <option key={o.value || '—'} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row admin-constructors__row--full">
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
          <input type="text" value={updateEventId} onChange={(e) => setUpdateEventId(e.target.value)} placeholder="event uuid" className="admin-constructors__input admin-constructors__input--uuid" />
          <button type="button" className="btn ghost admin-constructors__btn" onClick={fetchEventForUpdate} disabled={updateEventFetching}>{updateEventFetching ? '…' : 'Fetch'}</button>
        </div>
        {updateEventMsg && <p className="admin-constructors__msg" role="status">{updateEventMsg}</p>}
        <form onSubmit={updateEventSubmit} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Classification ID</label>
            <input type="text" value={updateEventForm.classification_id || ''} readOnly placeholder="—" className="admin-constructors__input admin-constructors__input--uuid" title="1 event = 1 classification (read-only)" />
          </div>
          <div className="admin-constructors__row admin-constructors__row--full">
            <label className="admin-constructors__label">Title</label>
            <input type="text" value={updateEventForm.title} onChange={(e) => setUpdateEventForm((f) => ({ ...f, title: e.target.value }))} placeholder="Event title" className="admin-constructors__input admin-constructors__input--title" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Source</label>
            <input type="text" value={updateEventForm.source} onChange={(e) => setUpdateEventForm((f) => ({ ...f, source: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Game</label>
            <select value={updateEventForm.game} onChange={(e) => setUpdateEventForm((f) => ({ ...f, game: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {GAMES.map((g) => (<option key={g || '—'} value={g}>{g || '—'}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Tier</label>
            <select value={updateEventForm.event_tier} onChange={(e) => setUpdateEventForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              <option value="">—</option>
              {EVENT_TIERS.map((t) => (<option key={t} value={t}>{t}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Race of</label>
            <select value={updateEventForm.special_event} onChange={(e) => setUpdateEventForm((f) => ({ ...f, special_event: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {SPECIAL_EVENT_OPTIONS.map((o) => (
                <option key={o.value || '—'} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Start time (UTC)</label>
            <input type="datetime-local" value={updateEventForm.start_time_utc} onChange={(e) => setUpdateEventForm((f) => ({ ...f, start_time_utc: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Finished time (UTC)</label>
            <input type="datetime-local" value={updateEventForm.finished_time_utc} onChange={(e) => setUpdateEventForm((f) => ({ ...f, finished_time_utc: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" placeholder="optional" />
          </div>
          <div className="admin-constructors__row admin-constructors__row--full">
            <label className="admin-constructors__label">Country / City</label>
            <input type="text" value={updateEventForm.country} onChange={(e) => setUpdateEventForm((f) => ({ ...f, country: e.target.value }))} placeholder="country" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={updateEventForm.city} onChange={(e) => setUpdateEventForm((f) => ({ ...f, city: e.target.value }))} placeholder="city" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event type (race/training) / Schedule / Type / Format</label>
            <select value={updateEventForm.session_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, session_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {SESSION_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <select value={updateEventForm.schedule_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, schedule_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {SCHEDULE_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.event_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, event_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {EVENT_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.format_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, format_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {FORMAT_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Team size / Duration / Grid / Classes</label>
            <input type="number" min="1" max="8" value={updateEventForm.team_size_min} onChange={(e) => setUpdateEventForm((f) => ({ ...f, team_size_min: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" placeholder="team min" />
            <input type="number" min="1" max="8" value={updateEventForm.team_size_max} onChange={(e) => setUpdateEventForm((f) => ({ ...f, team_size_max: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" placeholder="team max" />
            <input type="number" min="0" value={updateEventForm.duration_minutes} onChange={(e) => setUpdateEventForm((f) => ({ ...f, duration_minutes: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" placeholder="duration" />
            <input type="number" min="0" value={updateEventForm.grid_size_expected} onChange={(e) => setUpdateEventForm((f) => ({ ...f, grid_size_expected: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" placeholder="grid" />
            <input type="number" min="1" max="6" value={updateEventForm.class_count} onChange={(e) => setUpdateEventForm((f) => ({ ...f, class_count: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" placeholder="classes" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Damage / Penalties / Fuel / Tire / Weather</label>
            <select value={updateEventForm.damage_model} onChange={(e) => setUpdateEventForm((f) => ({ ...f, damage_model: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {DAMAGE_MODELS.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.penalties} onChange={(e) => setUpdateEventForm((f) => ({ ...f, penalties: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.fuel_usage} onChange={(e) => setUpdateEventForm((f) => ({ ...f, fuel_usage: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.tire_wear} onChange={(e) => setUpdateEventForm((f) => ({ ...f, tire_wear: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
              {RULES_TOGGLES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.weather} onChange={(e) => setUpdateEventForm((f) => ({ ...f, weather: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {WEATHER_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Stewarding / License</label>
            <select value={updateEventForm.stewarding} onChange={(e) => setUpdateEventForm((f) => ({ ...f, stewarding: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {STEWARDING_TYPES.map((s) => (<option key={s} value={s}>{s}</option>))}
            </select>
            <select value={updateEventForm.license_requirement} onChange={(e) => setUpdateEventForm((f) => ({ ...f, license_requirement: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
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
            <input type="text" value={updateEventForm.surface_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, surface_type: e.target.value }))} placeholder="surface_type" className="admin-constructors__input admin-constructors__input--narrow" />
            <input type="text" value={updateEventForm.track_type} onChange={(e) => setUpdateEventForm((f) => ({ ...f, track_type: e.target.value }))} placeholder="track_type" className="admin-constructors__input admin-constructors__input--narrow" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={updateEventLoading}>{updateEventLoading ? '…' : 'Update Event'}</button>
        </form>
      </section>
      </>
      )}

      {showParticipations && (
      <>
      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Participation</h4>
        <p className="admin-constructors__hint">Event must have a classification first (1 event = 1 classification).</p>
        <form onSubmit={createParticipation} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Driver ID</label>
            <input type="text" value={partForm.driver_id} onChange={(e) => setPartForm((f) => ({ ...f, driver_id: e.target.value }))} placeholder="driver uuid" required className="admin-constructors__input admin-constructors__input--uuid" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Event ID</label>
            <input type="text" value={partForm.event_id} onChange={(e) => setPartForm((f) => ({ ...f, event_id: e.target.value }))} placeholder="event uuid" required className="admin-constructors__input admin-constructors__input--uuid" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Discipline</label>
            <select value={partForm.discipline} onChange={(e) => setPartForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Status</label>
            <select value={partForm.status} onChange={(e) => setPartForm((f) => ({ ...f, status: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {PARTICIPATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">State</label>
            <select value={partForm.participation_state} onChange={(e) => setPartForm((f) => ({ ...f, participation_state: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {PARTICIPATION_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Position / Laps</label>
            <input type="number" min="0" value={partForm.position_overall} onChange={(e) => setPartForm((f) => ({ ...f, position_overall: e.target.value }))} placeholder="position" className="admin-constructors__input admin-constructors__input--num" />
            <input type="number" min="0" value={partForm.laps_completed} onChange={(e) => setPartForm((f) => ({ ...f, laps_completed: e.target.value }))} placeholder="laps" className="admin-constructors__input admin-constructors__input--num" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={partLoading}>{partLoading ? '…' : 'Create Participation'}</button>
          {partMsg && (
            <p className={`admin-constructors__msg${partMsg.startsWith('Participation created:') ? '' : ' admin-constructors__msg--error'}`} role="status">{partMsg}</p>
          )}
        </form>
      </section>

      <section className="admin-constructors__block">
        <h4 className="admin-constructors__subtitle">Create Incident</h4>
        <form onSubmit={createIncident} className="admin-constructors__form">
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Participation ID</label>
            <input type="text" value={incidentForm.participation_id} onChange={(e) => setIncidentForm((f) => ({ ...f, participation_id: e.target.value }))} placeholder="participation uuid" required className="admin-constructors__input admin-constructors__input--uuid" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Type / Severity / Lap</label>
            <select value={incidentForm.incident_type} onChange={(e) => setIncidentForm((f) => ({ ...f, incident_type: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              {INCIDENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <input type="number" min="1" max="5" value={incidentForm.severity} onChange={(e) => setIncidentForm((f) => ({ ...f, severity: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
            <input type="number" min="0" value={incidentForm.lap} onChange={(e) => setIncidentForm((f) => ({ ...f, lap: e.target.value }))} placeholder="lap" className="admin-constructors__input admin-constructors__input--num" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Description</label>
            <input type="text" value={incidentForm.description} onChange={(e) => setIncidentForm((f) => ({ ...f, description: e.target.value }))} placeholder="optional" className="admin-constructors__input admin-constructors__input--uuid" />
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
            <input type="text" value={updatePartForm.participation_id} onChange={(e) => setUpdatePartForm((f) => ({ ...f, participation_id: e.target.value }))} placeholder="participation uuid" required className="admin-constructors__input admin-constructors__input--uuid" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Status / State</label>
            <select value={updatePartForm.status} onChange={(e) => setUpdatePartForm((f) => ({ ...f, status: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              <option value="">—</option>
              {PARTICIPATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={updatePartForm.participation_state} onChange={(e) => setUpdatePartForm((f) => ({ ...f, participation_state: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
              <option value="">—</option>
              {PARTICIPATION_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Position / Laps</label>
            <input type="number" min="0" value={updatePartForm.position_overall} onChange={(e) => setUpdatePartForm((f) => ({ ...f, position_overall: e.target.value }))} placeholder="position" className="admin-constructors__input admin-constructors__input--num" />
            <input type="number" min="0" value={updatePartForm.laps_completed} onChange={(e) => setUpdatePartForm((f) => ({ ...f, laps_completed: e.target.value }))} placeholder="laps" className="admin-constructors__input admin-constructors__input--num" />
          </div>
          <div className="admin-constructors__row">
            <label className="admin-constructors__label">Started / Finished (ISO)</label>
            <input type="text" value={updatePartForm.started_at} onChange={(e) => setUpdatePartForm((f) => ({ ...f, started_at: e.target.value }))} placeholder="2025-01-31T12:00:00Z" className="admin-constructors__input admin-constructors__input--uuid" />
            <input type="text" value={updatePartForm.finished_at} onChange={(e) => setUpdatePartForm((f) => ({ ...f, finished_at: e.target.value }))} placeholder="2025-01-31T14:00:00Z" className="admin-constructors__input admin-constructors__input--uuid" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={updatePartLoading}>{updatePartLoading ? '…' : 'Update Participation'}</button>
          {updatePartMsg && <p className="admin-constructors__msg" role="status">{updatePartMsg}</p>}
        </form>
      </section>
      </>
      )}
    </div>
  );
};

const ClassificationsPanel = () => {
  const [classifications, setClassifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterEventId, setFilterEventId] = useState('');
  const [createForm, setCreateForm] = useState({
    event_id: '', event_tier: 'E2', tier_label: 'E2', difficulty_score: '0', seriousness_score: '0', realism_score: '0',
    classification_version: 'v1', inputs_hash: 'manual',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createMsg, setCreateMsg] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({
    event_tier: '', tier_label: '', difficulty_score: '', seriousness_score: '', realism_score: '',
    classification_version: '', inputs_hash: '',
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  const loadClassifications = () => {
    setLoading(true);
    setError(null);
    const q = filterEventId.trim() ? `?event_id=${encodeURIComponent(filterEventId.trim())}` : '';
    apiFetch(`/api/admin/classifications${q}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed');
        return res.json();
      })
      .then(setClassifications)
      .catch((err) => setError(err?.message || 'Error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadClassifications(); }, [filterEventId]);

  const handleCreate = (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateMsg(null);
    const body = {
      event_id: createForm.event_id.trim(),
      event_tier: createForm.event_tier.trim() || 'E2',
      tier_label: createForm.tier_label.trim() || 'E2',
      difficulty_score: parseFloat(createForm.difficulty_score) || 0,
      seriousness_score: parseFloat(createForm.seriousness_score) || 0,
      realism_score: parseFloat(createForm.realism_score) || 0,
      discipline_compatibility: {},
      caps_applied: [],
      classification_version: createForm.classification_version.trim() || 'v1',
      inputs_hash: createForm.inputs_hash.trim() || 'manual',
      inputs_snapshot: {},
    };
    apiFetch('/api/admin/classifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setCreateMsg('Created');
        setCreateForm({ event_id: '', event_tier: 'E2', tier_label: 'E2', difficulty_score: '0', seriousness_score: '0', realism_score: '0', classification_version: 'v1', inputs_hash: 'manual' });
        loadClassifications();
      })
      .catch((err) => setCreateMsg(err?.message || 'Error'))
      .finally(() => setCreateLoading(false));
  };

  const startEdit = (c) => {
    setEditingId(c.id);
    setEditForm({
      event_tier: c.event_tier || '',
      tier_label: c.tier_label || '',
      difficulty_score: String(c.difficulty_score ?? ''),
      seriousness_score: String(c.seriousness_score ?? ''),
      realism_score: String(c.realism_score ?? ''),
      classification_version: c.classification_version || '',
      inputs_hash: c.inputs_hash || '',
    });
    setSaveMsg(null);
  };

  const handleUpdate = (e) => {
    e.preventDefault();
    if (!editingId) return;
    setSaveLoading(true);
    setSaveMsg(null);
    const body = {};
    if (editForm.event_tier !== '') body.event_tier = editForm.event_tier.trim();
    if (editForm.tier_label !== '') body.tier_label = editForm.tier_label.trim();
    if (editForm.difficulty_score !== '') body.difficulty_score = parseFloat(editForm.difficulty_score);
    if (editForm.seriousness_score !== '') body.seriousness_score = parseFloat(editForm.seriousness_score);
    if (editForm.realism_score !== '') body.realism_score = parseFloat(editForm.realism_score);
    if (editForm.classification_version !== '') body.classification_version = editForm.classification_version.trim();
    if (editForm.inputs_hash !== '') body.inputs_hash = editForm.inputs_hash.trim();
    apiFetch(`/api/admin/classifications/${encodeURIComponent(editingId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setSaveMsg('Saved');
        loadClassifications();
        setEditingId(null);
      })
      .catch((err) => setSaveMsg(err?.message || 'Error'))
      .finally(() => setSaveLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">Classifications (constructor)</h3>
      <p className="admin-constructors__hint">1 event = 1 classification. Required for participation and CRS. Create event first, then add classification if not auto-created.</p>
      <div className="admin-constructors__row">
        <label className="admin-constructors__label">Filter by event_id</label>
        <input type="text" value={filterEventId} onChange={(e) => setFilterEventId(e.target.value)} placeholder="event uuid" className="admin-constructors__input admin-constructors__input--uuid" />
      </div>
      {loading && <p className="admin-constructors__msg">Loading…</p>}
      {error && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{error}</p>}
      {!loading && !error && (
        <>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Create classification</h4>
            <form onSubmit={handleCreate} className="admin-constructors__form">
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Event ID</label>
                <input type="text" value={createForm.event_id} onChange={(e) => setCreateForm((f) => ({ ...f, event_id: e.target.value }))} placeholder="event uuid" className="admin-constructors__input admin-constructors__input--uuid" required />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Tier / Tier label</label>
                <select value={createForm.event_tier} onChange={(e) => setCreateForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
                  {EVENT_TIERS.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
                <input type="text" value={createForm.tier_label} onChange={(e) => setCreateForm((f) => ({ ...f, tier_label: e.target.value }))} placeholder="E2" className="admin-constructors__input admin-constructors__input--narrow" />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">difficulty / seriousness / realism</label>
                <input type="number" step="0.1" min="0" max="100" value={createForm.difficulty_score} onChange={(e) => setCreateForm((f) => ({ ...f, difficulty_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
                <input type="number" step="0.1" min="0" max="100" value={createForm.seriousness_score} onChange={(e) => setCreateForm((f) => ({ ...f, seriousness_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
                <input type="number" step="0.1" min="0" max="100" value={createForm.realism_score} onChange={(e) => setCreateForm((f) => ({ ...f, realism_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">classification_version / inputs_hash</label>
                <input type="text" value={createForm.classification_version} onChange={(e) => setCreateForm((f) => ({ ...f, classification_version: e.target.value }))} placeholder="v1" className="admin-constructors__input admin-constructors__input--narrow" />
                <input type="text" value={createForm.inputs_hash} onChange={(e) => setCreateForm((f) => ({ ...f, inputs_hash: e.target.value }))} placeholder="manual" className="admin-constructors__input admin-constructors__input--short" required />
              </div>
              <button type="submit" className="btn primary admin-constructors__btn" disabled={createLoading}>{createLoading ? '…' : 'Create'}</button>
              {createMsg && <span className="admin-constructors__msg" role="status">{createMsg}</span>}
            </form>
          </section>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Classifications</h4>
            <table className="admin-constructors__table" role="grid">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>event_id</th>
                  <th>event_tier</th>
                  <th>difficulty_score</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {classifications.map((c) => (
                  <tr key={c.id}>
                    <td>{c.id}</td>
                    <td>{c.event_id}</td>
                    <td>{c.event_tier}</td>
                    <td>{c.difficulty_score}</td>
                    <td><button type="button" className="btn ghost admin-constructors__btn" onClick={() => startEdit(c)}>Edit</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {editingId && (
            <section className="admin-constructors__block">
              <h4 className="admin-constructors__subtitle">Edit classification</h4>
              <form onSubmit={handleUpdate} className="admin-constructors__form">
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">event_tier / tier_label</label>
                  <select value={editForm.event_tier} onChange={(e) => setEditForm((f) => ({ ...f, event_tier: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
                    {EVENT_TIERS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <input type="text" value={editForm.tier_label} onChange={(e) => setEditForm((f) => ({ ...f, tier_label: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">difficulty / seriousness / realism</label>
                  <input type="number" step="0.1" min="0" max="100" value={editForm.difficulty_score} onChange={(e) => setEditForm((f) => ({ ...f, difficulty_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                  <input type="number" step="0.1" min="0" max="100" value={editForm.seriousness_score} onChange={(e) => setEditForm((f) => ({ ...f, seriousness_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                  <input type="number" step="0.1" min="0" max="100" value={editForm.realism_score} onChange={(e) => setEditForm((f) => ({ ...f, realism_score: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">classification_version / inputs_hash</label>
                  <input type="text" value={editForm.classification_version} onChange={(e) => setEditForm((f) => ({ ...f, classification_version: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                  <input type="text" value={editForm.inputs_hash} onChange={(e) => setEditForm((f) => ({ ...f, inputs_hash: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                </div>
                <button type="submit" className="btn primary admin-constructors__btn" disabled={saveLoading}>{saveLoading ? '…' : 'Save'}</button>
                <button type="button" className="btn ghost admin-constructors__btn" onClick={() => setEditingId(null)}>Cancel</button>
                {saveMsg && <span className="admin-constructors__msg" role="status">{saveMsg}</span>}
              </form>
            </section>
          )}
        </>
      )}
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
                    className="admin-constructors__input admin-constructors__input--num"
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
                    className="admin-constructors__input admin-constructors__input--num"
                    placeholder="0"
                  />
                </div>
                <div className="admin-constructors__row admin-constructors__row--full">
                  <label className="admin-constructors__label">required_license_codes (comma-separated)</label>
                  <input
                    type="text"
                    value={editForm.required_license_codes}
                    onChange={(e) => setEditForm((f) => ({ ...f, required_license_codes: e.target.value }))}
                    className="admin-constructors__input admin-constructors__input--uuid"
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

const LicenseLevelsPanel = ({ onTaskCodeClick }) => {
  const [levels, setLevels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createForm, setCreateForm] = useState({
    discipline: 'gt',
    code: '',
    name: '',
    description: '',
    min_crs: '0',
    required_task_codes: '',
    active: true,
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createMsg, setCreateMsg] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({
    discipline: '',
    code: '',
    name: '',
    description: '',
    min_crs: '',
    required_task_codes: '',
    active: true,
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [filterDiscipline, setFilterDiscipline] = useState('');

  const loadLevels = () => {
    setLoading(true);
    setError(null);
    const q = filterDiscipline ? `?discipline=${encodeURIComponent(filterDiscipline)}` : '';
    apiFetch(`/api/admin/license-levels${q}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed');
        return res.json();
      })
      .then(setLevels)
      .catch((err) => setError(err?.message || 'Error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadLevels(); }, [filterDiscipline]);

  const handleCreate = (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateMsg(null);
    const body = {
      discipline: createForm.discipline,
      code: createForm.code.trim(),
      name: createForm.name.trim(),
      description: createForm.description.trim(),
      min_crs: parseFloat(createForm.min_crs) || 0,
      required_task_codes: createForm.required_task_codes.trim()
        ? createForm.required_task_codes.split(',').map((s) => s.trim()).filter(Boolean)
        : [],
      active: createForm.active,
    };
    apiFetch('/api/admin/license-levels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setCreateMsg('Created');
        setCreateForm({ discipline: 'gt', code: '', name: '', description: '', min_crs: '0', required_task_codes: '', active: true });
        loadLevels();
      })
      .catch((err) => setCreateMsg(err?.message || 'Error'))
      .finally(() => setCreateLoading(false));
  };

  const startEdit = (level) => {
    setEditingId(level.id);
    setEditForm({
      discipline: level.discipline,
      code: level.code,
      name: level.name,
      description: level.description,
      min_crs: String(level.min_crs),
      required_task_codes: Array.isArray(level.required_task_codes) ? level.required_task_codes.join(', ') : '',
      active: level.active,
    });
    setSaveMsg(null);
  };

  const handleUpdate = (e) => {
    e.preventDefault();
    if (!editingId) return;
    setSaveLoading(true);
    setSaveMsg(null);
    const body = {};
    if (editForm.discipline) body.discipline = editForm.discipline;
    if (editForm.code !== '') body.code = editForm.code.trim();
    if (editForm.name !== '') body.name = editForm.name.trim();
    if (editForm.description !== '') body.description = editForm.description.trim();
    if (editForm.min_crs !== '') body.min_crs = parseFloat(editForm.min_crs);
    if (editForm.required_task_codes !== undefined) {
      body.required_task_codes = editForm.required_task_codes.trim()
        ? editForm.required_task_codes.split(',').map((s) => s.trim()).filter(Boolean)
        : [];
    }
    body.active = editForm.active;
    apiFetch(`/api/admin/license-levels/${encodeURIComponent(editingId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setSaveMsg('Saved');
        loadLevels();
        setEditingId(null);
      })
      .catch((err) => setSaveMsg(err?.message || 'Error'))
      .finally(() => setSaveLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">License levels</h3>
      <p className="admin-constructors__hint">Levels define min_crs and required_task_codes for award. Only completions with participation_id count.</p>
      <div className="admin-constructors__row">
        <label className="admin-constructors__label">Filter by discipline</label>
        <select value={filterDiscipline} onChange={(e) => setFilterDiscipline(e.target.value)} className="admin-constructors__input admin-constructors__input--short">
          <option value="">All</option>
          {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>
      {loading && <p className="admin-constructors__msg">Loading…</p>}
      {error && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{error}</p>}
      {!loading && !error && (
        <>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Create level</h4>
            <form onSubmit={handleCreate} className="admin-constructors__form">
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Discipline</label>
                <select value={createForm.discipline} onChange={(e) => setCreateForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
                  {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Code</label>
                <input type="text" value={createForm.code} onChange={(e) => setCreateForm((f) => ({ ...f, code: e.target.value }))} placeholder="e.g. GT_ROOKIE" className="admin-constructors__input admin-constructors__input--narrow" required />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Name</label>
                <input type="text" value={createForm.name} onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))} placeholder="Rookie" className="admin-constructors__input admin-constructors__input--narrow" required />
              </div>
              <div className="admin-constructors__row admin-constructors__row--full">
                <label className="admin-constructors__label">Description</label>
                <input type="text" value={createForm.description} onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))} placeholder="Short description" className="admin-constructors__input admin-constructors__input--uuid" required />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">min_crs</label>
                <input type="number" step="0.1" min="0" max="100" value={createForm.min_crs} onChange={(e) => setCreateForm((f) => ({ ...f, min_crs: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">required_task_codes (comma)</label>
                <input type="text" value={createForm.required_task_codes} onChange={(e) => setCreateForm((f) => ({ ...f, required_task_codes: e.target.value }))} placeholder="finish_race, top10" className="admin-constructors__input admin-constructors__input--uuid" />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Active</label>
                <input type="checkbox" checked={createForm.active} onChange={(e) => setCreateForm((f) => ({ ...f, active: e.target.checked }))} />
              </div>
              <button type="submit" className="btn primary admin-constructors__btn" disabled={createLoading}>{createLoading ? '…' : 'Create'}</button>
              {createMsg && <span className="admin-constructors__msg" role="status">{createMsg}</span>}
            </form>
          </section>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Levels</h4>
            <table className="admin-constructors__table" role="grid">
              <thead>
                <tr>
                  <th>Discipline</th>
                  <th>Code</th>
                  <th>Name</th>
                  <th>min_crs</th>
                  <th>required_task_codes</th>
                  <th>Active</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {levels.map((lev) => (
                  <tr key={lev.id}>
                    <td>{lev.discipline}</td>
                    <td>{lev.code}</td>
                    <td>{lev.name}</td>
                    <td>{lev.min_crs}</td>
                    <td>
                      {lev.required_task_codes && Array.isArray(lev.required_task_codes) && lev.required_task_codes.length > 0
                        ? <span className="admin-task-codes-list">
                            {lev.required_task_codes.map((code) => (
                              onTaskCodeClick
                                ? <button key={code} type="button" className="admin-task-code-link" onClick={() => onTaskCodeClick(code)}>{code}</button>
                                : <span key={code}>{code}</span>
                            ))}
                          </span>
                        : '—'}
                    </td>
                    <td>{lev.active ? 'Yes' : 'No'}</td>
                    <td>
                      <button type="button" className="btn ghost admin-constructors__btn" onClick={() => startEdit(lev)}>Edit</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {editingId && (
            <section className="admin-constructors__block">
              <h4 className="admin-constructors__subtitle">Edit level</h4>
              <form onSubmit={handleUpdate} className="admin-constructors__form">
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Discipline</label>
                  <select value={editForm.discipline} onChange={(e) => setEditForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
                    {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Code</label>
                  <input type="text" value={editForm.code} onChange={(e) => setEditForm((f) => ({ ...f, code: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Name</label>
                  <input type="text" value={editForm.name} onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required />
                </div>
                <div className="admin-constructors__row admin-constructors__row--full">
                  <label className="admin-constructors__label">Description</label>
                  <input type="text" value={editForm.description} onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))} className="admin-constructors__input admin-constructors__input--uuid" required />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">min_crs</label>
                  <input type="number" step="0.1" min="0" max="100" value={editForm.min_crs} onChange={(e) => setEditForm((f) => ({ ...f, min_crs: e.target.value }))} className="admin-constructors__input admin-constructors__input--num" />
                </div>
                <div className="admin-constructors__row admin-constructors__row--full">
                  <label className="admin-constructors__label">Required tasks</label>
                  <span className="admin-task-codes-list">
                    {(() => {
                      const codes = (editForm.required_task_codes || '').split(',').map((s) => s.trim()).filter(Boolean);
                      if (!codes.length) return '—';
                      return codes.map((code) => (
                        onTaskCodeClick
                          ? <button key={code} type="button" className="admin-task-code-link" onClick={() => onTaskCodeClick(code)}>{code}</button>
                          : <span key={code}>{code}</span>
                      ));
                    })()}
                  </span>
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">required_task_codes (comma)</label>
                  <input type="text" value={editForm.required_task_codes} onChange={(e) => setEditForm((f) => ({ ...f, required_task_codes: e.target.value }))} className="admin-constructors__input admin-constructors__input--uuid" placeholder="finish_race, top10" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Active</label>
                  <input type="checkbox" checked={editForm.active} onChange={(e) => setEditForm((f) => ({ ...f, active: e.target.checked }))} />
                </div>
                <button type="submit" className="btn primary admin-constructors__btn" disabled={saveLoading}>{saveLoading ? '…' : 'Save'}</button>
                <button type="button" className="btn ghost admin-constructors__btn" onClick={() => setEditingId(null)}>Cancel</button>
                {saveMsg && <span className="admin-constructors__msg" role="status">{saveMsg}</span>}
              </form>
            </section>
          )}
        </>
      )}
    </div>
  );
};

const LicenseAwardPanel = ({ onTaskCodeClick }) => {
  const [driverId, setDriverId] = useState('');
  const [email, setEmail] = useState('');
  const [discipline, setDiscipline] = useState('gt');
  const [checkResult, setCheckResult] = useState(null);
  const [checkLoading, setCheckLoading] = useState(false);
  const [awardLoading, setAwardLoading] = useState(false);
  const [awardResult, setAwardResult] = useState(null);
  const [awardError, setAwardError] = useState(null);

  const params = () => {
    const p = new URLSearchParams({ discipline });
    if (driverId.trim()) p.set('driver_id', driverId.trim());
    else if (email.trim()) p.set('email', email.trim());
    return p.toString();
  };

  const handleCheck = (e) => {
    e.preventDefault();
    if (!driverId.trim() && !email.trim()) return;
    setCheckLoading(true);
    setCheckResult(null);
    apiFetch(`/api/admin/license-award-check?${params()}`)
      .then((res) => {
        if (!res.ok) return res.json().then((d) => Promise.reject(new Error(d.detail?.message || d.detail || res.statusText)));
        return res.json();
      })
      .then(setCheckResult)
      .catch((err) => setCheckResult({ eligible: false, reasons: [err?.message || 'Error'] }))
      .finally(() => setCheckLoading(false));
  };

  const handleAward = (e) => {
    e.preventDefault();
    if (!driverId.trim() && !email.trim()) return;
    setAwardLoading(true);
    setAwardResult(null);
    setAwardError(null);
    const body = { discipline };
    if (driverId.trim()) body.driver_id = driverId.trim();
    else body.email = email.trim();
    apiFetch('/api/admin/license-award', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.json().then((d) => ({ res, d })))
      .then(({ res, d }) => {
        if (!res.ok) {
          const msg = d.detail?.message || (Array.isArray(d.detail?.reasons) ? d.detail.reasons.join('; ') : '') || res.statusText;
          setAwardError(d.detail?.reasons?.length ? { ...d.detail, message: msg } : msg);
          return;
        }
        setAwardResult(d);
        setAwardError(null);
      })
      .catch((err) => setAwardError(err?.message || 'Error'))
      .finally(() => setAwardLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">License award (by email or driver id)</h3>
      <p className="admin-constructors__hint">Check eligibility or award next license. Only completions with participation_id count toward tasks.</p>
      <form onSubmit={handleCheck} className="admin-constructors__form">
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">Driver ID</label>
          <input type="text" value={driverId} onChange={(e) => setDriverId(e.target.value)} placeholder="driver uuid" className="admin-constructors__input admin-constructors__input--short" />
        </div>
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">or Email</label>
          <input type="text" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" className="admin-constructors__input admin-constructors__input--short" />
        </div>
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">Discipline</label>
          <select value={discipline} onChange={(e) => setDiscipline(e.target.value)} className="admin-constructors__input admin-constructors__input--short">
            {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <button type="submit" className="btn primary admin-constructors__btn" disabled={checkLoading}>{checkLoading ? '…' : 'Check'}</button>
        <button type="button" className="btn ghost admin-constructors__btn" onClick={handleAward} disabled={awardLoading}>{awardLoading ? '…' : 'Award'}</button>
      </form>
      {checkResult && (
        <section className="admin-constructors__block">
          <h4 className="admin-constructors__subtitle">Eligibility</h4>
          <p><strong>Eligible:</strong> {checkResult.eligible ? 'Yes' : 'No'}{checkResult.next_level_code ? ` — next: ${checkResult.next_level_code}` : ''}</p>
          {checkResult.current_crs != null && <p><strong>Current CRS:</strong> {checkResult.current_crs}</p>}
          {checkResult.reasons?.length > 0 && <p><strong>Reasons:</strong> {checkResult.reasons.join('; ')}</p>}
          {checkResult.completed_task_codes?.length >= 0 && <p><strong>Completed tasks:</strong> {checkResult.completed_task_codes?.length ? checkResult.completed_task_codes.join(', ') : '—'}</p>}
          {checkResult.required_task_codes?.length >= 0 && <p><strong>Required for next:</strong> {checkResult.required_task_codes?.length ? checkResult.required_task_codes.join(', ') : '—'}</p>}
        </section>
      )}
      {awardError && typeof awardError === 'object' && (
        <section className="admin-constructors__block">
          <h4 className="admin-constructors__subtitle admin-constructors__subtitle--error">Award error</h4>
          <p>{awardError.message}</p>
          {awardError.reasons?.length > 0 && <ul>{awardError.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>}
          {awardError.required_task_codes?.length > 0 && (
            <p><strong>Required:</strong>{' '}
              <span className="admin-task-codes-list">
                {awardError.required_task_codes.map((code) => (
                  onTaskCodeClick
                    ? <button key={code} type="button" className="admin-task-code-link" onClick={() => onTaskCodeClick(code)}>{code}</button>
                    : <span key={code}>{code}</span>
                ))}
              </span>
            </p>
          )}
        </section>
      )}
      {awardError && typeof awardError === 'string' && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{awardError}</p>}
      {awardResult && (
        <section className="admin-constructors__block">
          <h4 className="admin-constructors__subtitle">Awarded</h4>
          <p>License <strong>{awardResult.level_code}</strong> ({awardResult.discipline}) awarded at {formatDate(awardResult.awarded_at)}.</p>
        </section>
      )}
    </div>
  );
};

const CrsDiagnosticPanel = () => {
  const [driverId, setDriverId] = useState('');
  const [email, setEmail] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [computeLoading, setComputeLoading] = useState(false);
  const [computeMsg, setComputeMsg] = useState(null);

  const handleCheck = (e) => {
    e.preventDefault();
    if (!driverId.trim() && !email.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setComputeMsg(null);
    const params = new URLSearchParams();
    if (driverId.trim()) params.set('driver_id', driverId.trim());
    if (email.trim()) params.set('email', email.trim());
    apiFetch(`/api/admin/driver-crs-diagnostic?${params.toString()}`)
      .then((res) => {
        if (!res.ok) return res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText)));
        return res.json();
      })
      .then(setResult)
      .catch((err) => setError(err?.message || 'Error'))
      .finally(() => setLoading(false));
  };

  const handleComputeCrs = () => {
    if (!result?.driver_id || !result?.primary_discipline) return;
    setComputeLoading(true);
    setComputeMsg(null);
    const params = new URLSearchParams({ driver_id: result.driver_id, discipline: result.primary_discipline });
    apiFetch(`/api/crs/compute?${params.toString()}`, { method: 'POST' })
      .then((res) => {
        if (!res.ok) return res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText)));
        return res.json();
      })
      .then((data) => {
        setComputeMsg(`CRS computed: score ${data.score}`);
        setResult((prev) => prev ? { ...prev, latest_crs_score: data.score, latest_crs_discipline: data.discipline, reason: 'OK' } : prev);
      })
      .catch((err) => setComputeMsg(err?.message || 'Error'))
      .finally(() => setComputeLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">CRS diagnostic</h3>
      <p className="admin-constructors__hint">Check why CRS might be 0: no participations, events missing classification, or CRS never computed. CRS is also auto-recomputed when a participation is created.</p>
      <form onSubmit={handleCheck} className="admin-constructors__form">
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">Driver ID</label>
          <input type="text" value={driverId} onChange={(e) => setDriverId(e.target.value)} placeholder="driver uuid" className="admin-constructors__input admin-constructors__input--short" />
        </div>
        <div className="admin-constructors__row">
          <label className="admin-constructors__label">or Email</label>
          <input type="text" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" className="admin-constructors__input admin-constructors__input--short" />
        </div>
        <button type="submit" className="btn primary admin-constructors__btn" disabled={loading}>{loading ? '…' : 'Check'}</button>
      </form>
      {error && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{error}</p>}
      {result && (
        <section className="admin-constructors__block">
          <h4 className="admin-constructors__subtitle">Result</h4>
          <p><strong>Reason:</strong> {result.reason}</p>
          <dl className="admin-lookup-result__dl">
            <div><dt>driver_id</dt><dd>{result.driver_id}</dd></div>
            <div><dt>primary_discipline</dt><dd>{result.primary_discipline}</dd></div>
            <div><dt>participations_count</dt><dd>{result.participations_count}</dd></div>
            <div><dt>latest_crs_score</dt><dd>{result.latest_crs_score != null ? result.latest_crs_score : '—'}</dd></div>
            <div><dt>latest_crs_discipline</dt><dd>{result.latest_crs_discipline ?? '—'}</dd></div>
          </dl>
          {result.events_missing_classification?.length > 0 && (
            <p><strong>events_missing_classification:</strong> {result.events_missing_classification.join(', ')}</p>
          )}
          <div className="admin-constructors__row">
            <button type="button" className="btn primary admin-constructors__btn" onClick={handleComputeCrs} disabled={computeLoading}>{computeLoading ? '…' : 'Calculate CRS'}</button>
            {computeMsg && <span className="admin-constructors__msg" role="status">{computeMsg}</span>}
          </div>
        </section>
      )}
    </div>
  );
};

const TASK_SCOPES = ['global', 'per_participation', 'rolling_window', 'periodic'];

const TaskDefinitionsPanel = ({ pendingTaskEditId, onClearPendingTaskEdit }) => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterDiscipline, setFilterDiscipline] = useState('');
  const [createForm, setCreateForm] = useState({
    code: '', name: '', discipline: 'gt', description: '', requirements: '{}', min_event_tier: '', active: true,
    scope: 'per_participation', cooldown_days: '', period: '', window_size: '', window_unit: '',
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [createMsg, setCreateMsg] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({
    code: '', name: '', discipline: '', description: '', requirements: '', min_event_tier: '', active: true,
    scope: 'per_participation', cooldown_days: '', period: '', window_size: '', window_unit: '',
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  const loadTasks = () => {
    setLoading(true);
    setError(null);
    const q = filterDiscipline ? `?discipline=${encodeURIComponent(filterDiscipline)}` : '';
    apiFetch(`/api/admin/task-definitions${q}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed');
        return res.json();
      })
      .then(setTasks)
      .catch((err) => setError(err?.message || 'Error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTasks(); }, [filterDiscipline]);

  useEffect(() => {
    if (!pendingTaskEditId || !tasks.length || !onClearPendingTaskEdit) return;
    const task = tasks.find((t) => t.id === pendingTaskEditId);
    if (task) {
      startEdit(task);
    }
    onClearPendingTaskEdit();
  }, [pendingTaskEditId, tasks, onClearPendingTaskEdit]);

  const handleCreate = (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateMsg(null);
    let requirements = {};
    try {
      if (createForm.requirements.trim()) requirements = JSON.parse(createForm.requirements);
    } catch (_) {}
    const body = {
      code: createForm.code.trim(),
      name: createForm.name.trim(),
      discipline: createForm.discipline,
      description: createForm.description.trim(),
      requirements,
      min_event_tier: createForm.min_event_tier.trim() || null,
      active: createForm.active,
      scope: createForm.scope,
      cooldown_days: createForm.cooldown_days.trim() ? parseInt(createForm.cooldown_days, 10) : null,
      period: createForm.period.trim() || null,
      window_size: createForm.window_size.trim() ? parseInt(createForm.window_size, 10) : null,
      window_unit: createForm.window_unit.trim() || null,
    };
    apiFetch('/api/admin/task-definitions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setCreateMsg('Created');
        setCreateForm({ code: '', name: '', discipline: 'gt', description: '', requirements: '{}', min_event_tier: '', active: true, scope: 'per_participation', cooldown_days: '', period: '', window_size: '', window_unit: '' });
        loadTasks();
      })
      .catch((err) => setCreateMsg(err?.message || 'Error'))
      .finally(() => setCreateLoading(false));
  };

  const startEdit = (task) => {
    setEditingId(task.id);
    setEditForm({
      code: task.code,
      name: task.name,
      discipline: task.discipline,
      description: task.description,
      requirements: typeof task.requirements === 'object' ? JSON.stringify(task.requirements, null, 2) : (task.requirements || '{}'),
      min_event_tier: task.min_event_tier || '',
      active: task.active,
      scope: task.scope || 'per_participation',
      cooldown_days: task.cooldown_days != null ? String(task.cooldown_days) : '',
      period: task.period || '',
      window_size: task.window_size != null ? String(task.window_size) : '',
      window_unit: task.window_unit || '',
    });
    setSaveMsg(null);
  };

  const handleUpdate = (e) => {
    e.preventDefault();
    if (!editingId) return;
    setSaveLoading(true);
    setSaveMsg(null);
    let requirements = undefined;
    if (editForm.requirements.trim()) {
      try {
        requirements = JSON.parse(editForm.requirements);
      } catch (_) {}
    }
    const body = {};
    if (editForm.code !== '') body.code = editForm.code.trim();
    if (editForm.name !== '') body.name = editForm.name.trim();
    if (editForm.discipline) body.discipline = editForm.discipline;
    if (editForm.description !== '') body.description = editForm.description.trim();
    if (requirements !== undefined) body.requirements = requirements;
    if (editForm.min_event_tier !== undefined) body.min_event_tier = editForm.min_event_tier.trim() || null;
    body.active = editForm.active;
    if (editForm.scope) body.scope = editForm.scope;
    if (editForm.cooldown_days !== '') body.cooldown_days = editForm.cooldown_days.trim() ? parseInt(editForm.cooldown_days, 10) : null;
    if (editForm.period !== undefined) body.period = editForm.period.trim() || null;
    if (editForm.window_size !== '') body.window_size = editForm.window_size.trim() ? parseInt(editForm.window_size, 10) : null;
    if (editForm.window_unit !== undefined) body.window_unit = editForm.window_unit.trim() || null;
    apiFetch(`/api/admin/task-definitions/${encodeURIComponent(editingId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then((res) => res.ok ? res.json() : res.json().then((d) => Promise.reject(new Error(d.detail || res.statusText))))
      .then(() => {
        setSaveMsg('Saved');
        loadTasks();
        setEditingId(null);
      })
      .catch((err) => setSaveMsg(err?.message || 'Error'))
      .finally(() => setSaveLoading(false));
  };

  return (
    <div className="admin-constructors card">
      <h3 className="admin-constructors__title">Task definitions (constructor)</h3>
      <p className="admin-constructors__hint">
        Tasks are evaluated automatically when a driver joins an event (participation). No direct event–task link: definitions are per discipline; completions are tied to participation. Link to licenses: set <strong>required_task_codes</strong> on License levels (above); this table shows which license levels require each task.
      </p>
      <div className="admin-constructors__row">
        <label className="admin-constructors__label">Filter by discipline</label>
        <select value={filterDiscipline} onChange={(e) => setFilterDiscipline(e.target.value)} className="admin-constructors__input admin-constructors__input--short">
          <option value="">All</option>
          {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>
      {loading && <p className="admin-constructors__msg">Loading…</p>}
      {error && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{error}</p>}
      {!loading && !error && (
        <>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Create task</h4>
            <form onSubmit={handleCreate} className="admin-constructors__form">
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Code</label>
                <input type="text" value={createForm.code} onChange={(e) => setCreateForm((f) => ({ ...f, code: e.target.value }))} placeholder="finish_race" className="admin-constructors__input admin-constructors__input--narrow" required />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Name / Discipline / Description</label>
                <input type="text" value={createForm.name} onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))} placeholder="name" className="admin-constructors__input admin-constructors__input--short" required />
                <select value={createForm.discipline} onChange={(e) => setCreateForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
                  {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
                <input type="text" value={createForm.description} onChange={(e) => setCreateForm((f) => ({ ...f, description: e.target.value }))} placeholder="description" className="admin-constructors__input admin-constructors__input--narrow" required />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">requirements (JSON)</label>
                <input type="text" value={createForm.requirements} onChange={(e) => setCreateForm((f) => ({ ...f, requirements: e.target.value }))} placeholder="{}" className="admin-constructors__input admin-constructors__input--uuid" />
              </div>
              <div className="admin-constructors__row">
                <label className="admin-constructors__label">Scope / min_event_tier / active</label>
                <select value={createForm.scope} onChange={(e) => setCreateForm((f) => ({ ...f, scope: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
                  {TASK_SCOPES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <input type="text" value={createForm.min_event_tier} onChange={(e) => setCreateForm((f) => ({ ...f, min_event_tier: e.target.value }))} placeholder="E0" className="admin-constructors__input admin-constructors__input--short" />
                <label><input type="checkbox" checked={createForm.active} onChange={(e) => setCreateForm((f) => ({ ...f, active: e.target.checked }))} /> Active</label>
              </div>
              <button type="submit" className="btn primary admin-constructors__btn" disabled={createLoading}>{createLoading ? '…' : 'Create'}</button>
              {createMsg && <span className="admin-constructors__msg" role="status">{createMsg}</span>}
            </form>
          </section>
          <section className="admin-constructors__block">
            <h4 className="admin-constructors__subtitle">Tasks (required by license levels)</h4>
            <table className="admin-constructors__table" role="grid">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Discipline</th>
                  <th>Scope</th>
                  <th>Required by licenses</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id}>
                    <td>{t.code}</td>
                    <td>{t.name}</td>
                    <td>{t.discipline}</td>
                    <td>{t.scope}</td>
                    <td>{t.required_by_license_levels?.length ? t.required_by_license_levels.map((l) => `${l.discipline}:${l.level_code}`).join(', ') : '—'}</td>
                    <td>
                      <button type="button" className="btn ghost admin-constructors__btn" onClick={() => startEdit(t)}>Edit</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          {editingId && (
            <section className="admin-constructors__block">
              <h4 className="admin-constructors__subtitle">Edit task</h4>
              <form onSubmit={handleUpdate} className="admin-constructors__form">
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Code / Name / Discipline</label>
                  <input type="text" value={editForm.code} onChange={(e) => setEditForm((f) => ({ ...f, code: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required />
                  <input type="text" value={editForm.name} onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required />
                  <select value={editForm.discipline} onChange={(e) => setEditForm((f) => ({ ...f, discipline: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
                    {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Description</label>
                  <input type="text" value={editForm.description} onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow" required />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">requirements (JSON)</label>
                  <input type="text" value={editForm.requirements} onChange={(e) => setEditForm((f) => ({ ...f, requirements: e.target.value }))} className="admin-constructors__input admin-constructors__input--uuid" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Scope / min_event_tier / active</label>
                  <select value={editForm.scope} onChange={(e) => setEditForm((f) => ({ ...f, scope: e.target.value }))} className="admin-constructors__input admin-constructors__input--short">
                    {TASK_SCOPES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <input type="text" value={editForm.min_event_tier} onChange={(e) => setEditForm((f) => ({ ...f, min_event_tier: e.target.value }))} className="admin-constructors__input admin-constructors__input--short" />
                  <label><input type="checkbox" checked={editForm.active} onChange={(e) => setEditForm((f) => ({ ...f, active: e.target.checked }))} /> Active</label>
                </div>
                <button type="submit" className="btn primary admin-constructors__btn" disabled={saveLoading}>{saveLoading ? '…' : 'Save'}</button>
                <button type="button" className="btn ghost admin-constructors__btn" onClick={() => setEditingId(null)}>Cancel</button>
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
  const [activeTab, setActiveTab] = useState('drivers');
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

  const [partEditForm, setPartEditForm] = useState({
    participation_state: 'registered',
    status: 'finished',
    position_overall: '',
    position_class: '',
    laps_completed: 0,
    started_at: '',
    finished_at: '',
  });
  const [partSaveLoading, setPartSaveLoading] = useState(false);

  const [selectedTaskForCard, setSelectedTaskForCard] = useState(null);
  const [pendingTaskEditId, setPendingTaskEditId] = useState(null);
  const [taskCardLoading, setTaskCardLoading] = useState(false);

  const openTaskCardByCode = (code) => {
    if (!code || !code.trim()) return;
    setTaskCardLoading(true);
    setSelectedTaskForCard(null);
    apiFetch('/api/admin/task-definitions')
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Failed');
        return res.json();
      })
      .then((tasks) => {
        const task = tasks.find((t) => (t.code || '').toLowerCase() === (code || '').trim().toLowerCase());
        if (task) {
          setSelectedTaskForCard(task);
          setActiveTab('licenses');
        } else {
          window.alert(`Task with code "${code}" not found.`);
        }
      })
      .catch((err) => window.alert(err?.message || 'Failed to load tasks'))
      .finally(() => setTaskCardLoading(false));
  };

  useEffect(() => {
    if (!partData?.participation) return;
    const p = partData.participation;
    setPartEditForm({
      participation_state: p.participation_state ?? 'registered',
      status: p.status ?? 'finished',
      position_overall: p.position_overall != null ? String(p.position_overall) : '',
      position_class: p.position_class != null ? String(p.position_class) : '',
      laps_completed: p.laps_completed ?? 0,
      started_at: toDatetimeLocal(p.started_at),
      finished_at: toDatetimeLocal(p.finished_at),
    });
  }, [partData?.participation?.id]);

  const doLookup = (query) => {
    if (!query || !query.trim()) return Promise.resolve();
    setLoading(true);
    setError(null);
    setResult(null);
    setPartData(null);
    setPartError(null);
    setIncidentData(null);
    setIncidentError(null);
    return apiFetch(`/api/admin/lookup?q=${encodeURIComponent(query.trim())}`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Not found');
        return res.json();
      })
      .then((data) => {
        setResult(data);
        return data;
      })
      .catch((err) => {
        setError(err?.message || 'Error');
        throw err;
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    doLookup(query);
  };

  const updateParticipationState = async (partId, payload) => {
    const res = await apiFetch(`/api/admin/participations/${encodeURIComponent(partId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.detail || res.statusText || 'Update failed');
    }
    const query = q.trim();
    if (query) await doLookup(query);
  };

  const mockJoinParticipation = async (partId) => {
    const res = await apiFetch(`/api/dev/participations/${encodeURIComponent(partId)}/mock-join`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.detail || res.statusText || 'Mock join failed');
    }
    const query = q.trim();
    if (query) await doLookup(query);
  };

  const mockFinishParticipation = async (partId, status = 'finished') => {
    const res = await apiFetch(`/api/dev/participations/${encodeURIComponent(partId)}/mock-finish?status=${encodeURIComponent(status)}`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err?.detail || res.statusText || 'Mock finish failed');
    }
    const query = q.trim();
    if (query) await doLookup(query);
  };

  const fetchParticipation = (e) => {
    e.preventDefault();
    const id = partId.trim();
    if (!id) return;
    fetchParticipationById(id);
  };

  const fetchParticipationById = (id) => {
    if (!id) return;
    setPartId(id);
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

  const closeParticipationCard = () => {
    setPartData(null);
    setPartError(null);
    setPartId('');
  };

  const saveParticipationEdit = (e) => {
    e.preventDefault();
    if (!partData?.participation?.id) return;
    setPartSaveLoading(true);
    const posOverall = partEditForm.position_overall === '' ? null : parseInt(partEditForm.position_overall, 10);
    const posClass = partEditForm.position_class === '' ? null : parseInt(partEditForm.position_class, 10);
    const payload = {
      participation_state: partEditForm.participation_state || null,
      status: partEditForm.status || null,
      position_overall: posOverall != null && !Number.isNaN(posOverall) ? posOverall : null,
      position_class: posClass != null && !Number.isNaN(posClass) ? posClass : null,
      laps_completed: partEditForm.laps_completed,
      started_at: partEditForm.started_at ? new Date(partEditForm.started_at).toISOString() : null,
      finished_at: partEditForm.finished_at ? new Date(partEditForm.finished_at).toISOString() : null,
    };
    apiFetch(`/api/admin/participations/${encodeURIComponent(partData.participation.id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText || 'Update failed');
        return res.json();
      })
      .then(() => fetchParticipationById(partData.participation.id))
      .catch((err) => window.alert(err?.message || 'Update failed'))
      .finally(() => setPartSaveLoading(false));
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
      <div className="admin-tabs" role="tablist" aria-label="Admin sections">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={activeTab === t}
            aria-controls={`admin-tabpanel-${t}`}
            id={`admin-tab-${t}`}
            className={`admin-tabs__tab${activeTab === t ? ' admin-tabs__tab--active' : ''}`}
            onClick={() => setActiveTab(t)}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div className="admin-tabpanels">
        {activeTab === 'drivers' && (
          <div id="admin-tabpanel-drivers" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-drivers">
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
            {result && (
        <div className="admin-constructors card">
          <h3 className="admin-constructors__title">Driver (by id/email)</h3>

          {partData && (
            <section className="admin-constructors__block admin-participation-card">
              <div className="admin-participation-card__head">
                <button type="button" className="btn ghost btn-back-arrow" aria-label="Back" onClick={closeParticipationCard}>←</button>
                <h4 className="admin-constructors__subtitle">Participation</h4>
              </div>
              <h4 className="admin-constructors__subtitle">Event</h4>
              <p><strong>{partData.event?.title ?? partData.event?.id}</strong> {partData.event?.game ? `(${partData.event.game})` : ''}</p>
              <h4 className="admin-constructors__subtitle">Driver</h4>
              <p>{partData.driver?.name} ({partData.driver?.primary_discipline ?? '—'})</p>
              <h4 className="admin-constructors__subtitle">Participation</h4>
              <dl className="admin-lookup-result__dl">
                <div><dt>ID</dt><dd className="admin-lookup-result__part-id">{partData.participation?.id}</dd></div>
                <div><dt>State</dt><dd>{partData.participation?.participation_state ?? '—'}</dd></div>
                <div><dt>Status</dt><dd>{partData.participation?.status ?? '—'}</dd></div>
                <div><dt>Position</dt><dd>{partData.participation?.position_overall ?? '—'}</dd></div>
                <div><dt>Laps</dt><dd>{partData.participation?.laps_completed ?? '—'}</dd></div>
                <div><dt>Started</dt><dd>{formatDate(partData.participation?.started_at)}</dd></div>
                <div><dt>Finished</dt><dd>{formatDate(partData.participation?.finished_at)}</dd></div>
              </dl>
              {partData.incidents?.length > 0 && (
                <>
                  <h4 className="admin-constructors__subtitle">Incidents</h4>
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
              <form onSubmit={saveParticipationEdit} className="admin-constructors__form">
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">State</label>
                  <select value={partEditForm.participation_state} onChange={(e) => setPartEditForm((f) => ({ ...f, participation_state: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
                    {PARTICIPATION_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Status</label>
                  <select value={partEditForm.status} onChange={(e) => setPartEditForm((f) => ({ ...f, status: e.target.value }))} className="admin-constructors__input admin-constructors__input--narrow">
                    {PARTICIPATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Position / Class / Laps</label>
                  <input type="number" min="0" value={partEditForm.position_overall} onChange={(e) => setPartEditForm((f) => ({ ...f, position_overall: e.target.value }))} placeholder="overall" className="admin-constructors__input admin-constructors__input--num" />
                  <input type="number" min="0" value={partEditForm.position_class} onChange={(e) => setPartEditForm((f) => ({ ...f, position_class: e.target.value }))} placeholder="class" className="admin-constructors__input admin-constructors__input--num" />
                  <input type="number" min="0" value={partEditForm.laps_completed} onChange={(e) => setPartEditForm((f) => ({ ...f, laps_completed: parseInt(e.target.value, 10) || 0 }))} className="admin-constructors__input admin-constructors__input--num" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Started (UTC)</label>
                  <input type="datetime-local" value={partEditForm.started_at} onChange={(e) => setPartEditForm((f) => ({ ...f, started_at: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" />
                </div>
                <div className="admin-constructors__row">
                  <label className="admin-constructors__label">Finished (UTC)</label>
                  <input type="datetime-local" value={partEditForm.finished_at} onChange={(e) => setPartEditForm((f) => ({ ...f, finished_at: e.target.value }))} className="admin-constructors__input admin-constructors__input--datetime" />
                </div>
                <button type="submit" className="btn primary admin-constructors__btn" disabled={partSaveLoading}>{partSaveLoading ? '…' : 'Save'}</button>
              </form>
              <div className="admin-participation-card__actions">
                {partData.participation?.participation_state === 'registered' && (
                  <>
                    <button type="button" className="btn primary admin-constructors__btn" onClick={() => updateParticipationState(partData.participation.id, { participation_state: 'started', started_at: new Date().toISOString() }).then(() => fetchParticipationById(partData.participation.id)).catch((err) => window.alert(err?.message || 'Failed'))}>
                      Mark as started
                    </button>
                    <button type="button" className="btn ghost admin-constructors__btn" title="Mock: simulate driver joined session" onClick={() => mockJoinParticipation(partData.participation.id).then(() => fetchParticipationById(partData.participation.id)).catch((err) => window.alert(err?.message || 'Failed'))}>
                      Mock join
                    </button>
                  </>
                )}
                {partData.participation?.participation_state === 'started' && (
                  <>
                    <button type="button" className="btn primary admin-constructors__btn" onClick={() => updateParticipationState(partData.participation.id, { participation_state: 'completed', finished_at: new Date().toISOString(), status: 'finished' }).then(() => fetchParticipationById(partData.participation.id)).catch((err) => window.alert(err?.message || 'Failed'))}>
                      Mark as completed
                    </button>
                    <button type="button" className="btn ghost admin-constructors__btn" title="Mock: simulate driver finished race" onClick={() => mockFinishParticipation(partData.participation.id, 'finished').then(() => fetchParticipationById(partData.participation.id)).catch((err) => window.alert(err?.message || 'Failed'))}>
                      Mock finish
                    </button>
                  </>
                )}
              </div>
            </section>
          )}

          {result.driver && (
            <section className="admin-constructors__block">
              <h4 className="admin-constructors__subtitle">Driver</h4>
              <dl className="admin-lookup-result__dl">
                <div><dt>ID</dt><dd>{result.driver.id}</dd></div>
                <div><dt>Name</dt><dd>{result.driver.name}</dd></div>
                <div><dt>Discipline</dt><dd>{result.driver.primary_discipline}</dd></div>
                <div><dt>Games</dt><dd>{result.driver.sim_games?.length ? result.driver.sim_games.join(', ') : '—'}</dd></div>
              </dl>
              <h4 className="admin-constructors__subtitle">Last Participations</h4>
              {result.participations?.length > 0 ? (
                <ul className="admin-lookup-result__list admin-lookup-result__participations">
                  {result.participations.map((p) => (
                    <li
                      key={p.id}
                      className="admin-lookup-result__part-row admin-lookup-result__part-row--clickable"
                      role="button"
                      tabIndex={0}
                      onClick={() => fetchParticipationById(p.id)}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fetchParticipationById(p.id); } }}
                      aria-label={`Open participation ${p.id}`}
                    >
                      <span className="admin-lookup-result__part-id">{p.id}</span>
                      <span className="admin-lookup-result__part-meta">{p.event_title ?? p.event_id?.slice(0, 8)} · {p.participation_state ?? '—'}</span>
                      <span className="admin-lookup-result__part-date">{formatDate(p.started_at) || '—'}</span>
                      {p.participation_state === 'registered' && (
                        <>
                          <button
                            type="button"
                            className="btn ghost admin-constructors__btn"
                            onClick={(e) => { e.stopPropagation(); updateParticipationState(p.id, { participation_state: 'started', started_at: new Date().toISOString() }).catch((err) => window.alert(err?.message || 'Failed')); }}
                          >
                            Mark as started
                          </button>
                          <button
                            type="button"
                            className="btn ghost admin-constructors__btn"
                            title="Mock: simulate driver joined session (external integration)"
                            onClick={(e) => { e.stopPropagation(); mockJoinParticipation(p.id).catch((err) => window.alert(err?.message || 'Failed')); }}
                          >
                            Mock join
                          </button>
                        </>
                      )}
                      {p.participation_state === 'started' && (
                        <>
                          <button
                            type="button"
                            className="btn ghost admin-constructors__btn"
                            onClick={(e) => { e.stopPropagation(); updateParticipationState(p.id, { participation_state: 'completed', finished_at: new Date().toISOString(), status: 'finished' }).catch((err) => window.alert(err?.message || 'Failed')); }}
                          >
                            Mark as completed
                          </button>
                          <button
                            type="button"
                            className="btn ghost admin-constructors__btn"
                            title="Mock: simulate driver finished race (external integration)"
                            onClick={(e) => { e.stopPropagation(); mockFinishParticipation(p.id, 'finished').catch((err) => window.alert(err?.message || 'Failed')); }}
                          >
                            Mock finish
                          </button>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="admin-constructors__msg">No participations</p>
              )}
            </section>
          )}

          <section className="admin-constructors__block">
            <label className="admin-constructors__label" htmlFor="admin-lookup-part-id">
              Participation by id
            </label>
            <form className="admin-constructors__row" onSubmit={fetchParticipation}>
              <input
                id="admin-lookup-part-id"
                type="text"
                className="admin-constructors__input admin-constructors__input--uuid"
                placeholder="participation id"
                value={partId}
                onChange={(e) => setPartId(e.target.value)}
                autoComplete="off"
              />
              <button type="submit" className="btn primary admin-constructors__btn" disabled={partLoading}>
                {partLoading ? '…' : 'Fetch'}
              </button>
            </form>
            {partError && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{partError}</p>}
            {partData && (
              <p className="admin-constructors__msg">Participation opened in card above. Use Back (←) to close.</p>
            )}

            <label className="admin-constructors__label" htmlFor="admin-lookup-incident-id">
              Incident by id
            </label>
            <form className="admin-constructors__row" onSubmit={fetchIncident}>
              <input
                id="admin-lookup-incident-id"
                type="text"
                className="admin-constructors__input admin-constructors__input--uuid"
                placeholder="incident id"
                value={incidentId}
                onChange={(e) => setIncidentId(e.target.value)}
                autoComplete="off"
              />
              <button type="submit" className="btn primary admin-constructors__btn" disabled={incidentLoading}>
                {incidentLoading ? '…' : 'Fetch'}
              </button>
            </form>
            {incidentError && <p className="admin-constructors__msg admin-constructors__msg--error" role="alert">{incidentError}</p>}
            {incidentData && (
              <div className="admin-lookup-result__fetched">
                <h4 className="admin-constructors__subtitle">Incident</h4>
                <dl className="admin-lookup-result__dl">
                  <div><dt>Type</dt><dd>{incidentData.incident?.incident_type}</dd></div>
                  <div><dt>Severity</dt><dd>{incidentData.incident?.severity}</dd></div>
                  <div><dt>Lap</dt><dd>{incidentData.incident?.lap ?? '—'}</dd></div>
                  <div><dt>Description</dt><dd>{incidentData.incident?.description ?? '—'}</dd></div>
                </dl>
                {incidentData.participation && (
                  <>
                    <h4 className="admin-constructors__subtitle">Participation</h4>
                    <p>{incidentData.participation.id} — {incidentData.participation.status}</p>
                  </>
                )}
                {incidentData.event && (
                  <>
                    <h4 className="admin-constructors__subtitle">Event</h4>
                    <p>{incidentData.event.title} {incidentData.event.game ? `(${incidentData.event.game})` : ''}</p>
                  </>
                )}
                {incidentData.driver && (
                  <>
                    <h4 className="admin-constructors__subtitle">Driver</h4>
                    <p>{incidentData.driver.name}</p>
                  </>
                )}
              </div>
            )}
          </section>
        </div>
      )}
            <LicenseAwardPanel onTaskCodeClick={openTaskCardByCode} />
            <CrsDiagnosticPanel />
          </div>
        )}

        {activeTab === 'events' && (
          <div id="admin-tabpanel-events" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-events">
            <AdminConstructors tab="events" />
          </div>
        )}

        {activeTab === 'classifications' && (
          <div id="admin-tabpanel-classifications" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-classifications">
            <ClassificationsPanel />
          </div>
        )}

        {activeTab === 'participations' && (
          <div id="admin-tabpanel-participations" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-participations">
            <AdminConstructors tab="participations" />
          </div>
        )}

        {activeTab === 'tasks' && (
          <div id="admin-tabpanel-tasks" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-tasks">
            <TaskDefinitionsPanel pendingTaskEditId={pendingTaskEditId} onClearPendingTaskEdit={() => setPendingTaskEditId(null)} />
          </div>
        )}

        {activeTab === 'licenses' && (
          <div id="admin-tabpanel-licenses" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-licenses">
            {taskCardLoading && <p className="admin-constructors__msg">Loading task…</p>}
            {selectedTaskForCard && (
              <section className="admin-constructors__block admin-task-card">
                <div className="admin-participation-card__head">
                  <button type="button" className="btn ghost btn-back-arrow" aria-label="Back" onClick={() => setSelectedTaskForCard(null)}>←</button>
                  <h4 className="admin-constructors__subtitle">Task</h4>
                </div>
                <dl className="admin-lookup-result__dl">
                  <div><dt>Code</dt><dd>{selectedTaskForCard.code ?? '—'}</dd></div>
                  <div><dt>Name</dt><dd>{selectedTaskForCard.name ?? '—'}</dd></div>
                  <div><dt>Discipline</dt><dd>{selectedTaskForCard.discipline ?? '—'}</dd></div>
                  <div><dt>Description</dt><dd>{selectedTaskForCard.description ?? '—'}</dd></div>
                  <div><dt>Scope</dt><dd>{selectedTaskForCard.scope ?? '—'}</dd></div>
                  {selectedTaskForCard.min_event_tier && <div><dt>Min event tier</dt><dd>{selectedTaskForCard.min_event_tier}</dd></div>}
                  <div><dt>Active</dt><dd>{selectedTaskForCard.active ? 'Yes' : 'No'}</dd></div>
                  {selectedTaskForCard.required_by_license_levels?.length > 0 && (
                    <div><dt>Required by licenses</dt><dd>{selectedTaskForCard.required_by_license_levels.map((l) => `${l.discipline}:${l.level_code}`).join(', ')}</dd></div>
                  )}
                </dl>
                <div className="admin-participation-card__actions">
                  <button type="button" className="btn primary admin-constructors__btn" onClick={() => { setActiveTab('tasks'); setPendingTaskEditId(selectedTaskForCard.id); setSelectedTaskForCard(null); }}>Edit in Tasks tab</button>
                </div>
              </section>
            )}
            <LicenseLevelsPanel onTaskCodeClick={openTaskCardByCode} />
            <LicenseAwardPanel onTaskCodeClick={openTaskCardByCode} />
          </div>
        )}

        {activeTab === 'tier' && (
          <div id="admin-tabpanel-tier" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-tier">
            <TierRulesPanel />
          </div>
        )}

        {activeTab === 'schema' && (
          <div id="admin-tabpanel-schema" className="admin-tabpanel" role="tabpanel" aria-labelledby="admin-tab-schema">
            <ProjectSchemaPanel />
          </div>
        )}
      </div>
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
