import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { recommendationService } from '../services/api';
import { motion } from 'framer-motion';

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
      // If no ID is passed, this could be handled by navigating to the dashboard
      // But we enforce an ID in the route definition for this page
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
    if (id) {
      fetchRecommendations(false);
    } else {
      // Fallback if accessed without ID
      navigate('/dashboard', { replace: true });
    }
  }, [id, navigate]);

  const handleEnhance = () => {
    fetchRecommendations(true);
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Generating personalized recommendations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <p>{error}</p>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button onClick={() => fetchRecommendations(false)} className="btn-primary">Retry</button>
          <Link to="/dashboard" className="btn-secondary" style={{ textDecoration: 'none', padding: '0.75rem 1.5rem', background: '#e2e8f0', color: '#1e293b', borderRadius: '8px', fontWeight: '500' }}>Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  const recommendations = data?.recommendations || [];

  return (
    <motion.div 
      className="recommendations-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="page-header" style={{ alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
            <Link to="/dashboard" style={{ color: 'var(--water-blue)', textDecoration: 'none', fontWeight: '500' }}>← Dashboard</Link>
          </div>
          <h2>Your Action Plan</h2>
          <p className="subtitle">
            Based on your recent assessment, here are steps you can take to save water.
          </p>
        </div>
        
        {!isEnhanced && recommendations.length > 0 && (
          <button 
            onClick={handleEnhance} 
            disabled={enhancing}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {enhancing ? (
              <>
                <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span>
                Enhancing with AI...
              </>
            ) : (
              <>
                <span>✨</span> Enhance with AI
              </>
            )}
          </button>
        )}
      </header>

      {recommendations.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h3>Great Job!</h3>
          <p>We don't have any specific recommendations right now. Keep up your efficient water usage!</p>
          <Link to="/dashboard" className="btn-primary">Return to Dashboard</Link>
        </div>
      ) : (
        <div className="recs-grid" style={{ display: 'grid', gap: '1.5rem', gridTemplateColumns: '1fr' }}>
          {recommendations.map((rec, index) => (
            <motion.div 
              key={index}
              className="metric-card"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              style={{ borderLeft: '4px solid var(--water-blue)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', color: 'var(--text-color)', marginBottom: '0.5rem' }}>{rec.title}</h3>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', background: '#f1f5f9', padding: '0.25rem 0.5rem', borderRadius: '4px', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                      {rec.category}
                    </span>
                    {rec.difficulty && (
                      <span style={{ fontSize: '0.75rem', background: '#f0fdf4', color: 'var(--conservation-green)', padding: '0.25rem 0.5rem', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '600' }}>
                        {rec.difficulty}
                      </span>
                    )}
                  </div>
                </div>
                {rec.potential_saving > 0 && (
                  <div style={{ textAlign: 'right', background: '#e0f2fe', padding: '0.75rem 1rem', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--water-blue)', fontWeight: '600', textTransform: 'uppercase' }}>Save up to</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--water-blue)' }}>{rec.potential_saving} <span style={{ fontSize: '1rem', fontWeight: '500' }}>L/day</span></div>
                  </div>
                )}
              </div>
              <p style={{ color: '#475569', lineHeight: '1.6', fontSize: '1rem' }}>{rec.description}</p>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default Recommendations;
