import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App.jsx';
import './styles.css';
import { setAuthVisibility, setOnboardingVisibility } from './ui/visibility.js';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

const bootstrapFeatures = async () => {
  const [
    tabsModule,
    classifierModule,
    driversModule,
    participationsModule,
    incidentsModule,
    authModule,
    onboardingModule,
    profileModule,
    crsModule,
    recommendationsModule,
    licensesModule,
    adminModule,
    dashboardModule
  ] = await Promise.all([
    import('./ui/tabs.js'),
    import('./features/classifier.js'),
    import('./features/drivers.js'),
    import('./features/participations.js'),
    import('./features/incidents.js'),
    import('./features/auth.js'),
    import('./features/onboarding.js'),
    import('./features/profile.js'),
    import('./features/crs.js'),
    import('./features/recommendations.js'),
    import('./features/licenses.js'),
    import('./features/admin.js'),
    import('./features/dashboard.js')
  ]);

  setAuthVisibility(false);
  setOnboardingVisibility(false);

  classifierModule.initClassifier();
  driversModule.initDrivers();
  participationsModule.initParticipations();
  incidentsModule.initIncidents();
  authModule.initAuth();
  onboardingModule.initOnboarding();
  setTimeout(() => profileModule.initProfileForm(), 0);
  crsModule.initCrs();
  recommendationsModule.initRecommendations();
  licensesModule.initLicenses();
  adminModule.initAdminPanel();

  driversModule.loadDrivers();
  classifierModule.loadEvents();
  dashboardModule.loadDashboardEvents();
  participationsModule.loadParticipations();
  incidentsModule.loadIncidents();
  profileModule.loadProfile();

  tabsModule.setupTabs();
  tabsModule.setupStatCardNavigation();
};

requestAnimationFrame(() => {
  bootstrapFeatures().catch((error) => {
    console.error('Failed to bootstrap RacerPath features', error);
  });
});
