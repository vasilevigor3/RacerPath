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
        if (!res.ok) throw new Error(res.statusText || 'Failed to load metrics');
        return res.json();
      })
      .then((data) => {
        if (!cancelled) setMetrics(data);
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

const AdminLookup = ({ onSelectEntity }) => {
  const [q, setQ] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    setLoading(true);
    setError(null);
    setResult(null);
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

  const handleClick = (type, id) => {
    if (typeof onSelectEntity === 'function') onSelectEntity({ type, id });
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
      {result && (
        <div className="admin-lookup-result card">
          {result.user && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">User</h3>
              <dl className="admin-lookup-result__dl">
                <div><dt>ID</dt><dd>{result.user.id}</dd></div>
                <div><dt>Name</dt><dd>{result.user.name}</dd></div>
                <div><dt>Email</dt><dd>{result.user.email ?? '—'}</dd></div>
                <div><dt>Role</dt><dd>{result.user.role}</dd></div>
              </dl>
            </section>
          )}
          {result.driver && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Driver</h3>
              <dl className="admin-lookup-result__dl">
                <div><dt>ID</dt><dd>{result.driver.id}</dd></div>
                <div><dt>Name</dt><dd>{result.driver.name}</dd></div>
                <div><dt>Discipline</dt><dd>{result.driver.primary_discipline}</dd></div>
                <div><dt>Games</dt><dd>{result.driver.sim_games?.length ? result.driver.sim_games.join(', ') : '—'}</dd></div>
              </dl>
            </section>
          )}
          {result.participations?.length > 0 && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Participations</h3>
              <ul className="admin-lookup-result__list">
                {result.participations.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      className="admin-lookup-result__link"
                      onClick={() => handleClick('participation', p.id)}
                      data-entity-type="participation"
                      data-entity-id={p.id}
                    >
                      {p.event_title || p.event_id} {p.event_game ? `(${p.event_game})` : ''} — {p.status} · {p.incidents_count} incident(s)
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {result.incidents?.length > 0 && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Incidents</h3>
              <ul className="admin-lookup-result__list">
                {result.incidents.map((i) => (
                  <li key={i.id}>
                    <button
                      type="button"
                      className="admin-lookup-result__link"
                      onClick={() => handleClick('incident', i.id)}
                      data-entity-type="incident"
                      data-entity-id={i.id}
                    >
                      {i.incident_type} (severity {i.severity}) · participation {i.participation_id?.slice(0, 8)}…
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {result.licenses?.length > 0 && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Licenses</h3>
              <ul className="admin-lookup-result__list">
                {result.licenses.map((l) => (
                  <li key={l.id}>
                    <button
                      type="button"
                      className="admin-lookup-result__link"
                      onClick={() => handleClick('license', l.id)}
                      data-entity-type="license"
                      data-entity-id={l.id}
                    >
                      {l.discipline} — {l.level_code} ({l.status})
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {result.last_crs && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Last CRS</h3>
              <p>{result.last_crs.discipline}: {result.last_crs.score} ({formatDate(result.last_crs.computed_at)})</p>
            </section>
          )}
          {result.last_recommendation && (
            <section className="admin-lookup-result__block">
              <h3 className="admin-lookup-result__title">Last recommendation</h3>
              <p>{result.last_recommendation.discipline}: {result.last_recommendation.readiness_status} — {result.last_recommendation.summary}</p>
            </section>
          )}
        </div>
      )}
    </div>
  );
};

const ADMIN_DETAIL_ENDPOINTS = {
  event: (id) => `/api/admin/events/${id}`,
  participation: (id) => `/api/admin/participations/${id}`,
  incident: (id) => `/api/admin/incidents/${id}`,
};

const AdminDetailPanel = ({ entity, onBack, onSelectEntity }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!entity?.type || !entity?.id) return;
    const endpoint = ADMIN_DETAIL_ENDPOINTS[entity.type];
    if (!endpoint) {
      setData(null);
      setError(`No detail for type: ${entity.type}`);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);
    apiFetch(endpoint(entity.id))
      .then((res) => {
        if (cancelled) return;
        if (!res.ok) throw new Error(res.statusText || 'Failed to load');
        return res.json();
      })
      .then(setData)
      .catch((err) => { if (!cancelled) setError(err?.message || 'Error'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entity?.type, entity?.id]);

  const handleNav = (type, id) => {
    if (typeof onSelectEntity === 'function') onSelectEntity({ type, id });
  };

  if (entity?.type === 'license') {
    return (
      <div className="admin-console__detail card" role="region" aria-label="Detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
          <h3 className="admin-detail-panel__title">License</h3>
        </div>
        <p className="admin-console__detail-placeholder">License {entity.id} — no detail endpoint yet.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="admin-console__detail card" role="region" aria-label="Detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
        </div>
        <p aria-busy="true">Loading…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="admin-console__detail card" role="region" aria-label="Detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
        </div>
        <p className="admin-detail-panel__error" role="alert">{error}</p>
      </div>
    );
  }
  if (!data) return null;

  if (entity.type === 'event') {
    const { event, classification, participations } = data;
    return (
      <div className="admin-console__detail card" role="region" aria-label="Event detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
          <h3 className="admin-detail-panel__title">{event?.title ?? event?.id}</h3>
        </div>
        <section className="admin-detail-panel__block">
          <h4 className="admin-detail-panel__subtitle">Event</h4>
          <dl className="admin-lookup-result__dl">
            <div><dt>ID</dt><dd>{event?.id}</dd></div>
            <div><dt>Game</dt><dd>{event?.game ?? '—'}</dd></div>
            <div><dt>Start</dt><dd>{formatDate(event?.start_time_utc)}</dd></div>
            <div><dt>Type</dt><dd>{event?.event_type ?? '—'}</dd></div>
          </dl>
        </section>
        {classification && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Classification</h4>
            <dl className="admin-lookup-result__dl">
              <div><dt>Tier</dt><dd>{classification.event_tier} — {classification.tier_label}</dd></div>
              <div><dt>Difficulty</dt><dd>{classification.difficulty_score}</dd></div>
            </dl>
          </section>
        )}
        {participations?.length > 0 && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Participations</h4>
            <ul className="admin-lookup-result__list">
              {participations.map((p) => (
                <li key={p.id}>
                  <button type="button" className="admin-lookup-result__link" onClick={() => handleNav('participation', p.id)}>
                    {p.driver_name ?? p.driver_id} — P{p.position_overall ?? '?'} · {p.laps_completed} laps · {p.incidents_count} incident(s)
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    );
  }

  if (entity.type === 'participation') {
    const { participation, driver, event, incidents } = data;
    return (
      <div className="admin-console__detail card" role="region" aria-label="Participation detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
          <h3 className="admin-detail-panel__title">Participation {participation?.id?.slice(0, 8)}…</h3>
        </div>
        <section className="admin-detail-panel__block">
          <h4 className="admin-detail-panel__subtitle">Event</h4>
          <p>
            <button type="button" className="admin-lookup-result__link" onClick={() => handleNav('event', event?.id)}>
              {event?.title ?? event?.id} {event?.game ? `(${event.game})` : ''}
            </button>
          </p>
        </section>
        <section className="admin-detail-panel__block">
          <h4 className="admin-detail-panel__subtitle">Driver</h4>
          <dl className="admin-lookup-result__dl">
            <div><dt>Name</dt><dd>{driver?.name}</dd></div>
            <div><dt>Discipline</dt><dd>{driver?.primary_discipline}</dd></div>
          </dl>
        </section>
        <section className="admin-detail-panel__block">
          <h4 className="admin-detail-panel__subtitle">Result</h4>
          <dl className="admin-lookup-result__dl">
            <div><dt>Status</dt><dd>{participation?.status}</dd></div>
            <div><dt>Position</dt><dd>{participation?.position_overall ?? '—'}</dd></div>
            <div><dt>Laps</dt><dd>{participation?.laps_completed}</dd></div>
            <div><dt>Started</dt><dd>{formatDate(participation?.started_at)}</dd></div>
          </dl>
        </section>
        {incidents?.length > 0 && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Incidents</h4>
            <ul className="admin-lookup-result__list">
              {incidents.map((i) => (
                <li key={i.id}>
                  <button type="button" className="admin-lookup-result__link" onClick={() => handleNav('incident', i.id)}>
                    {i.incident_type} (severity {i.severity}) {i.lap != null ? `lap ${i.lap}` : ''}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    );
  }

  if (entity.type === 'incident') {
    const { incident, participation, event, driver } = data;
    return (
      <div className="admin-console__detail card" role="region" aria-label="Incident detail">
        <div className="admin-detail-panel__head">
          <button type="button" className="admin-detail-panel__back" onClick={onBack}>← Back</button>
          <h3 className="admin-detail-panel__title">{incident?.incident_type} (severity {incident?.severity})</h3>
        </div>
        <section className="admin-detail-panel__block">
          <h4 className="admin-detail-panel__subtitle">Incident</h4>
          <dl className="admin-lookup-result__dl">
            <div><dt>ID</dt><dd>{incident?.id}</dd></div>
            <div><dt>Type</dt><dd>{incident?.incident_type}</dd></div>
            <div><dt>Lap</dt><dd>{incident?.lap ?? '—'}</dd></div>
            <div><dt>Description</dt><dd>{incident?.description ?? '—'}</dd></div>
            <div><dt>Created</dt><dd>{formatDate(incident?.created_at)}</dd></div>
          </dl>
        </section>
        {participation && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Participation</h4>
            <p>
              <button type="button" className="admin-lookup-result__link" onClick={() => handleNav('participation', participation.id)}>
                {participation.id} — {participation.status} (started {formatDate(participation.started_at)})
              </button>
            </p>
          </section>
        )}
        {event && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Event</h4>
            <p>
              <button type="button" className="admin-lookup-result__link" onClick={() => handleNav('event', event.id)}>
                {event.title} {event.game ? `(${event.game})` : ''}
              </button>
            </p>
          </section>
        )}
        {driver && (
          <section className="admin-detail-panel__block">
            <h4 className="admin-detail-panel__subtitle">Driver</h4>
            <p>{driver.name} ({driver.id})</p>
          </section>
        )}
      </div>
    );
  }

  return null;
};

const Operations = () => {
  const [selectedEntity, setSelectedEntity] = useState(null);

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
        <AdminLookup onSelectEntity={setSelectedEntity} />
        {selectedEntity && (
          <AdminDetailPanel
            entity={selectedEntity}
            onBack={() => setSelectedEntity(null)}
            onSelectEntity={setSelectedEntity}
          />
        )}
      </div>
    </section>
  );
};

export default Operations;
