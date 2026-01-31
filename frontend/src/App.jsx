import AuthLanding from './components/AuthLanding.jsx';
import Cabinet from './components/Cabinet.jsx';
import Footer from './components/Footer.jsx';
import Header from './components/Header.jsx';
import Onboarding from './components/Onboarding.jsx';
import Operations from './components/Operations.jsx';
import Recommendations from './components/Recommendations.jsx';

const App = () => (
  <>
    <div className="bg-grid" aria-hidden="true"></div>
    <Header />

    <main>
      <AuthLanding />
      <div data-auth-required>
        <Onboarding />
        <Operations />
        <div data-onboarding-hidden>
          <Cabinet />
          <Recommendations />
        </div>
      </div>
    </main>

    <Footer />
  </>
);

export default App;
