import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { assessmentService } from '../services/api';
import Icon from '../components/Icon';

const formatDate = (value) => {
  if (!value) return 'Date unavailable';
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) return value;
  return new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(year, month - 1, day));
};

const formatNumber = (value) => {
  if (value == null || value === '') return '—';
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—';
};

function HistoryLoading() {
  return (
    <div className="recommendation-history-loading" role="status" aria-live="polite">
      <span className="sr-only">Loading your assessment history</span>
      <div className="recommendation-skeleton-heading" />
      {Array.from({ length: 3 }, (_, index) => <div className="recommendation-skeleton-row" key={index} />)}
    </div>
  );
}

const RecommendationsIndex = () => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let current = true;
    const loadAssessments = async () => {
      try {
        const response = await assessmentService.getAssessments();
        if (!response?.data?.success || !Array.isArray(response.data.data?.assessments)) {
          throw new Error('Assessment history is unavailable.');
        }
        if (current) setAssessments(response.data.data.assessments);
      } catch {
        if (current) setError(true);
      } finally {
        if (current) setLoading(false);
      }
    };
    loadAssessments();
    return () => { current = false; };
  }, []);

  const retry = async () => {
    setLoading(true);
    setError(false);
    try {
      const response = await assessmentService.getAssessments();
      if (!response?.data?.success || !Array.isArray(response.data.data?.assessments)) {
        throw new Error('Assessment history is unavailable.');
      }
      setAssessments(response.data.data.assessments);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <HistoryLoading />;

  if (error) {
    return (
      <section className="recommendation-state-card" role="alert">
        <span className="recommendation-state-icon"><Icon name="warning" size={22} /></span>
        <div>
          <h2>We couldn’t load your action plans</h2>
          <p>Your assessment history is still safe. Try loading it again.</p>
        </div>
        <button type="button" onClick={retry} className="btn-primary">Try again</button>
      </section>
    );
  }

  return (
    <motion.div className="recommendations-index-page" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      <header className="page-header recommendations-page-header">
        <div>
          <p className="recommendations-eyebrow">YOUR CONSERVATION PLAN</p>
          <h2>Action plans</h2>
          <p className="subtitle">Open an assessment to review the practical water-saving actions created from it.</p>
        </div>
        <Link to="/assessment" className="btn-primary recommendations-new-assessment">
          <Icon name="assessment" size={17} /> New assessment
        </Link>
      </header>

      {assessments.length === 0 ? (
        <section className="recommendations-empty-state">
          <span className="recommendations-empty-icon"><Icon name="recommendations" size={28} /></span>
          <p className="recommendations-eyebrow">START WITH YOUR WATER USE</p>
          <h3>Your action plans will appear here</h3>
          <p>Complete a household or farm assessment to receive practical steps based on your water-use information.</p>
          <Link to="/assessment" className="btn-primary">Start an assessment <Icon name="arrowRight" size={17} /></Link>
        </section>
      ) : (
        <section className="recommendation-history-section" aria-labelledby="recommendation-history-title">
          <div className="recommendation-history-heading">
            <div>
              <h3 id="recommendation-history-title">Recent assessments</h3>
              <p>Each assessment has a corresponding action plan.</p>
            </div>
            <span>{assessments.length} {assessments.length === 1 ? 'assessment' : 'assessments'}</span>
          </div>
          <div className="recommendation-history-list">
            {assessments.map((assessment, index) => (
              <motion.article
                className="recommendation-history-card"
                key={assessment.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: Math.min(index * 0.035, 0.21) }}
              >
                <Link
                  to={`/recommendations/${assessment.id}`}
                  className="recommendation-history-link"
                  aria-label={`Open action plan from ${formatDate(assessment.assessment_date)}`}
                >
                  <span className="recommendation-history-leading-icon"><Icon name="water" size={20} /></span>
                  <span className="recommendation-history-main">
                    <span className="recommendation-history-date">{formatDate(assessment.assessment_date)}</span>
                    <span className="recommendation-history-context">{assessment.assessment_type === 'farmer' ? 'Farm' : 'Household'} assessment</span>
                  </span>
                  <span className="recommendation-history-metric">
                    <span>Daily use</span>
                    <strong>{formatNumber(assessment.daily_consumption)} <small>L/day</small></strong>
                  </span>
                  <span className="recommendation-history-metric score">
                    <span>Water Saver Score</span>
                    <strong>{assessment.water_saver_score ?? '—'} <small>/100</small></strong>
                  </span>
                  <span className="recommendation-history-open">Open plan <Icon name="arrowRight" size={17} /></span>
                </Link>
              </motion.article>
            ))}
          </div>
        </section>
      )}
    </motion.div>
  );
};

export default RecommendationsIndex;
