import React, { useState, useEffect } from 'react';
import { dashboardService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

const CARD_ICONS = {
  score: '🏅',
  usage: '💧',
  streak: '🔥',
  category: '📊',
};

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.35, delay },
});

const Dashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [dashRes, trendsRes] = await Promise.all([
          dashboardService.getDashboard(),
          dashboardService.getTrends()
        ]);
        if (dashRes.data.success)   setData(dashRes.data.data);
        if (trendsRes.data.success) setTrends(trendsRes.data.data.trends);
      } catch (err) {
        console.error('Dashboard fetch error:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) return (
    <div className="dashboard-loading">
      <div className="spinner" />
      <p>Loading your water stats…</p>
    </div>
  );

  if (error) return (
    <div className="state-error">
      <p>{error}</p>
      <button onClick={() => window.location.reload()} className="btn-primary" style={{ alignSelf: 'flex-start' }}>
        Retry
      </button>
    </div>
  );

  const hasData = data && data.assessment_count > 0;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-row">
            <span className="tooltip-dot" />
            {payload[0].value} L/day
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div className="dashboard-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      <header className="page-header">
        <div>
          <h2>Welcome back, {user?.name?.split(' ')[0]}! 👋</h2>
          <p className="subtitle">Here's your water conservation overview.</p>
        </div>
        {!hasData && (
          <Link to="/assessment" className="btn-primary">Take First Assessment →</Link>
        )}
      </header>

      {!hasData ? (
        <div className="empty-state">
          <div className="empty-icon">💧</div>
          <h3>No Data Yet</h3>
          <p>Complete your first water assessment to unlock your Water Saver Score, track trends, and get personalised recommendations.</p>
          <Link to="/assessment" className="btn-primary">Start Assessment →</Link>
        </div>
      ) : (
        <>
          <section className="metrics-grid">
            <motion.div className="metric-card highlight" {...fadeUp(0)}>
              <span className="metric-icon">{CARD_ICONS.score}</span>
              <div className="metric-label">Water Saver Score</div>
              <div className="metric-value">
                {data.latest_water_saver_score}
                <span className="unit">/100</span>
              </div>
            </motion.div>

            <motion.div className="metric-card" {...fadeUp(0.05)}>
              <span className="metric-icon">{CARD_ICONS.usage}</span>
              <div className="metric-label">Daily Usage</div>
              <div className="metric-value">
                {data.latest_daily_consumption}
                <span className="unit">L</span>
              </div>
            </motion.div>

            <motion.div className="metric-card" {...fadeUp(0.10)}>
              <span className="metric-icon">{CARD_ICONS.streak}</span>
              <div className="metric-label">Current Streak</div>
              <div className="metric-value">
                {data.current_streak}
                <span className="unit">days</span>
              </div>
            </motion.div>

            <motion.div className="metric-card" {...fadeUp(0.15)}>
              <span className="metric-icon">{CARD_ICONS.category}</span>
              <div className="metric-label">Top Water-Use Category</div>
              <span className="category-pill">{data.top_category || 'N/A'}</span>
            </motion.div>
          </section>

          <div className="dashboard-row">
            <motion.section className="dashboard-section" {...fadeUp(0.2)}>
              <div className="section-header">
                <h3>Consumption Trends</h3>
              </div>
              <div className="chart-container">
                {trends.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trends} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} dy={8} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--blue-200)', strokeWidth: 2 }} />
                      <Line
                        type="monotone" dataKey="daily_consumption"
                        stroke="var(--blue-500)" strokeWidth={2.5}
                        dot={{ r: 3.5, fill: 'var(--blue-500)', strokeWidth: 0 }}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                        animationDuration={1200}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="chart-empty">Need at least 2 assessments to show trends.</div>
                )}
              </div>
            </motion.section>

            <motion.section className="dashboard-section" {...fadeUp(0.25)}>
              <div className="section-header">
                <h3>Recommendations</h3>
                <Link to="/recommendations" className="view-all-link">View all →</Link>
              </div>
              <div className="recs-list">
                {data.recommendations && data.recommendations.length > 0 ? (
                  data.recommendations.slice(0, 3).map((rec, index) => (
                    <div key={index} className="rec-preview-card">
                      <div className="rec-icon-wrap">💡</div>
                      <div className="rec-content">
                        <h4>{rec.title}</h4>
                        <span className="rec-saving">Save ~{rec.potential_saving} L/day</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="no-recs">No recommendations available yet.</p>
                )}
              </div>
            </motion.section>
          </div>
        </>
      )}
    </motion.div>
  );
};

export default Dashboard;
