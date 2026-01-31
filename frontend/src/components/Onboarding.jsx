import DisciplineSelect from './DisciplineSelect.jsx';
import OptionGrid from './OptionGrid.jsx';
import { SIM_GAMES } from '../constants/uiData.js';

const Onboarding = () => (
  <section id="onboarding" className="section onboarding reveal" data-onboarding-only data-driver-only>
    <div className="section-heading">
      <h2>Finish onboarding</h2>
      <p>Before we can recommend races and tasks, we need your games and discipline path.</p>
    </div>
    <div className="grid-2">
      <div className="card">
        <p className="card-title">Required setup</p>
        <ul className="list">
          <li>Select the sim games you race</li>
          <li>Choose your primary discipline path</li>
        </ul>
        <p className="muted">This unlocks tailored events, tasks, and readiness tracking.</p>
      </div>
      <div className="card">
        <p className="card-title">Driver onboarding</p>
        <p className="muted" data-profile-status>
          Log in to see your profile.
        </p>
        <div className="pill-row">
          <span className="pill" data-profile-name>
            --
          </span>
          <span className="pill" data-profile-role>
            --
          </span>
        </div>
        <p className="muted" data-profile-driver>
          No driver profile yet.
        </p>
        <form data-my-driver-form>
          <div className="field-group">
            <label htmlFor="myDriverName">Driver name</label>
            <input id="myDriverName" name="myDriverName" type="text" placeholder="My driver name" />
          </div>
          <div className="field-group">
            <label htmlFor="myDriverDiscipline">Primary discipline</label>
            <DisciplineSelect id="myDriverDiscipline" name="myDriverDiscipline" defaultValue="gt" />
          </div>
          <div className="field-group">
            <label>Sim games</label>
            <OptionGrid name="simGames" options={SIM_GAMES} />
          </div>
          <button className="btn primary" type="submit">
            Save and continue
          </button>
          <div className="form-status" data-my-driver-status>
            &nbsp;
          </div>
        </form>
      </div>
    </div>
  </section>
);

export default Onboarding;
