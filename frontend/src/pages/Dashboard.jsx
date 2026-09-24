import React, { useState, useEffect } from 'react';
import { dashboardService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

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
        
        if (dashRes.data.success) {
          setData(dashRes.data.data);
        }
        if (trendsRes.data.success) {
          setTrends(trendsRes.data.data.trends);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading your water stats...</p>
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

  const hasData = data && data.assessment_count > 0;

  // Custom Tooltip for the chart
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-date">{label}</p>
          <p className="tooltip-value">
            <span className="tooltip-indicator"></span>
            {payload[0].value} L/day
          </p>
          {payload[1] && (
            <p className="tooltip-score">Score: {payload[1].value}/100</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <motion.div 
      className="dashboard-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="page-header">
        <div>
          <h2>Welcome back, {user?.name.split(' ')[0]}!</h2>
          <p className="subtitle">Here's your water conservation overview.</p>
        </div>
        {!hasData && (
          <Link to="/assessment" className="btn-primary">Take First Assessment</Link>
        )}
      </header>

      {!hasData ? (
        <div className="empty-state">
          <div className="empty-icon">💧</div>
          <h3>No Data Yet</h3>
          <p>Complete your first water assessment to unlock insights, track your trends, and get personalized recommendations.</p>
          <Link to="/assessment" className="btn-primary">Start Assessment</Link>
        </div>
      ) : (
        <>
          {/* Key Metrics Grid */}
          <section className="metrics-grid">
            <div className="metric-card highlight">
              <div className="metric-label">Water Saver Score</div>
              <div className="metric-value">{data.latest_water_saver_score}<span>/100</span></div>
            </div>
            
            <div className="metric-card">
              <div className="metric-label">Latest Daily Usage</div>
              <div className="metric-value">{data.latest_daily_consumption} <span>L</span></div>
            </div>
            
            <div className="metric-card">
              <div className="metric-label">Current Streak</div>
              <div className="metric-value">{data.current_streak} <span>days</span></div>
            </div>
            
            <div className="metric-card">
              <div className="metric-label">Top Category</div>
              <div className="metric-value category-value">{data.top_category || 'N/A'}</div>
            </div>
          </section>

          <div className="dashboard-row">
            {/* Trends Chart */}
            <section className="dashboard-section chart-section">
              <div className="section-header">
                <h3>Consumption Trends</h3>
              </div>
              <div className="chart-container">
                {trends.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis 
                        dataKey="date" 
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#64748b', fontSize: 12 }} 
                        dy={10}
                      />
                      <YAxis 
                        yAxisId="left"
                        axisLine={false} 
                        tickLine={false} 
                        tick={{ fill: '#64748b', fontSize: 12 }} 
                      />
                      <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#e0f2fe', strokeWidth: 2 }} />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="daily_consumption" 
                        stroke="#0ea5e9" 
                        strokeWidth={3}
                        dot={{ r: 4, fill: '#0ea5e9', strokeWidth: 0 }}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                        animationDuration={1500}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="chart-empty">Not enough data to show trends.</div>
                )}
              </div>
            </section>

            {/* Recommendations Preview */}
            <section className="dashboard-section recs-section">
              <div className="section-header">
                <h3>Recent Recommendations</h3>
                <Link to="/recommendations" className="view-all-link">View All</Link>
              </div>
              <div className="recs-list">
                {data.recommendations && data.recommendations.length > 0 ? (
                  data.recommendations.slice(0, 3).map((rec, index) => (
                    <div key={index} className="rec-preview-card">
                      <div className="rec-icon">💡</div>
                      <div className="rec-content">
                        <h4>{rec.title}</h4>
                        <span className="rec-saving">Save ~{rec.potential_saving} L/day</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="no-recs">No recommendations available at this time.</p>
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </motion.div>
  );
};

export default Dashboard;
