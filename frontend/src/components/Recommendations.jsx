/**
 * Recommendation engine block.
 * Data source: GET /api/recommendations/latest?driver_id=&discipline=
 * Filled by loadDashboardRecommendations (dashboard.js) when profile loads:
 * - readiness_status + summary → Readiness forecast card
 * - first "Race next: ..." from items → Next event card
 * - first "Complete task: ..." or "Risk: ..." from items → Skill gap card
 */
const Recommendations = () => (
  <section id="recommendations" className="section reveal" data-driver-only>
    <div className="section-heading">
      <h2>Recommendation engine</h2>
      <p>Next steps are driven by missing skills and proven behavior.</p>
    </div>
    <div className="grid-3">
      <div className="card" data-rec-card="next-event">
        <p className="card-title">Next event</p>
        <h3 data-rec-next-event-title>—</h3>
        <p className="muted" data-rec-next-event-desc>Load profile to see recommended event.</p>
        <button className="btn primary" type="button">
          Add to plan
        </button>
      </div>
      <div className="card" data-rec-card="skill-gap">
        <p className="card-title">Skill gap</p>
        <h3 data-rec-skill-gap-title>—</h3>
        <p className="muted" data-rec-skill-gap-desc>Load profile to see next skill focus.</p>
        <button className="btn ghost" type="button">
          View skill map
        </button>
      </div>
      <div className="card" data-rec-card="readiness">
        <p className="card-title">Readiness forecast</p>
        <h3 data-rec-readiness-title>—</h3>
        <p className="muted" data-rec-readiness-desc>Load profile to see readiness.</p>
        <button className="btn ghost" type="button">
          See forecast
        </button>
      </div>
    </div>
  </section>
);

export default Recommendations;
