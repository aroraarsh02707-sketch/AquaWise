import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { profileService } from '../services/api';
import { useAuth } from '../context/AuthContext';

const AchievementCard = ({ achievement }) => {
  const { unlocked, name, description, badge_icon, earned_at } = achievement;
  return (
    <div className={`achievement-card ${unlocked ? 'unlocked' : 'locked'}`}>
      <div className="achievement-icon">{badge_icon || '🏅'}</div>
      <div className="achievement-body">
        <h4>{name}</h4>
        <p>{description}</p>
        {unlocked && earned_at && (
          <span className="achievement-date">Earned {new Date(earned_at).toLocaleDateString()}</span>
        )}
      </div>
      <span className={`achievement-badge ${unlocked ? 'unlocked-badge' : 'locked-badge'}`}>
        {unlocked ? '✓ Unlocked' : 'Locked'}
      </span>
    </div>
  );
};

const Profile = () => {
  const { user: authUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formName, setFormName] = useState('');
  const [formUserType, setFormUserType] = useState('household');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const [profileRes, achRes] = await Promise.all([
          profileService.getProfile(),
          profileService.getAchievements(),
        ]);
        if (profileRes.data.success) {
          const p = profileRes.data.data.profile;
          setProfile(p);
          setFormName(p.name || '');
          setFormUserType(p.user_type || 'household');
        }
        if (achRes.data.success) setAchievements(achRes.data.data.achievements);
      } catch {
        setError('Failed to load profile. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaveError(null);
    setSaveSuccess(false);
    setSaving(true);
    try {
      const res = await profileService.updateProfile({ name: formName, user_type: formUserType });
      if (res.data.success) {
        setProfile(prev => ({ ...prev, ...res.data.data.profile }));
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3500);
      }
    } catch (err) {
      if (err.response?.data?.error?.details) {
        setSaveError(Object.values(err.response.data.error.details)[0] || 'Validation failed.');
      } else {
        setSaveError(err.response?.data?.error?.message || 'Failed to save. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" />
      <p>Loading your profile…</p>
    </div>
  );

  if (error) return (
    <div className="state-error">
      <p>{error}</p>
      <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
    </div>
  );

  const streak = profile?.streak || {};
  const badges = profile?.badges || [];
  const unlockedCount = achievements.filter(a => a.unlocked).length;

  return (
    <motion.div className="profile-page"
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
    >
      <header className="page-header" style={{ marginBottom: '2rem' }}>
        <div>
          <h2>My Profile</h2>
          <p className="subtitle">Manage your account and track your conservation achievements.</p>
        </div>
      </header>

      <div className="profile-grid">
        {/* ── Left Column ── */}
        <div>
          {/* Profile Card Header */}
          <div className="profile-card">
            <div className="profile-card-header">
              <div className="profile-avatar">{profile?.name?.charAt(0).toUpperCase()}</div>
              <p className="profile-name">{profile?.name}</p>
              <p className="profile-email">{profile?.email}</p>
            </div>
          </div>

          {/* Edit form below the header card */}
          <div className="profile-form-card">
            <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.25rem' }}>Edit Account</h3>
            <form onSubmit={handleSave} className="profile-form">
              <div className="form-group">
                <label htmlFor="prof-name">Display Name</label>
                <input id="prof-name" type="text" value={formName}
                  onChange={e => { setFormName(e.target.value); setSaveSuccess(false); }}
                  maxLength={100} required disabled={saving} />
              </div>
              <div className="form-group">
                <label htmlFor="prof-type">User Type</label>
                <select id="prof-type" value={formUserType}
                  onChange={e => setFormUserType(e.target.value)} disabled={saving}>
                  <option value="household">Household</option>
                  <option value="farmer">Farmer</option>
                </select>
              </div>

              {saveError && <div className="auth-error">{saveError}</div>}
              {saveSuccess && <div className="save-success">✓ Profile saved successfully.</div>}

              <button type="submit" className="btn-primary auth-submit" disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </form>
          </div>

          {/* Stats */}
          <div className="profile-stats-card">
            <p className="stats-heading">Your Stats</p>
            <div className="profile-stats">
              <div className="profile-stat">
                <span className="profile-stat-value">{profile?.assessment_count ?? 0}</span>
                <span className="profile-stat-label">Assessments</span>
              </div>
              <div className="profile-stat">
                <span className="profile-stat-value">{streak.current_streak ?? 0}</span>
                <span className="profile-stat-label">Day Streak 🔥</span>
              </div>
              <div className="profile-stat">
                <span className="profile-stat-value">{streak.longest_streak ?? 0}</span>
                <span className="profile-stat-label">Best Streak</span>
              </div>
              <div className="profile-stat">
                <span className="profile-stat-value">{badges.length}</span>
                <span className="profile-stat-label">Badges Earned</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right Column: Achievements ── */}
        <div className="achievements-section">
          <div className="achievements-header">
            <h3>Achievements</h3>
            <span className="achievements-count">{unlockedCount} / {achievements.length} unlocked</span>
          </div>

          {achievements.length === 0 ? (
            <div className="empty-state" style={{ padding: '2rem', border: 'none' }}>
              <div className="empty-icon">🏅</div>
              <p>Complete assessments to earn achievements!</p>
            </div>
          ) : (
            <div className="achievements-list">
              {[...achievements]
                .sort((a, b) => (b.unlocked ? 1 : 0) - (a.unlocked ? 1 : 0))
                .map((ach, i) => (
                  <motion.div key={ach.id}
                    initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                  >
                    <AchievementCard achievement={ach} />
                  </motion.div>
                ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default Profile;
