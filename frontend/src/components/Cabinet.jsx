import DisciplineSelect from './DisciplineSelect.jsx';
import OptionGrid from './OptionGrid.jsx';
import { SIM_GAMES, WHEEL_TYPES, PEDALS_CLASSES } from '../constants/uiData.js';

const Cabinet = () => (
  <section id="cabinet" className="section dashboard reveal" data-driver-only>
    <div className="dashboard-head">
      <div className="dashboard-title">
        <p className="eyebrow">Personal cockpit</p>
        <h1>
          Welcome back, <span data-dashboard-name>Driver</span>
        </h1>
        <p className="lead">Your private dashboard: progress, risks, and the next events you must complete.</p>
      </div>
    </div>

    <div className="dashboard-grid">
      <aside className="profile-pane">
        <div className="card profile-card">
          <p className="card-title">Driver identity</p>
          <div className="avatar" data-profile-initials>
            RP
          </div>
          <h3 data-profile-fullname>--</h3>
          <p className="muted" data-profile-location>
            Location not set
          </p>
          <p className="muted" data-profile-user-id>
            Driver ID: --
          </p>
          <div className="progress">
            <div className="progress-label">Next tier</div>
            <div className="progress-track">
              <div className="progress-fill" data-profile-next-tier style={{ width: '0%' }}></div>
            </div>
            <div className="progress-meta" data-profile-next-tier-meta>
              Complete profile and races to advance.
            </div>
          </div>
          <div className="progress">
            <div className="progress-label">Readiness index <span className="readiness-score" data-readiness-score>--</span></div>
            <div className="progress-track">
              <div className="progress-fill" data-readiness-fill style={{ width: '0%' }}></div>
            </div>
            <div className="progress-meta" data-readiness-note>
              Complete tasks to increase readiness.
            </div>
          </div>
          <div className="pill-row">
            <span className="pill" data-profile-discipline>
              Discipline: --
            </span>
            <span className="pill" data-profile-tier>
              Tier: --
            </span>
            <span className="pill" data-driver-snapshot-pill-crs>
              CRS --
            </span>
            <span className="pill" data-profile-platforms>
              Platforms: --
            </span>
          </div>
          <button className="btn ghost" type="button" data-tab-jump="profile" data-profile-cta-button>
            Complete profile
          </button>
        </div>
      </aside>

      <div className="dashboard-main">
        <div className="stats-grid">
          <button
            className="stat-card is-link"
            type="button"
            data-stat-target="crs"
            data-scroll-target="#dashboards"
            data-focus-target="crs-card"
          >
            <span className="stat-label">CRS</span>
            <span className="stat-value" data-stat-crs>
              --
            </span>
            <span className="stat-meta">Latest score</span>
          </button>
          <button className="stat-card is-link" type="button" data-stat-target="events" data-tab-target="events">
            <span className="stat-label">Events raced</span>
            <span className="stat-value" data-stat-events>
              0
            </span>
            <span className="stat-meta">Last 30 days</span>
          </button>
          <button className="stat-card is-link" type="button" data-stat-target="tasks" data-tab-target="tasks">
            <span className="stat-label">Tasks done</span>
            <span className="stat-value" data-stat-tasks>
              0
            </span>
            <span className="stat-meta">Completed</span>
          </button>
          <button
            className="stat-card is-link"
            type="button"
            data-stat-target="licenses"
            data-tab-target="licenses"
            data-focus-target="licenses-card"
          >
            <span className="stat-label">Licenses</span>
            <span className="stat-value" data-stat-licenses>
              0
            </span>
            <span className="stat-meta">Earned</span>
          </button>
          <button
            className="stat-card is-link"
            type="button"
            data-stat-target="risk-flags"
            data-tab-target="risk-flags"
            data-focus-target="risk-flags-card"
          >
            <span className="stat-label">Risk flags</span>
            <span className="stat-value" data-stat-risk-flags>
              0
            </span>
            <span className="stat-meta">Review</span>
          </button>
        </div>

        <div className="tabs">
          <button className="tab-button active" type="button" data-tab-button="overview">
            Overview
          </button>
          <button className="tab-button" type="button" data-tab-button="tasks">
            Tasks
          </button>
          <button className="tab-button" type="button" data-tab-button="events">
            Events
          </button>
          <button className="tab-button" type="button" data-tab-button="licenses">
            Licenses
          </button>
          <button className="tab-button" type="button" data-tab-button="incidents">
            Incidents
          </button>
          <button className="tab-button" type="button" data-tab-button="risk-flags">
            Risk flags
          </button>
          <button className="tab-button" type="button" data-tab-button="teams">
            Teams
          </button>
          <button className="tab-button" type="button" data-tab-button="garage">
            My car / garage
          </button>
          <button className="tab-button" type="button" data-tab-button="profile">
            Profile
          </button>
        </div>

        <div className="tab-panel active" data-tab-panel="overview">
          <div className="grid-2">
            {/* Next actions: loadDashboardRecommendations (dashboard.js) when profile loads.
                Data: GET /api/recommendations/latest?driver_id=&discipline= → items (risks, missing tasks, "Race next: …"). */}
            <div className="card compact">
              <p className="card-title">Next actions</p>
              <ul className="list" data-recommendation-list>
                <li>Log in to load recommendations.</li>
              </ul>
            </div>
            {/* Upcoming events: loadDashboardEvents (dashboard.js). GET /api/events → filter by driver.sim_games (only events for selected games) → only future events (start_time_utc > now), max 3. */}
            <div className="card compact">
              <p className="card-title">Upcoming events</p>
              <ul className="list" data-upcoming-events>
                <li>Log in to load events.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="licenses">
          <div className="card license-card" data-focus-id="licenses-card">
            <p className="card-title">License progress</p>
            <div data-licenses-list-view>
              <div className="license-flow">
                <button type="button" className="license-flow__badge license-flow__badge--current" data-license-current>—</button>
                <span className="license-flow__arrow" aria-hidden />
                <button type="button" className="license-flow__badge license-flow__badge--next" data-license-next>—</button>
              </div>
              <ul className="list" data-license-reqs>
                <li>No requirements loaded.</li>
              </ul>
            </div>
            <div className="license-detail-panel is-hidden" data-license-detail-panel>
              <div className="license-detail-content" data-license-detail-content />
              <button type="button" className="btn ghost" data-license-detail-back>Back</button>
            </div>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="incidents">
          <div className="card compact" data-focus-id="incidents-card">
            <p className="card-title">My incidents</p>
            <ul className="list" data-incident-list>
              <li>Log in to see incidents.</li>
            </ul>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="risk-flags">
          <div data-risk-flags-list-view className="card compact" data-focus-id="risk-flags-card">
            <p className="card-title">Risk flags</p>
            <ul className="list" data-risk-flags-tab-list>
              <li>Log in to see risk flags.</li>
            </ul>
          </div>
          <div className="risk-flag-detail-panel is-hidden" data-risk-flags-detail>
            <h3 className="risk-flag-detail-title" data-risk-flags-detail-title>—</h3>
            <p className="risk-flag-detail-explanation muted" data-risk-flags-detail-explanation>—</p>
            <p className="card-title" style={{ marginTop: '1rem' }}>Related events</p>
            <ul className="list" data-risk-flags-detail-events>
              <li>—</li>
            </ul>
            <button type="button" className="btn ghost" data-risk-flags-detail-back>Back</button>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="tasks">
          <div data-tasks-list-view className="grid-2">
            <div className="card compact card-tasks">
              <p className="card-title">Completed tasks</p>
              <ul className="list" data-tasks-completed>
                <li>No tasks completed yet.</li>
              </ul>
            </div>
            <div className="card compact card-tasks">
              <p className="card-title">Pending tasks</p>
              <ul className="list" data-tasks-pending>
                <li>No pending tasks.</li>
              </ul>
            </div>
          </div>
          <div className="task-detail-panel is-hidden" data-task-detail-panel>
            <div className="task-detail-content" data-task-detail-content />
            <div className="task-detail-actions" data-task-detail-actions>
              <button type="button" className="btn primary btn-task-take" data-task-detail-take>Take task</button>
              <button type="button" className="btn primary btn-task-complete" data-task-detail-complete>Complete</button>
              <button type="button" className="btn ghost btn-task-decline" data-task-detail-decline>Decline</button>
            </div>
            <button type="button" className="btn ghost task-detail-back" data-task-detail-back>Back</button>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="events">
          <div className="card compact" data-current-race-card style={{ display: 'none' }}>
            <p className="card-title">Current race</p>
            <p className="muted" data-current-race-event>—</p>
            <ul className="list" data-current-race-stats>
              <li data-current-race-position>Position: —</li>
              <li data-current-race-laps>Laps: —</li>
              <li data-current-race-penalties>Penalties: —</li>
              <li data-current-race-incidents>Incidents: —</li>
            </ul>
          </div>
          <div className="grid-2">
            <div className="card card-events">
              <p className="card-title">Recent events</p>
              <div data-events-list-view>
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <input type="checkbox" data-events-same-tier />
                  <span>Show only my lvl events</span>
                </label>
                <ul className="list" data-dashboard-events>
                  <li>No events loaded.</li>
                </ul>
              </div>
              <div className="event-detail-panel is-hidden" data-event-detail-panel>
                <button type="button" className="btn ghost event-detail-back" data-event-detail-back>Back</button>
                <div className="event-detail-content" data-event-detail-content />
                <div className="event-detail-actions" data-event-detail-actions>
                  <p className="event-detail-no-register-message is-hidden muted" data-event-detail-no-register-message />
                  <button type="button" className="btn primary btn-register-event-panel" data-event-detail-register disabled>Register on event</button>
                  <button type="button" className="btn secondary btn-withdraw-event-panel is-hidden" data-event-detail-withdraw>Withdraw from event</button>
                  <p className="event-detail-max-withdrawals is-hidden" data-event-detail-max-withdrawals />
                </div>
                <button type="button" className="btn ghost event-detail-back" data-event-detail-back>Back</button>
              </div>
            </div>
            <div className="card">
              <p className="card-title">Recent participations</p>
              <ul className="list" data-dashboard-participations>
                <li>No participations loaded.</li>
              </ul>
              <button className="btn ghost" type="button" data-scroll-target="#operations">
                Log participation
              </button>
            </div>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="teams">
          <div className="card compact">
            <p className="card-title">Teams</p>
            <p className="muted">Coming soon.</p>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="garage">
          <div className="card compact">
            <p className="card-title">My car / garage</p>
            <p className="muted">Coming soon.</p>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="profile">
          <div className="grid-2">
            <div className="card">
              <p className="card-title">Profile editor</p>
              <form data-profile-form>
                <div className="grid-2">
                  <div className="field-group">
                    <label htmlFor="profileFullName">Full name</label>
                    <input id="profileFullName" name="profileFullName" type="text" placeholder="Your name" />
                  </div>
                  <div className="field-group">
                    <label htmlFor="profileCountry">Country</label>
                    <input id="profileCountry" name="profileCountry" type="text" placeholder="Country" />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="field-group">
                    <label htmlFor="profileCity">City</label>
                    <input id="profileCity" name="profileCity" type="text" placeholder="City" />
                  </div>
                  <div className="field-group">
                    <label htmlFor="profileAge">Age</label>
                    <input id="profileAge" name="profileAge" type="number" min="0" max="120" placeholder="Age" />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="field-group">
                    <label htmlFor="profileExperience">Experience (years)</label>
                    <input id="profileExperience" name="profileExperience" type="number" min="0" max="60" placeholder="Experience" />
                  </div>
                  <div className="field-group">
                    <label htmlFor="profileDiscipline">Primary discipline</label>
                    <DisciplineSelect id="profileDiscipline" name="profileDiscipline" defaultValue="gt" />
                  </div>
                </div>
                <div className="field-group">
                  <label>Sim platforms</label>
                  <OptionGrid name="profilePlatforms" options={SIM_GAMES} />
                </div>
                <div className="field-group">
                  <label>Rig options</label>
                  <div className="grid-2" style={{ gap: '0.75rem' }}>
                    <div>
                      <label htmlFor="profileWheelType" className="muted" style={{ fontSize: '0.85rem' }}>Wheel</label>
                      <select id="profileWheelType" name="profileWheelType">
                        {WHEEL_TYPES.map((o) => (
                          <option key={o.value || 'empty'} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label htmlFor="profilePedalsClass" className="muted" style={{ fontSize: '0.85rem' }}>Pedals</label>
                      <select id="profilePedalsClass" name="profilePedalsClass">
                        {PEDALS_CLASSES.map((o) => (
                          <option key={o.value || 'empty'} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <label className="checkbox-label" style={{ marginTop: '0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                    <input type="checkbox" name="profileManualWithClutch" id="profileManualWithClutch" value="1" />
                    <span>Manual gearbox with clutch</span>
                  </label>
                </div>
                <button className="btn primary" type="submit">
                  Save profile
                </button>
                <div className="form-status" data-profile-save-status>
                  &nbsp;
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);

export default Cabinet;
