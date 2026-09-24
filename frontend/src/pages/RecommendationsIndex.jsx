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
      } catch (err) {
        setError('Failed to load assessment history.');
      } finally {
        setLoading(false);
      }
    };
    fetchAssessments();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading your history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <p>{error}</p>
        <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
      </div>
    );
  }

  return (
    <motion.div 
      className="recommendations-index-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="page-header">
        <div>
          <h2>Recommendation History</h2>
          <p className="subtitle">Select an assessment to view its personalized action plan.</p>
        </div>
        <Link to="/assessment" className="btn-primary">New Assessment</Link>
      </header>

      {assessments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>No Assessments Found</h3>
          <p>Complete a water usage assessment to generate recommendations.</p>
          <Link to="/assessment" className="btn-primary">Take Assessment</Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {assessments.map((a) => (
            <div key={a.id} className="metric-card" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-color)' }}>Assessment on {a.assessment_date}</h4>
                <div style={{ color: '#64748b', fontSize: '0.875rem' }}>
                  Score: <strong style={{ color: 'var(--water-blue)' }}>{a.water_saver_score}</strong> | Daily Usage: {a.daily_consumption}L
                </div>
              </div>
              <Link to={`/recommendations/${a.id}`} className="btn-primary" style={{ padding: '0.5rem 1rem' }}>
                View Plan
              </Link>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default RecommendationsIndex;
