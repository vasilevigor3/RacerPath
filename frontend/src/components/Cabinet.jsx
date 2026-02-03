import DisciplineSelect from './DisciplineSelect.jsx';
import OptionGrid from './OptionGrid.jsx';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
        <Card className="profile-card border-border/80 shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Driver identity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div className="avatar" data-profile-initials>
              RP
            </div>
            <h3 className="font-semibold text-foreground" data-profile-fullname>--</h3>
            <p className="text-sm text-muted-foreground" data-profile-location>
              Location not set
            </p>
            <p className="text-sm text-muted-foreground" data-profile-user-id>
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
            <Button variant="outline" className="w-full" type="button" data-tab-jump="profile" data-profile-cta-button>
              Complete profile
            </Button>
          </CardContent>
        </Card>
      </aside>

      <div className="dashboard-main">
        <div className="stats-grid gap-3">
          <button
            className="stat-card is-link rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            type="button"
            data-stat-target="crs"
            data-scroll-target="#dashboards"
            data-focus-target="crs-card"
          >
            <span className="stat-label text-muted-foreground">CRS</span>
            <span className="stat-value text-foreground" data-stat-crs>
              --
            </span>
            <span className="stat-meta text-muted-foreground">Latest score</span>
          </button>
          <button
            className="stat-card is-link rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            type="button"
            data-stat-target="events"
            data-tab-target="events"
          >
            <span className="stat-label text-muted-foreground">Events raced</span>
            <span className="stat-value text-foreground" data-stat-events>0</span>
            <span className="stat-meta text-muted-foreground">Last 30 days</span>
          </button>
          <button
            className="stat-card is-link rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            type="button"
            data-stat-target="tasks"
            data-tab-target="tasks"
          >
            <span className="stat-label text-muted-foreground">Tasks done</span>
            <span className="stat-value text-foreground" data-stat-tasks>0</span>
            <span className="stat-meta text-muted-foreground">Completed</span>
          </button>
          <button
            className="stat-card is-link rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            type="button"
            data-stat-target="licenses"
            data-tab-target="licenses"
            data-focus-target="licenses-card"
          >
            <span className="stat-label text-muted-foreground">Licenses</span>
            <span className="stat-value text-foreground" data-stat-licenses>0</span>
            <span className="stat-meta text-muted-foreground">Earned</span>
          </button>
          <button
            className="stat-card is-link rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md hover:border-primary/40 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            type="button"
            data-stat-target="risk-flags"
            data-tab-target="risk-flags"
            data-focus-target="risk-flags-card"
          >
            <span className="stat-label text-muted-foreground">Risk flags</span>
            <span className="stat-value text-foreground" data-stat-risk-flags>0</span>
            <span className="stat-meta text-muted-foreground">Review</span>
          </button>
        </div>

        <div className="tabs flex flex-wrap gap-1 rounded-lg bg-muted/50 p-1">
          <button className="tab-button active rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="overview">
            Overview
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="tasks">
            Tasks
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="events">
            Events
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="licenses">
            Licenses
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="risk-flags">
            Risk flags
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="teams">
            Teams
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="garage">
            My car / garage
          </button>
          <button className="tab-button rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-background hover:text-foreground" type="button" data-tab-button="profile">
            Profile
          </button>
        </div>

        <div className="tab-panel active" data-tab-panel="overview">
          <div className="grid-2">
            {/* Next actions: 2 columns — Tasks (open task card), Race of d/w/m/y (open event card). */}
            <Card className="border-border/80 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Next actions
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="next-actions-grid">
                  <div>
                    <p className="next-actions-column-title">Tasks</p>
                    <div className="next-action-cards" data-recommendation-tasks role="list">
                      <div role="listitem">Log in to load recommendations.</div>
                    </div>
                  </div>
                  <div>
                    <p className="next-actions-column-title">Race of d/w/m/y</p>
                    <div className="next-action-cards" data-recommendation-races role="list">
                      <div role="listitem">—</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            {/* Upcoming events: loadDashboardEvents (dashboard.js). Event cards, same as Events tab. */}
            <Card className="border-border/80 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Upcoming events
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="overview-upcoming-scroll">
                  <div className="event-cards" data-upcoming-events role="list">
                    <div role="listitem">Log in to load events.</div>
                  </div>
                </div>
              </CardContent>
            </Card>
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
              <button type="button" className="btn ghost btn-back-arrow" data-license-detail-back aria-label="Back"><span aria-hidden>←</span></button>
            </div>
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
          <div className="grid-2 risk-flags-incidents-penalties">
            <div className="card compact" data-focus-id="incidents-card">
              <p className="card-title">My incidents (<span className="tab-count" data-incidents-total-card aria-label="Total incidents">0</span>)</p>
              <div data-incidents-list-view>
                <div className="incident-cards-scroll" data-incident-scroll>
                  <div className="incident-cards" data-incident-list role="list">
                    <div role="listitem">Log in to see incidents.</div>
                  </div>
                </div>
              </div>
              <div className="incident-detail-panel is-hidden" data-incident-detail>
                <h3 className="incident-detail-title" data-incident-detail-type>—</h3>
                <p className="incident-detail-race muted" data-incident-detail-race>—</p>
                <p className="incident-detail-meta" data-incident-detail-meta>—</p>
                <p className="incident-detail-desc muted" data-incident-detail-desc></p>
                <button type="button" className="btn ghost" data-incident-detail-back>Back</button>
              </div>
            </div>
            <div className="card compact" data-focus-id="penalties-card">
              <p className="card-title">My penalties (<span className="tab-count" data-penalties-total-card aria-label="Total penalties">0</span>)</p>
              <div data-penalties-list-view>
                <div className="penalty-cards-scroll" data-penalty-scroll>
                  <div className="penalty-cards" data-penalty-list role="list">
                    <div role="listitem">Log in to see penalties.</div>
                  </div>
                </div>
              </div>
              <div className="penalty-detail-panel is-hidden" data-penalty-detail>
                <h3 className="penalty-detail-title" data-penalty-detail-type>—</h3>
                <p className="penalty-detail-race muted" data-penalty-detail-race>—</p>
                <p className="penalty-detail-meta" data-penalty-detail-meta>—</p>
                <p className="penalty-detail-desc muted" data-penalty-detail-desc></p>
                <button type="button" className="btn ghost" data-penalty-detail-back>Back</button>
              </div>
            </div>
          </div>
          <button type="button" className="btn ghost risk-flags-bottom-back" data-risk-flags-detail-back>Back</button>
        </div>

        <div className="tab-panel" data-tab-panel="tasks">
          <div data-tasks-list-view className="grid-3">
            <div className="card compact card-tasks">
              <p className="card-title">Pending tasks</p>
              <ul className="list" data-tasks-pending>
                <li>No pending tasks.</li>
              </ul>
            </div>
            <div className="card compact card-tasks">
              <p className="card-title">In progress</p>
              <ul className="list" data-tasks-in-progress>
                <li>No tasks in progress.</li>
              </ul>
            </div>
            <div className="card compact card-tasks">
              <p className="card-title">Completed</p>
              <ul className="list" data-tasks-completed>
                <li>No tasks completed yet.</li>
              </ul>
            </div>
          </div>
          <div className="task-detail-panel is-hidden" data-task-detail-panel>
            <div className="task-detail-content" data-task-detail-content />
            <p className="task-detail-event-related-msg is-hidden muted" data-task-detail-event-related-msg />
            <div className="task-detail-actions" data-task-detail-actions>
              <button type="button" className="btn primary btn-task-take" data-task-detail-take>Take task</button>
              <button type="button" className="btn ghost btn-task-decline" data-task-detail-decline>Decline</button>
            </div>
            <button type="button" className="btn ghost btn-back-arrow task-detail-back" data-task-detail-back aria-label="Back"><span aria-hidden>←</span></button>
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
              <p className="card-title">Upcoming events</p>
              <div data-events-list-view>
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <input type="checkbox" data-events-same-tier />
                  <span>Show only my lvl events</span>
                </label>
                <div className="upcoming-events-scroll" data-upcoming-events-scroll>
                  <div className="event-cards" data-dashboard-events role="list">
                    <div role="listitem">No events loaded.</div>
                  </div>
                </div>
              </div>
              <div className="event-detail-panel is-hidden" data-event-detail-panel>
                <div className="event-detail-content" data-event-detail-content />
                <div className="event-detail-actions" data-event-detail-actions>
                  <p className="event-detail-no-register-message is-hidden muted" data-event-detail-no-register-message />
                  <button type="button" className="btn primary btn-register-event-panel" data-event-detail-register disabled>Register on event</button>
                  <button type="button" className="btn secondary btn-withdraw-event-panel is-hidden" data-event-detail-withdraw>Withdraw from event</button>
                  <p className="event-detail-max-withdrawals is-hidden" data-event-detail-max-withdrawals />
                </div>
                <button type="button" className="btn ghost btn-back-arrow event-detail-back" data-event-detail-back aria-label="Back"><span aria-hidden>←</span></button>
              </div>
            </div>
            <div className="card">
              <p className="card-title">Past events</p>
              <div className="past-events-scroll" data-past-events-scroll>
                <div className="event-cards" data-dashboard-past-events role="list">
                  <div role="listitem">No past events.</div>
                </div>
              </div>
            </div>
            <div className="card">
              <p className="card-title">Recent participations</p>
              <div data-dashboard-participations-list-view>
                <div className="participation-cards-scroll" data-participation-scroll>
                  <div className="participation-cards" data-dashboard-participations role="list">
                    <div role="listitem">No participations loaded.</div>
                  </div>
                </div>
              </div>
              <div className="participation-detail-panel is-hidden" data-participation-detail>
                <h3 className="participation-detail-title" data-participation-detail-event>—</h3>
                <p className="participation-detail-meta" data-participation-detail-meta>—</p>
                <p className="participation-detail-stats muted" data-participation-detail-stats>—</p>
                <button type="button" className="btn ghost" data-participation-detail-back>Back</button>
              </div>
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
