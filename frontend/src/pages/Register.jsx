import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import AuthAside from '../components/AuthAside';

function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirm_password: '', user_type: 'household' });
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
    <motion.main className="auth-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.22 }}>
      <section className="auth-panel" aria-labelledby="register-heading">
        <div className="auth-form-shell register-form-shell">
          <div className="auth-brand"><span className="auth-brand-mark"><Icon name="water" size={22} /></span><span>AquaWise</span></div>
          <header className="auth-header">
            <span className="auth-eyebrow">CREATE YOUR ACCOUNT</span>
            <h1 id="register-heading">Get started with AquaWise</h1>
            <p>Set up your profile to record and understand your water use.</p>
          </header>

          {error && <div id="register-error" className="auth-error" role="alert"><Icon name="warning" size={18} /><span>{error}</span></div>}

          <form onSubmit={handleSubmit} className="auth-form register-form">
            <div className="form-group">
              <label htmlFor="name">Full name</label>
              <input id="name" name="name" type="text" autoComplete="name" value={formData.name} onChange={handleChange} placeholder="Your name" maxLength={100} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined} />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" autoComplete="email" value={formData.email} onChange={handleChange} placeholder="name@example.com" maxLength={120} required disabled={isSubmitting} aria-invalid={Boolean(error)} aria-describedby={error ? 'register-error' : undefined} />
            </div>
            <div className="form-group">
              <label htmlFor="user_type">Account type</label>
              <select id="user_type" name="user_type" value={formData.user_type} onChange={handleChange} disabled={isSubmitting}>
                <option value="household">Household</option>
                <option value="farmer">Farmer</option>
              </select>
              <span className="auth-field-note">This helps tailor your assessment to your water use.</span>
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
            <button type="submit" className="btn-primary auth-submit" disabled={isSubmitting}>
              {isSubmitting ? <><span className="spinner auth-button-spinner" aria-hidden="true" />Creating account…</> : 'Create account'}
            </button>
          </form>

          <p className="auth-footer">Already have an account? <Link to="/login">Sign in</Link></p>
        </div>
      </section>
      <AuthAside />
    </motion.main>
  );
}

export default Register;
