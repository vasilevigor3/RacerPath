const linkClass = 'text-sm text-muted-foreground hover:text-primary transition-colors';

const Footer = () => (
  <footer className="footer border-t border-border bg-card/50 py-8 px-6vw" data-auth-required data-onboarding-hidden>
    <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div>
        <h3 className="font-semibold text-foreground">RacerPath</h3>
        <p className="text-sm text-muted-foreground mt-1">Sim racing progression toward real-world motorsport.</p>
      </div>
      <div className="footer-links flex flex-wrap gap-4">
        <a href="#cabinet" className={linkClass}>Back to dashboard</a>
        <a href="#classification" className={`${linkClass} is-hidden`} data-admin-only>Classifier</a>
        <a href="#dashboards" className={`${linkClass} is-hidden`} data-admin-only>Dashboards</a>
      </div>
    </div>
  </footer>
);

export default Footer;
