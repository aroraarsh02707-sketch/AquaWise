import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
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
    <main className="auth-page auth-rebuild auth-login-enter">
      <section className="auth-form-side" aria-labelledby="login-heading">
        <Link to="/" className="auth-brand"><span className="auth-brand-mark"><Icon name="water" size={22}/></span><span>AquaWise</span><small>WATER INTELLIGENCE</small></Link>
        <div className="auth-form-shell">
          <header className="auth-header"><span className="auth-eyebrow">YOUR CONSERVATION WORKSPACE</span><h1 id="login-heading">Welcome back.</h1><p>Sign in to return to your water-use insights and recommendations.</p></header>
          {error && <div id="login-error" className="auth-error" role="alert"><Icon name="warning" size={18}/><span>{error}</span></div>}
          <form onSubmit={handleSubmit} className="auth-form"><div className="form-group"><label htmlFor="email">Email address</label><input id="email" type="email" autoComplete="email" value={email} onChange={(event) => { setEmail(event.target.value); setError(''); }} placeholder="you@example.com" required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined}/></div><div className="form-group"><label htmlFor="password">Password</label><input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => { setPassword(event.target.value); setError(''); }} placeholder="Your password" required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'login-error' : undefined}/></div><button type="submit" className="button button-primary auth-submit" disabled={isSubmitting}>{isSubmitting ? <><span className="spinner"/>Signing in…</> : <>Continue to AquaWise <Icon name="arrowRight" size={17}/></>}</button></form>
          <p className="auth-footer">New to AquaWise? <Link to="/register">Create an account <Icon name="arrowRight" size={14}/></Link></p>
        </div>
        <span className="auth-legal">Private workspace · Your usage data stays connected to your account</span>
      </section>
      <AuthAside />
    </main>
  );
}

export default Login;
