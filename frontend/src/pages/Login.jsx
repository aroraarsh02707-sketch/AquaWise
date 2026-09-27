import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import AuthAside from '../components/AuthAside';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const submitLock = useRef(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (user) navigate(from, { replace: true });
  }, [user, navigate, from]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitLock.current) return;
    submitLock.current = true;
    setError('');
    setIsSubmitting(true);
    const result = await login(email, password);
    setIsSubmitting(false);
    submitLock.current = false;
    if (result.success) navigate(from, { replace: true });
    else setError(result.error || 'Login failed. Please try again.');
  };

  return (
    <motion.main className="auth-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.22 }}>
      <section className="auth-panel" aria-labelledby="login-heading">
        <div className="auth-form-shell">
          <div className="auth-brand"><span className="auth-brand-mark"><Icon name="water" size={22} /></span><span>AquaWise</span></div>
          <header className="auth-header">
            <span className="auth-eyebrow">YOUR CONSERVATION WORKSPACE</span>
            <h1 id="login-heading">Welcome back</h1>
            <p>Sign in to continue to your AquaWise account.</p>
          </header>

          {error && <div id="login-error" className="auth-error" role="alert"><Icon name="warning" size={18} /><span>{error}</span></div>}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input id="email" type="email" autoComplete="email" value={email} onChange={(event) => { setEmail(event.target.value); setError(''); }} placeholder="name@example.com" required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined} />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => { setPassword(event.target.value); setError(''); }} placeholder="Enter your password" required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined} />
            </div>
            <button type="submit" className="btn-primary auth-submit" disabled={isSubmitting}>
              {isSubmitting ? <><span className="spinner auth-button-spinner" aria-hidden="true" />Signing in…</> : 'Sign in'}
            </button>
          </form>

          <p className="auth-footer">New to AquaWise? <Link to="/register">Create an account</Link></p>
        </div>
      </section>
      <AuthAside />
    </motion.main>
  );
}

export default Login;
