import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { assessmentService } from '../services/api';
import { motion } from 'framer-motion';

const RecommendationsIndex = () => {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        const response = await assessmentService.getAssessments();
        if (response.data.success) {
          setAssessments(response.data.data.assessments);
        }
      } catch {
        setError('Failed to load assessment history.');
      } finally {
        setLoading(false);
      }
    };
    fetchAssessments();
  }, []);

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" />
      <p>Loading your history…</p>
    </div>
  );

  if (error) return (
    <div className="state-error">
      <p>{error}</p>
      <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
    </div>
  );

  return (
    <motion.div className="recommendations-index-page"
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
    >
      <header className="page-header">
        <div>
          <h2>Recommendation History</h2>
          <p className="subtitle">Select an assessment to view its personalised action plan.</p>
        </div>
        <Link to="/assessment" className="btn-primary">+ New Assessment</Link>
      </header>

      {assessments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>No Assessments Yet</h3>
          <p>Complete your first water usage assessment to generate recommendations.</p>
          <Link to="/assessment" className="btn-primary">Take Assessment</Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          {assessments.map((a, i) => (
            <motion.div key={a.id} className="history-card"
              initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
            >
              <div className="history-card-info">
                <h4>Assessment — {a.assessment_date}</h4>
                <div className="history-card-meta">
                  <span className="score-pill">🏅 {a.water_saver_score}/100</span>
                  <span className="history-meta-item">Daily: <strong>{a.daily_consumption} L</strong></span>
                  <span className="history-meta-item">Type: <strong style={{ textTransform: 'capitalize' }}>{a.assessment_type}</strong></span>
                </div>
              </div>
              <Link to={`/recommendations/${a.id}`} className="btn-primary" style={{ padding: '0.55rem 1.1rem', fontSize: '0.875rem' }}>
                View Plan →
              </Link>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default RecommendationsIndex;
