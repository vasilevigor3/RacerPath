import { Button } from '@/components/ui/button';

const navLinkClass =
  'inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground';

const Header = () => (
  <header className="site-header">
    <a href="#" className="logo text-foreground font-bold text-xl tracking-tight">
      RacerPath
    </a>
    <nav className="nav flex flex-wrap gap-1" data-auth-required data-onboarding-hidden>
      <a href="#cabinet" className={navLinkClass} data-driver-only>
        Cabinet
      </a>
      <a href="#operations" className={`${navLinkClass} is-hidden`} data-admin-only>
        Operations
      </a>
      <a href="#dashboards" className={`${navLinkClass} is-hidden`} data-admin-only>
        Dashboards
      </a>
    </nav>
    <div className="header-actions flex items-center gap-2">
      <Button size="sm" data-scroll-target="#auth" data-auth-only>
        Login / Register
      </Button>
      <Button size="sm" variant="outline" data-scroll-target="#cabinet" data-auth-required data-onboarding-hidden data-driver-only>
        Open dashboard
      </Button>
      <Button size="sm" variant="ghost" data-logout data-auth-required>
        Logout
      </Button>
    </div>
  </header>
);

export default Header;
