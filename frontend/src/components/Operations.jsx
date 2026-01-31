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
