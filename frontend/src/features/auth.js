import { apiFetch } from '../api/client.js';
import { resetSession, setApiKey } from '../state/session.js';
import { setAuthVisibility, setOnboardingVisibility } from '../ui/visibility.js';
import { updateReadiness } from '../ui/readiness.js';
import { loadProfile, setProfileEmpty } from './profile.js';

const registerForm = document.querySelector('[data-register-form]');
const registerStatus = document.querySelector('[data-register-status]');
const loginForm = document.querySelector('[data-login-form]');
const loginStatus = document.querySelector('[data-login-status]');
const logoutButton = document.querySelector('[data-logout]');

export const initAuth = () => {
  if (registerForm && registerStatus) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const loginInput = registerForm.querySelector('#registerLogin');
      const emailInput = registerForm.querySelector('#registerEmail');
      const passwordInput = registerForm.querySelector('#registerPassword');
      const login = loginInput ? loginInput.value.trim() : '';
      const email = emailInput ? emailInput.value.trim() : '';
      const password = passwordInput ? passwordInput.value : '';
      if (!login || !email || !password) {
        registerStatus.textContent = 'Login, email, and password are required.';
        return;
      }
      registerStatus.textContent = 'Creating account...';
      try {
        const res = await apiFetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ login, email, password })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          registerStatus.textContent = err.detail || 'Registration failed.';
          return;
        }
        const data = await res.json();
        setApiKey(data.api_key);
        setAuthVisibility(true);
        if (passwordInput) passwordInput.value = '';
        registerStatus.textContent = 'Account created. Complete onboarding.';
        await loadProfile();
      } catch (err) {
        registerStatus.textContent = 'Registration failed.';
      }
    });
  }

  if (loginForm && loginStatus) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const emailInput = loginForm.querySelector('#loginEmail');
      const passwordInput = loginForm.querySelector('#loginPassword');
      const email = emailInput ? emailInput.value.trim() : '';
      const password = passwordInput ? passwordInput.value : '';
      if (!email || !password) {
        loginStatus.textContent = 'Email and password required.';
        return;
      }
      loginStatus.textContent = 'Logging in...';
      try {
        const res = await apiFetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          loginStatus.textContent = err.detail || 'Login failed.';
          return;
        }
        const data = await res.json();
        setApiKey(data.api_key);
        setAuthVisibility(true);
        if (passwordInput) passwordInput.value = '';
        await loadProfile();
      } catch (err) {
        loginStatus.textContent = 'Login failed.';
      }
    });
  }

  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      resetSession();
      setAuthVisibility(false);
      setOnboardingVisibility(false);
      setProfileEmpty('Log in to see your profile.');
      if (loginStatus) loginStatus.textContent = 'Logged out.';
      updateReadiness();
    });
  }
}
