import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { profileService } from '../services/api';
import Icon from '../components/Icon';

function formatDate(value) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric', year: 'numeric' }).format(date);
}

function LoadingState({ label }) {
  return <div className="profile-loading-state" role="status"><span className="spinner" /><span>{label}</span></div>;
}

function AchievementCard({ achievement, index }) {
  const unlocked = achievement.unlocked === true;
  return (
    <motion.article className={`achievement-card ${unlocked ? 'unlocked' : 'locked'}`} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2, delay: Math.min(index * 0.035, 0.21) }}>
      <span className={`achievement-icon ${unlocked ? 'earned' : ''}`} aria-hidden="true"><Icon name={unlocked ? 'score' : 'water'} size={21} /></span>
      <div className="achievement-body">
        <h3>{achievement.name || 'Achievement'}</h3>
        {achievement.description && <p>{achievement.description}</p>}
        {unlocked && achievement.earned_at && <time className="achievement-date" dateTime={achievement.earned_at}>Earned {formatDate(achievement.earned_at)}</time>}
      </div>
      <span className={`achievement-status ${unlocked ? 'unlocked-badge' : 'locked-badge'}`}>
        <span className="achievement-status-mark" aria-hidden="true">{unlocked ? '✓' : '○'}</span>{unlocked ? 'Completed' : 'Not yet earned'}
      </span>
    </motion.article>
  );
}

function Profile() {
  const [profile, setProfile] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [profileLoading, setProfileLoading] = useState(true);
  const [achievementsLoading, setAchievementsLoading] = useState(true);
  const [profileError, setProfileError] = useState('');
  const [achievementsError, setAchievementsError] = useState('');
  const [formName, setFormName] = useState('');
  const [formUserType, setFormUserType] = useState('household');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const saveLock = useRef(false);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError('');
    try {
      const response = await profileService.getProfile();
      const data = response?.data?.data?.profile;
      if (!response?.data?.success || !data) throw new Error('Profile is unavailable.');
      setProfile(data);
      setFormName(data.name || '');
      setFormUserType(data.user_type === 'farmer' ? 'farmer' : 'household');
    } catch {
      setProfileError('Your profile could not be loaded. Please try again.');
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadAchievements = useCallback(async () => {
    setAchievementsLoading(true);
    setAchievementsError('');
    try {
      const response = await profileService.getAchievements();
      const data = response?.data?.data?.achievements;
      if (!response?.data?.success || !Array.isArray(data)) throw new Error('Achievements are unavailable.');
      setAchievements(data.filter((item) => item && typeof item === 'object'));
    } catch {
      setAchievementsError('Achievements could not be loaded. Your profile information is still available.');
    } finally {
      setAchievementsLoading(false);
    }
  }, []);

  // Load profile and achievements independently so one failed request does not hide the other.
  // eslint-disable-next-line react/set-state-in-effect
  useEffect(() => { void loadProfile(); void loadAchievements(); }, [loadProfile, loadAchievements]);

  const handleSave = async (event) => {
    event.preventDefault();
    if (saveLock.current || !profile) return;
    saveLock.current = true;
    setSaveError('');
    setSaveSuccess(false);
    setSaving(true);
    try {
      const response = await profileService.updateProfile({ name: formName, user_type: formUserType });
      if (!response?.data?.success || !response.data.data?.profile) throw new Error('Profile could not be saved.');
      const updatedProfile = response.data.data.profile;
      setProfile((previous) => ({ ...previous, ...updatedProfile }));
      setFormName(updatedProfile.name || formName);
      setFormUserType(updatedProfile.user_type === 'farmer' ? 'farmer' : 'household');
      setSaveSuccess(true);
    } catch (error) {
      const details = error.response?.data?.error?.details;
      setSaveError((details && Object.values(details)[0]) || error.response?.data?.error?.message || 'Your changes could not be saved. Please try again.');
    } finally {
      saveLock.current = false;
      setSaving(false);
    }
  };

  const badges = Array.isArray(profile?.badges) ? profile.badges : [];
  const unlockedCount = achievements.filter((item) => item?.unlocked === true).length;
  const initials = (profile?.name || '').trim().split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
  const accountType = profile?.user_type === 'farmer' ? 'Farmer' : 'Household';

  return (
    <motion.main className="profile-page" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <header className="page-header profile-page-header">
        <div><span className="profile-eyebrow">YOUR AQUAWISE ACCOUNT</span><h1>Profile & progress</h1><p className="subtitle">Manage your details and see how your conservation practice is growing.</p></div>
      </header>

      <section className="profile-identity" aria-labelledby="profile-identity-heading">
        {profileLoading ? <LoadingState label="Loading your profile…" /> : profileError ? (
          <div className="profile-inline-error" role="alert"><Icon name="warning" size={20} /><span>{profileError}</span><button type="button" className="btn-secondary" onClick={loadProfile}>Try again</button></div>
        ) : (
          <>
            <div className="profile-avatar" aria-hidden="true">{initials || <Icon name="profile" size={30} />}</div>
            <div className="profile-identity-copy"><span className="profile-eyebrow">{accountType.toUpperCase()} ACCOUNT</span><h2 id="profile-identity-heading">{profile.name}</h2><p>{profile.email}</p></div>
            <span className="profile-type-label"><Icon name={profile.user_type === 'farmer' ? 'assessment' : 'water'} size={17} />{accountType}</span>
          </>
        )}
      </section>

      <section className="profile-settings-section" aria-labelledby="profile-settings-heading">
        <div className="profile-section-heading"><div><span className="profile-eyebrow">ACCOUNT DETAILS</span><h2 id="profile-settings-heading">Personal information</h2><p>Update the information associated with your AquaWise account.</p></div></div>
        {profile && !profileError && <form onSubmit={handleSave} className="profile-settings-card">
          <div className="profile-form-grid">
            <div className="form-group"><label htmlFor="prof-name">Display name</label><input id="prof-name" type="text" autoComplete="name" value={formName} onChange={(event) => { setFormName(event.target.value); setSaveSuccess(false); }} maxLength={100} required disabled={saving} /><span className="profile-field-note">This is the name shown on your account.</span></div>
            <div className="form-group"><label htmlFor="prof-email">Email address <span>Read only</span></label><input id="prof-email" type="email" value={profile.email || ''} readOnly aria-readonly="true" /><span className="profile-field-note">Email changes are not available here.</span></div>
            <div className="form-group profile-account-type-field"><label htmlFor="prof-type">Account type</label><select id="prof-type" value={formUserType} onChange={(event) => { setFormUserType(event.target.value); setSaveSuccess(false); }} disabled={saving}><option value="household">Household</option><option value="farmer">Farmer</option></select><span className="profile-field-note">Choose the profile that best describes your water use.</span></div>
          </div>
          <div className="profile-save-row">
            <div className="profile-save-feedback" aria-live="polite">{saveError && <span className="profile-save-error" role="alert"><Icon name="warning" size={17} />{saveError}</span>}{saveSuccess && <span className="profile-save-success" role="status"><span aria-hidden="true">✓</span> Your profile has been saved.</span>}</div>
            <button type="submit" className="btn-primary profile-save-button" disabled={saving || !formName.trim()}>{saving ? <><span className="spinner profile-button-spinner" />Saving changes…</> : 'Save changes'}</button>
          </div>
        </form>}
      </section>

      {!profileLoading && !profileError && <section className="profile-statistics-section" aria-labelledby="profile-statistics-heading">
        <div className="profile-section-heading"><div><span className="profile-eyebrow">YOUR CONSERVATION RECORD</span><h2 id="profile-statistics-heading">At a glance</h2></div></div>
        <div className="profile-stats">
          <article className="profile-stat"><span className="profile-stat-icon"><Icon name="assessment" size={19} /></span><span className="profile-stat-value">{profile.assessment_count ?? 0}</span><span className="profile-stat-label">Assessments completed</span></article>
          <article className="profile-stat"><span className="profile-stat-icon"><Icon name="trend" size={19} /></span><span className="profile-stat-value">{profile.streak?.current_streak ?? 0}<small> days</small></span><span className="profile-stat-label">Current streak</span></article>
          <article className="profile-stat"><span className="profile-stat-icon"><Icon name="calendar" size={19} /></span><span className="profile-stat-value">{profile.streak?.longest_streak ?? 0}<small> days</small></span><span className="profile-stat-label">Longest streak</span></article>
          <article className="profile-stat"><span className="profile-stat-icon"><Icon name="score" size={19} /></span><span className="profile-stat-value">{badges.length}</span><span className="profile-stat-label">Achievements earned</span></article>
        </div>
      </section>}

      <section className="achievements-section" aria-labelledby="achievements-heading">
        <div className="achievements-header"><div><span className="profile-eyebrow">MILESTONES</span><h2 id="achievements-heading">Achievements</h2><p>Recognition for the conservation habits you build over time.</p></div>{!achievementsLoading && !achievementsError && <span className="achievements-count">{unlockedCount} of {achievements.length} completed</span>}</div>
        {achievementsLoading ? <LoadingState label="Loading achievements…" /> : achievementsError ? (
          <div className="profile-achievement-error" role="alert"><Icon name="warning" size={20} /><div><h3>Achievements are temporarily unavailable</h3><p>{achievementsError}</p></div><button type="button" className="btn-secondary" onClick={loadAchievements}>Try again</button></div>
        ) : achievements.length === 0 ? (
          <div className="profile-achievement-empty"><span className="profile-empty-icon"><Icon name="score" size={23} /></span><div><h3>Your milestones start here</h3><p>Complete an assessment to begin building your AquaWise conservation record.</p></div><Link to="/assessment" className="btn-secondary">Start an assessment <Icon name="arrowRight" size={16} /></Link></div>
        ) : (
          <div className="achievements-list">{[...achievements].sort((a, b) => Number(b?.unlocked === true) - Number(a?.unlocked === true)).map((achievement, index) => <AchievementCard key={achievement.id ?? `${achievement.name || 'achievement'}-${index}`} achievement={achievement} index={index} />)}</div>
        )}
      </section>
    </motion.main>
  );
}

export default Profile;
