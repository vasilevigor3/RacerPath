import DisciplineSelect from './DisciplineSelect.jsx';

const AdminCabinet = () => (
  <div data-admin-panel className="admin-cabinet-panel">
    <div className="card compact admin-live-card" style={{ marginTop: '24px' }}>
      <p className="card-title">Live metrics</p>
      <ul className="list" data-admin-live-stats>
        <li>No admin metrics yet.</li>
      </ul>
    </div>
    <div className="admin-search-row">
      <div className="card compact admin-search-card">
        <p className="card-title">User search</p>
        <form className="inline-form" data-admin-user-search-form>
          <div className="inline-fields">
            <div className="field-group">
              <label htmlFor="adminUserSearchEmail">Email</label>
              <input
                id="adminUserSearchEmail"
                name="adminUserSearchEmail"
                type="email"
                placeholder="driver@mail.com"
                data-admin-user-search-input
              />
            </div>
          </div>
          <button className="btn primary" type="submit">
            Search
          </button>
        </form>
        <div className="admin-output" data-admin-user-search-output>
          Search by email to see driver details.
        </div>
      </div>
      <div className="card compact admin-search-card">
        <p className="card-title">Participation search</p>
        <form className="inline-form" data-admin-participation-search-form>
          <div className="inline-fields">
            <div className="field-group">
              <label htmlFor="adminParticipationSearch">Driver ID or email</label>
              <input
                id="adminParticipationSearch"
                name="adminParticipationSearch"
                type="text"
                placeholder="driver id or email"
                data-admin-participation-search-input
              />
            </div>
          </div>
          <button className="btn primary" type="submit">
            Search
          </button>
        </form>
        <div className="admin-output" data-admin-participation-search-output>
          Search to load participations.
        </div>
      </div>
    </div>
    <div className="admin-grid">
      <div className="card compact admin-card-full">
        <p className="card-title">User accounts</p>
        <ul className="list" data-admin-user-list>
          <li>Loading users...</li>
        </ul>
      </div>
      <div className="card compact admin-card-full">
        <p className="card-title">Recent participations</p>
        <ul className="list" data-admin-recent-participations>
          <li>—</li>
        </ul>
      </div>
      <div className="card compact admin-card-full">
        <p className="card-title">Recent incidents</p>
        <ul className="list" data-admin-recent-incidents>
          <li>—</li>
        </ul>
      </div>
      <div className="card compact admin-card-full">
        <p className="card-title">Published events</p>
        <form className="inline-form" data-admin-events-filter>
          <div className="inline-fields">
            <div className="field-group">
              <label htmlFor="adminEventsGame">Game</label>
              <input id="adminEventsGame" name="adminEventsGame" type="text" placeholder="e.g. ac2" />
            </div>
            <div className="field-group">
              <label htmlFor="adminEventsDateFrom">From</label>
              <input id="adminEventsDateFrom" name="adminEventsDateFrom" type="date" />
            </div>
            <div className="field-group">
              <label htmlFor="adminEventsDateTo">To</label>
              <input id="adminEventsDateTo" name="adminEventsDateTo" type="date" />
            </div>
          </div>
          <button className="btn primary" type="submit">Filter</button>
        </form>
        <ul className="list admin-event-list" data-admin-event-list>
          <li>Loading events...</li>
        </ul>
        <div className="admin-output" data-admin-event-classification aria-label="Event classification" />
        <button className="btn ghost" type="button" data-admin-refresh-events>
          Refresh events
        </button>
      </div>
    </div>
    <div className="stack">
      <div className="grid-2">
        <div className="card compact">
          <p className="card-title">Player inspector</p>
          <div className="admin-inline-panel">
            <form className="inline-form" data-admin-player-form>
              <div className="inline-fields">
                <div className="field-group">
                  <label htmlFor="adminPlayerId">Driver ID or email</label>
                  <input id="adminPlayerId" name="adminPlayerId" type="text" placeholder="ABCDE-12345 or email" />
                </div>
              </div>
              <button className="btn primary" type="submit">
                Search
              </button>
              <div className="form-status" data-admin-player-status>
                &nbsp;
              </div>
            </form>
            <div className="admin-output" data-admin-player-output>
              <div className="admin-output-grid" data-admin-player-summary>
                Provide an ID to inspect a driver.
              </div>
              <div className="admin-output-crs" data-admin-player-crs aria-label="CRS and licenses" />
              <ul className="list" data-admin-player-participations>
                <li>No participations loaded.</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="card compact">
          <p className="card-title">Profile adjustments</p>
          <form data-admin-player-profile-form>
            <div className="field-group">
              <label htmlFor="adminProfileDiscipline">Primary discipline</label>
              <DisciplineSelect id="adminProfileDiscipline" name="adminProfileDiscipline" includeKeepCurrent />
            </div>
            <div className="field-group">
              <label htmlFor="adminProfilePlatforms">Sim platforms</label>
              <input id="adminProfilePlatforms" name="adminProfilePlatforms" type="text" placeholder="Comma separated" />
            </div>
            <div className="field-row">
              <div className="field-group">
                <label htmlFor="adminProfileExperience">Experience (years)</label>
                <input id="adminProfileExperience" name="adminProfileExperience" type="number" min="0" max="60" />
              </div>
              <div className="field-group">
                <label htmlFor="adminProfileAge">Age</label>
                <input id="adminProfileAge" name="adminProfileAge" type="number" min="0" max="120" />
              </div>
            </div>
            <button className="btn primary" type="submit">
              Save profile
            </button>
            <div className="form-status" data-admin-player-profile-status>
              &nbsp;
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
);

export default AdminCabinet;
