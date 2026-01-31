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

const AdminConstructors = () => {
  const [eventForm, setEventForm] = useState({ title: '', source: 'admin', game: '', country: '', city: '' });
  const [eventLoading, setEventLoading] = useState(false);
  const [eventMsg, setEventMsg] = useState(null);

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
            <label className="admin-constructors__label">Country / City</label>
            <input type="text" value={eventForm.country} onChange={(e) => setEventForm((f) => ({ ...f, country: e.target.value }))} placeholder="country" className="admin-constructors__input admin-constructors__input--short" />
            <input type="text" value={eventForm.city} onChange={(e) => setEventForm((f) => ({ ...f, city: e.target.value }))} placeholder="city" className="admin-constructors__input admin-constructors__input--short" />
          </div>
          <button type="submit" className="btn primary admin-constructors__btn" disabled={eventLoading}>{eventLoading ? '…' : 'Create Event'}</button>
          {eventMsg && <p className="admin-constructors__msg" role="status">{eventMsg}</p>}
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
