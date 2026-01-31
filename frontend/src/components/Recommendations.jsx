const Recommendations = () => (
  <section id="recommendations" className="section reveal" data-driver-only>
    <div className="section-heading">
      <h2>Recommendation engine</h2>
      <p>Next steps are driven by missing skills and proven behavior.</p>
    </div>
    <div className="grid-3">
      <div className="card">
        <p className="card-title">Next event</p>
        <h3>90 minute multiclass GT3</h3>
        <p className="muted">Dynamic weather, full damage, strict penalties.</p>
        <button className="btn primary" type="button">
          Add to plan
        </button>
      </div>
      <div className="card">
        <p className="card-title">Skill gap</p>
        <h3>Traffic endurance</h3>
        <p className="muted">Complete 2 events with 25+ car grids.</p>
        <button className="btn ghost" type="button">
          View skill map
        </button>
      </div>
      <div className="card">
        <p className="card-title">Readiness forecast</p>
        <h3>Almost ready</h3>
        <p className="muted">Estimated 3-5 events to reach E4 readiness.</p>
        <button className="btn ghost" type="button">
          See forecast
        </button>
      </div>
    </div>
  </section>
);

export default Recommendations;
