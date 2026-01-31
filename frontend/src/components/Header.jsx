const Header = () => (
  <header className="site-header">
    <div className="logo">RacerPath</div>
    <nav className="nav" data-auth-required data-onboarding-hidden>
      <a href="#cabinet" data-driver-only>
        Cabinet
      </a>
      <a href="#operations" className="is-hidden" data-admin-only>
        Operations
      </a>
      <a href="#dashboards" className="is-hidden" data-admin-only>
        Dashboards
      </a>
      <a href="#recommendations" data-driver-only>
        Recommendations
      </a>
    </nav>
    <div className="header-actions">
      <button className="btn primary" type="button" data-scroll-target="#auth" data-auth-only>
        Login / Register
      </button>
      <button
        className="btn primary"
        type="button"
        data-scroll-target="#cabinet"
        data-auth-required
        data-onboarding-hidden
        data-driver-only
      >
        Open dashboard
      </button>
      <button className="btn ghost" type="button" data-logout data-auth-required>
        Logout
      </button>
    </div>
  </header>
);

export default Header;
