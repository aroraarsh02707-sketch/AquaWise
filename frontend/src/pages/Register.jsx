import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MotionConfig, motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import AuthAside from '../components/AuthAside';

function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirm_password: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const submitLock = useRef(false);
  const { register, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true });
  }, [user, navigate]);

  const handleChange = (event) => {
    const { id, value } = event.target;
    setFormData((previous) => ({ ...previous, [id]: value }));
    setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submitLock.current) return;
    setError('');
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match. Check both fields and try again.');
      return;
    }
    if (formData.password.length < 6) {
      setError('Your password must contain at least 6 characters.');
      return;
    }

    submitLock.current = true;
    setIsSubmitting(true);
    const result = await register(formData);
    setIsSubmitting(false);
    submitLock.current = false;
    if (result.success) navigate('/dashboard', { replace: true });
    else setError(result.error || 'Your account could not be created. Please try again.');
  };

  return (
    <MotionConfig reducedMotion="user">
      <motion.main className="auth-page auth-rebuild" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.22 }}>
      <section className="auth-form-side" aria-labelledby="register-heading">
        <Link to="/" className="auth-brand"><span className="auth-brand-mark"><Icon name="water" size={22}/></span><span>AquaWise</span><small>WATER INTELLIGENCE</small></Link>
        <div className="auth-form-shell register-form-shell">
          <header className="auth-header"><span className="auth-eyebrow">CREATE YOUR ACCOUNT</span><h1 id="register-heading">Make water count.</h1><p>Tell us a little about your water use so your workspace starts in the right place.</p></header>
          {error && <div id="register-error" className="auth-error" role="alert"><Icon name="warning" size={18}/><span>{error}</span></div>}
          <form onSubmit={handleSubmit} className="auth-form register-form">
            <div className="form-group">
              <label htmlFor="name">Full name</label>
              <input id="name" name="name" type="text" autoComplete="name" value={formData.name} onChange={handleChange} placeholder="Your name" maxLength={100} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined} />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" autoComplete="email" value={formData.email} onChange={handleChange} placeholder="name@example.com" maxLength={120} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined} />
            </div>
            <div className="auth-password-grid">
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input id="password" name="password" type="password" autoComplete="new-password" value={formData.password} onChange={handleChange} placeholder="At least 6 characters" minLength={6} maxLength={200} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : 'password-note'} />
                <span id="password-note" className="auth-field-note">Use at least 6 characters.</span>
              </div>
              <div className="form-group">
                <label htmlFor="confirm_password">Confirm password</label>
                <input id="confirm_password" name="confirm_password" type="password" autoComplete="new-password" value={formData.confirm_password} onChange={handleChange} placeholder="Enter it again" minLength={6} maxLength={200} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined} />
              </div>
            </div>
            <button type="submit" className="button button-primary auth-submit" disabled={isSubmitting}>{isSubmitting ? <><span className="spinner"/>Creating workspace…</> : <>Create your workspace <Icon name="arrowRight" size={17}/></>}</button>
          </form>
          <p className="auth-footer">Already have an account? <Link to="/login">Sign in <Icon name="arrowRight" size={14}/></Link></p>
        </div>
        <span className="auth-legal">Private workspace · Your usage data stays connected to your account</span>
      </section>
      <AuthAside />
      </motion.main>
    </MotionConfig>
  );
}

export default Register;
