import DisciplineSelect from './DisciplineSelect.jsx';
import OptionGrid from './OptionGrid.jsx';
import { RIG_OPTIONS, SIM_GAMES } from '../constants/uiData.js';

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
      <div className="card level-card">
        <p className="card-title">Profile level</p>
        <div className="level-value" data-profile-level>
          Rookie
        </div>
        <div className="progress">
          <div className="progress-label">Profile completion</div>
          <div className="progress-track">
            <div className="progress-fill" data-profile-completion style={{ width: '5%' }}></div>
          </div>
          <div className="progress-meta" data-profile-missing>
            Complete your profile to unlock the next level.
          </div>
        </div>
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
            data-scroll-target="#dashboards"
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
            data-stat-target="incidents"
            data-scroll-target="#operations"
            data-focus-target="incidents-card"
          >
            <span className="stat-label">Incidents</span>
            <span className="stat-value" data-stat-incidents>
              0
            </span>
            <span className="stat-meta">Last 10 races</span>
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
          <div className="grid-2">
            <div className="card compact">
              <p className="card-title">Risk flags</p>
              <ul className="list" data-risk-flags>
                <li>No risks yet.</li>
              </ul>
            </div>
            <div className="card">
              <p className="card-title">Profile progress</p>
              <p className="muted" data-profile-cta>
                Keep your profile updated to unlock higher readiness levels.
              </p>
            </div>
          </div>
          <div className="grid-3">
            <div className="card readiness-card">
              <p className="card-title">Readiness index</p>
              <div className="readiness-score" data-readiness-score>
                --
              </div>
              <div className="progress">
                <div className="progress-label">Readiness progress</div>
                <div className="progress-track">
                  <div className="progress-fill" data-readiness-fill style={{ width: '0%' }}></div>
                </div>
                <div className="progress-meta" data-readiness-note>
                  Complete tasks to increase readiness.
                </div>
              </div>
            </div>
            <div className="card license-card">
              <p className="card-title">License progress</p>
              <p className="muted">Current license</p>
              <h3 data-license-current>--</h3>
              <p className="muted">Next target</p>
              <h4 data-license-next>--</h4>
              <ul className="list" data-license-reqs>
                <li>No requirements loaded.</li>
              </ul>
            </div>
            <div className="card compact activity-card">
              <p className="card-title">Activity feed</p>
              <ul className="list" data-activity-feed>
                <li>No activity yet.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="tab-panel" data-tab-panel="tasks">
          <div className="grid-2">
            <div className="card compact">
              <p className="card-title">Completed tasks</p>
              <ul className="list" data-tasks-completed>
                <li>No tasks completed yet.</li>
              </ul>
            </div>
            <div className="card compact">
              <p className="card-title">Pending tasks</p>
              <ul className="list" data-tasks-pending>
                <li>No pending tasks.</li>
              </ul>
            </div>
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
            <div className="card">
              <p className="card-title">Recent events</p>
              <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <input type="checkbox" data-events-same-tier />
                <span>Show only my lvl events</span>
              </label>
              <ul className="list" data-dashboard-events>
                <li>No events loaded.</li>
              </ul>
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
                  <OptionGrid name="rigOptions" options={RIG_OPTIONS} />
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
