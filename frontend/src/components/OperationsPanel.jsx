import DisciplineSelect from './DisciplineSelect.jsx';

const OperationsPanel = () => (
  <div data-operations-panel className="operations-panel stack">
    <div className="grid-2">
      <div className="card compact">
        <p className="card-title">Recent drivers</p>
        <ul className="list" data-driver-list>
          <li>No drivers yet.</li>
        </ul>
      </div>
      <div className="card compact">
        <p className="card-title">Recent events</p>
        <ul className="list" data-event-list>
          <li>No events yet.</li>
        </ul>
      </div>
    </div>
    <div className="grid-4">
      <div className="card compact">
        <p className="card-title">Log participation</p>
        <form data-participation-form>
          <div className="field-group">
            <label htmlFor="participationDriverId">Driver</label>
            <select id="participationDriverId" name="participationDriverId" data-picker="driver">
              <option value="">— Select driver —</option>
            </select>
          </div>
          <div className="field-group">
            <label htmlFor="participationEventId">Event</label>
            <select id="participationEventId" name="participationEventId" data-picker="event">
              <option value="">— Select event —</option>
            </select>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationDiscipline">Discipline</label>
              <DisciplineSelect id="participationDiscipline" name="participationDiscipline" defaultValue="gt" />
            </div>
            <div className="field-group">
              <label htmlFor="participationStatus">Status</label>
              <select id="participationStatus" name="participationStatus" defaultValue="finished">
                <option value="finished">Finished</option>
                <option value="dnf">DNF</option>
                <option value="dsq">DSQ</option>
                <option value="dns">DNS</option>
              </select>
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationPositionOverall">Position overall</label>
              <input id="participationPositionOverall" name="participationPositionOverall" type="number" min="1" />
            </div>
            <div className="field-group">
              <label htmlFor="participationPositionClass">Position class</label>
              <input id="participationPositionClass" name="participationPositionClass" type="number" min="1" />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationLaps">Laps completed</label>
              <input id="participationLaps" name="participationLaps" type="number" min="0" defaultValue="0" />
            </div>
            <div className="field-group">
              <label htmlFor="participationIncidents">Incidents count</label>
              <input id="participationIncidents" name="participationIncidents" type="number" min="0" defaultValue="0" />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationPenalties">Penalties count</label>
              <input id="participationPenalties" name="participationPenalties" type="number" min="0" defaultValue="0" />
            </div>
            <div className="field-group">
              <label htmlFor="participationPaceDelta">Pace delta</label>
              <input id="participationPaceDelta" name="participationPaceDelta" type="number" step="0.01" />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationConsistency">Consistency score</label>
              <input id="participationConsistency" name="participationConsistency" type="number" step="0.01" />
            </div>
            <div className="field-group">
              <label htmlFor="participationStartedAt">Started at (UTC)</label>
              <input id="participationStartedAt" name="participationStartedAt" type="datetime-local" />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="participationFinishedAt">Finished at (UTC)</label>
              <input id="participationFinishedAt" name="participationFinishedAt" type="datetime-local" />
            </div>
            <div className="field-group">
              <label htmlFor="participationRawMetrics">Raw metrics (JSON)</label>
              <input id="participationRawMetrics" name="participationRawMetrics" type="text" placeholder='{"avg_lap": 92.4}' />
            </div>
          </div>
          <button className="btn primary" type="submit">
            Save participation
          </button>
          <div className="form-status" data-participation-status>
            &nbsp;
          </div>
        </form>
      </div>
      <div className="card compact" data-focus-id="incidents-card">
        <p className="card-title">Log incident</p>
        <form data-incident-form>
          <div className="field-group">
            <label htmlFor="incidentParticipationId">Participation</label>
            <select id="incidentParticipationId" name="incidentParticipationId" data-picker="participation">
              <option value="">— Select participation —</option>
            </select>
          </div>
          <div className="field-group">
            <label htmlFor="incidentType">Incident type</label>
            <select id="incidentType" name="incidentType" defaultValue="Contact">
              <option value="Contact">Contact</option>
              <option value="Avoidable contact">Avoidable contact</option>
              <option value="Off-track">Off-track</option>
              <option value="Track limits">Track limits</option>
              <option value="Unsafe rejoin">Unsafe rejoin</option>
              <option value="Blocking">Blocking</option>
              <option value="Mechanical">Mechanical</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="incidentSeverity">Severity (1-5)</label>
              <input id="incidentSeverity" name="incidentSeverity" type="number" min="1" max="5" defaultValue="1" />
            </div>
            <div className="field-group">
              <label htmlFor="incidentLap">Lap</label>
              <input id="incidentLap" name="incidentLap" type="number" min="0" />
            </div>
          </div>
          <div className="field-row">
            <div className="field-group">
              <label htmlFor="incidentTimestamp">Timestamp (UTC)</label>
              <input id="incidentTimestamp" name="incidentTimestamp" type="datetime-local" />
            </div>
            <div className="field-group">
              <label htmlFor="incidentDescription">Description</label>
              <input id="incidentDescription" name="incidentDescription" type="text" placeholder="Optional notes" />
            </div>
          </div>
          <button className="btn primary" type="submit">
            Save incident
          </button>
          <div className="form-status" data-incident-status>
            &nbsp;
          </div>
        </form>
      </div>
      <div className="card compact">
        <p className="card-title">Recent participations</p>
        <ul className="list" data-participation-list>
          <li>No participations yet.</li>
        </ul>
      </div>
      <div className="card compact">
        <p className="card-title">Recent incidents</p>
        <ul className="list" data-incident-list>
          <li>No incidents yet.</li>
        </ul>
      </div>
    </div>
  </div>
);

export default OperationsPanel;
