const Footer = () => (
  <footer className="footer" data-auth-required data-onboarding-hidden>
    <div>
      <h3>RacerPath</h3>
      <p className="muted">Sim racing progression toward real-world motorsport.</p>
    </div>
    <div className="footer-links">
      <a href="#cabinet">Back to dashboard</a>
      <a href="#classification" data-admin-only>
        Classifier
      </a>
      <a href="#dashboards" data-admin-only>
        Dashboards
      </a>
    </div>
  </footer>
);

export default Footer;
