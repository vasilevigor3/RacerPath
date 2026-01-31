const AuthLanding = () => (
  <section id="auth" className="section auth-landing reveal" data-auth-only>
    <div className="auth-hero">
      <div>
        <p className="eyebrow">Start here</p>
        <h1>Sign in to your private racing cabinet.</h1>
        <p className="lead">
          Create an account, log in, and unlock your personal dashboard with tasks, events, and readiness stats.
        </p>
      </div>
      <div className="auth-card">
        <div className="card">
          <p className="card-title">Create account</p>
          <form data-register-form>
            <div className="field-group">
              <label htmlFor="registerLogin">Login</label>
              <input id="registerLogin" name="registerLogin" type="text" autoComplete="username" placeholder="igor" />
            </div>
            <div className="field-group">
              <label htmlFor="registerEmail">Email</label>
              <input id="registerEmail" name="registerEmail" type="email" autoComplete="email" placeholder="igor@mail.com" />
            </div>
            <div className="field-group">
              <label htmlFor="registerPassword">Password</label>
              <input
                id="registerPassword"
                name="registerPassword"
                type="password"
                autoComplete="new-password"
                placeholder="Create a password"
              />
            </div>
            <button className="btn primary" type="submit">
              Register
            </button>
            <div className="form-status" data-register-status>
              &nbsp;
            </div>
          </form>
        </div>
        <div className="card">
          <p className="card-title">Login</p>
          <form data-login-form>
            <div className="field-group">
              <label htmlFor="loginEmail">Email</label>
              <input id="loginEmail" name="loginEmail" type="email" autoComplete="email" placeholder="you@mail.com" />
            </div>
            <div className="field-group">
              <label htmlFor="loginPassword">Password</label>
              <input id="loginPassword" name="loginPassword" type="password" autoComplete="current-password" placeholder="Your password" />
            </div>
            <button className="btn primary" type="submit">
              Login
            </button>
            <div className="form-status" data-login-status>
              Not logged in.
            </div>
          </form>
        </div>
      </div>
    </div>
  </section>
);

export default AuthLanding;
