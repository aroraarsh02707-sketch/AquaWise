import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { recommendationService } from '../services/api';
import { motion } from 'framer-motion';

const difficultyClass = (d) => {
  if (!d) return 'tag-difficulty-easy';
  const lc = d.toLowerCase();
  if (lc === 'easy') return 'tag-difficulty-easy';
  if (lc === 'medium') return 'tag-difficulty-medium';
  return 'tag-difficulty-hard';
};

const Recommendations = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [enhancing, setEnhancing] = useState(false);
  const [isEnhanced, setIsEnhanced] = useState(false);

  const fetchRecommendations = async (enhance = false) => {
    if (enhance) setEnhancing(true);
    else setLoading(true);
    setError(null);
    try {
      const response = await recommendationService.getRecommendations(id, enhance);
      if (response.data.success) {
        setData(response.data.data);
        setIsEnhanced(response.data.data.enhanced);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load recommendations.');
    } finally {
      setLoading(false);
      setEnhancing(false);
    }
  };

  useEffect(() => {
    if (id) fetchRecommendations(false);
    else navigate('/dashboard', { replace: true });
  }, [id]);

  if (loading) return (
    <div className="page-loader">
      <div className="spinner" />
      <p>Generating your action plan…</p>
    </div>
  );

  if (error) return (
    <div className="state-error">
      <p>{error}</p>
      <div style={{ display: 'flex', gap: '0.75rem' }}>
        <button onClick={() => fetchRecommendations(false)} className="btn-primary">Retry</button>
        <Link to="/recommendations" className="btn-secondary">Back to History</Link>
      </div>
    </div>
  );

  const recommendations = data?.recommendations || [];

  return (
    <motion.div className="recommendations-page"
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
    >
      <header className="page-header">
        <div>
          <Link to="/recommendations" style={{ fontSize: '0.825rem', color: 'var(--text-muted)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem' }}>
            ← Back to History
          </Link>
          <h2>Your Action Plan</h2>
          <p className="subtitle">
            {recommendations.length} personalised recommendation{recommendations.length !== 1 ? 's' : ''} based on your assessment.
            {isEnhanced && <span style={{ color: 'var(--teal-600)', fontWeight: 600 }}> ✨ AI-enhanced</span>}
          </p>
        </div>

        {!isEnhanced && recommendations.length > 0 && (
          <button onClick={() => fetchRecommendations(true)} disabled={enhancing} className="btn-primary">
            {enhancing
              ? <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Enhancing…</>
              : '✨ Enhance with AI'}
          </button>
        )}
      </header>

      {recommendations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h3>Great Job!</h3>
          <p>Your water usage is already efficient — no specific recommendations at this time. Keep it up!</p>
          <Link to="/dashboard" className="btn-primary">Back to Dashboard</Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.125rem' }}>
          {recommendations.map((rec, index) => (
            <motion.div key={index} className="rec-full-card"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.07 }}
            >
              <div className="rec-header">
                <div>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{rec.title}</h3>
                  <div className="rec-tags">
                    <span className={`tag tag-category`}>{rec.category}</span>
                    {rec.difficulty && (
                      <span className={`tag ${difficultyClass(rec.difficulty)}`}>{rec.difficulty}</span>
                    )}
                  </div>
                </div>
                {rec.potential_saving > 0 && (
                  <div className="rec-saving-badge">
                    <span className="save-label">Save up to</span>
                    <span className="save-value">{rec.potential_saving}</span>
                    <span className="save-unit">litres/day</span>
                  </div>
                )}
              </div>
              <p className="rec-description">{rec.description}</p>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default Recommendations;
