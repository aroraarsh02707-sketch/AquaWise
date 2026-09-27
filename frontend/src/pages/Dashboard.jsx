import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { dashboardService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';

const numberFormat = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 });
const shortDate = (value) => {
  if (!value) return '';
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) return value;
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(year, month - 1, day));
};

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.28, delay },
});

function TrendTooltip({ active, payload, label, metric }) {
  if (!active || !payload?.length) return null;
  const scoreMode = metric === 'score';
  const value = payload[0].value;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{shortDate(label)}</p>
      <p className="tooltip-row">
        <span className="tooltip-dot" />
        {scoreMode ? `${value} / 100` : `${numberFormat.format(value)} L/day`}
      </p>
    </div>
  );
}

function LoadingDashboard() {
  return (
    <div className="dashboard-loading-state" role="status" aria-live="polite">
      <span className="sr-only">Loading your water overview</span>
      <div className="dashboard-skeleton dashboard-skeleton-heading" />
      <div className="dashboard-skeleton dashboard-skeleton-hero" />
      <div className="dashboard-skeleton-grid">
        {Array.from({ length: 5 }, (_, index) => <div className="dashboard-skeleton dashboard-skeleton-metric" key={index} />)}
      </div>
      <div className="dashboard-skeleton dashboard-skeleton-chart" />
    </div>
  );
}

function MetricCard({ label, value, unit, icon, detail, delay }) {
  return (
    <motion.article className="dashboard-metric-card" {...fadeUp(delay)}>
      <div className="dashboard-metric-topline">
        <span className="dashboard-metric-icon"><Icon name={icon} size={18} /></span>
        <span className="dashboard-metric-label">{label}</span>
      </div>
      <p className="dashboard-metric-value">
        {value}
        {unit && <span>{unit}</span>}
      </p>
      {detail && <p className="dashboard-metric-detail">{detail}</p>}
    </motion.article>
  );
}

const Dashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [trends, setTrends] = useState([]);
  const [trendMetric, setTrendMetric] = useState('consumption');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [dashRes, trendsRes] = await Promise.all([
        dashboardService.getDashboard(),
        dashboardService.getTrends(),
      ]);
      if (!dashRes.data.success || !trendsRes.data.success) {
        throw new Error('Dashboard data was unavailable.');
      }
      setData(dashRes.data.data);
      setTrends(trendsRes.data.data.trends || []);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError('We couldn’t load your water overview. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const retryDashboardData = () => {
    setLoading(true);
    setError(null);
    fetchDashboardData();
  };

  if (loading) return <LoadingDashboard />;

  if (error) {
    return (
      <section className="dashboard-state-card dashboard-error-state" role="alert">
        <span className="dashboard-state-icon"><Icon name="water" size={23} /></span>
        <div>
          <h1>Your overview is temporarily unavailable</h1>
          <p>{error}</p>
        </div>
        <button type="button" onClick={retryDashboardData} className="btn-primary">Try again</button>
      </section>
    );
  }

  const hasData = Number(data?.assessment_count) > 0;
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there';
  const recommendations = data?.recommendations || [];
  const latestTrend = trends[trends.length - 1];

  return (
    <motion.div className="dashboard-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.24 }}>
      <header className="page-header dashboard-page-header">
        <div>
          <p className="dashboard-eyebrow">YOUR WATER AT A GLANCE</p>
          <h1>Good to see you, {firstName}</h1>
          <p className="subtitle">A clear view of your water use and the steps that can reduce it.</p>
        </div>
        <Link to="/assessment" className="btn-primary dashboard-assessment-cta">
          <Icon name="assessment" size={18} />
          {hasData ? 'New assessment' : 'Start assessment'}
          <Icon name="arrowRight" size={17} />
        </Link>
      </header>

      {!hasData ? (
        <motion.section className="dashboard-empty-state" {...fadeUp()}>
          <div className="dashboard-empty-mark"><Icon name="water" size={30} /></div>
          <p className="dashboard-eyebrow">A GOOD PLACE TO START</p>
          <h3>Your water picture starts here</h3>
          <p>Complete a short assessment to estimate your daily use, see where water goes, and get practical ways to save.</p>
          <Link to="/assessment" className="btn-primary">
            Complete your first assessment <Icon name="arrowRight" size={17} />
          </Link>
          <div className="dashboard-empty-notes">
            <span><Icon name="assessment" size={16} /> Household or farm use</span>
            <span><Icon name="recommendations" size={16} /> Personalised actions</span>
            <span><Icon name="trend" size={16} /> Progress over time</span>
          </div>
        </motion.section>
      ) : (
        <>
          <motion.section className="water-summary-card" {...fadeUp()} aria-label="Latest daily water use">
            <div className="water-summary-main">
              <div className="water-summary-heading">
                <span className="water-summary-icon"><Icon name="water" size={22} /></span>
                <p>Estimated daily water use</p>
              </div>
              <div className="water-summary-number">
                {numberFormat.format(data.latest_daily_consumption ?? 0)}
                <span>litres / day</span>
              </div>
              <p className="water-summary-note">
                {latestTrend?.date ? `From your latest assessment on ${shortDate(latestTrend.date)}.` : 'From your latest completed assessment.'}
              </p>
            </div>
            <div className="water-summary-aside">
              <p className="water-summary-aside-label">Largest use category</p>
              <p className="water-summary-category">{data.top_category || 'Not available'}</p>
              <p className="water-summary-aside-copy">Your highest-volume category is a useful place to begin making changes.</p>
            </div>
          </motion.section>

          <section className="dashboard-metrics-grid" aria-label="Water use and progress metrics">
            <MetricCard label="Weekly use" value={numberFormat.format(data.latest_weekly_consumption ?? 0)} unit="L" icon="water" detail="Estimated per week" delay={0.03} />
            <MetricCard label="Monthly use" value={numberFormat.format(data.latest_monthly_consumption ?? 0)} unit="L" icon="calendar" detail="Estimated per month" delay={0.06} />
            <MetricCard label="Water Saver Score" value={data.latest_water_saver_score ?? '—'} unit={data.latest_water_saver_score != null ? '/100' : ''} icon="score" detail="Based on your latest assessment" delay={0.09} />
            <MetricCard label="Current streak" value={data.current_streak ?? 0} unit="days" icon="trend" detail="Consecutive days active" delay={0.12} />
            <MetricCard label="Assessments" value={data.assessment_count ?? 0} unit="total" icon="assessment" detail="Your completed check-ins" delay={0.15} />
          </section>

          <div className="dashboard-content-grid">
            <motion.section className="dashboard-panel trend-panel" {...fadeUp(0.16)} aria-labelledby="trend-title">
              <div className="dashboard-panel-header">
                <div>
                  <p className="dashboard-eyebrow">YOUR HISTORY</p>
                  <h3 id="trend-title">Progress over time</h3>
                  <p className="dashboard-panel-subtitle">Compare your recorded water use or Water Saver Score.</p>
                </div>
                <div className="trend-switch" role="group" aria-label="Choose trend metric">
                  <button type="button" className={trendMetric === 'consumption' ? 'active' : ''} aria-pressed={trendMetric === 'consumption'} onClick={() => setTrendMetric('consumption')}>Water use</button>
                  <button type="button" className={trendMetric === 'score' ? 'active' : ''} aria-pressed={trendMetric === 'score'} onClick={() => setTrendMetric('score')}>Score</button>
                </div>
              </div>
              {trends.length ? (
                <div className="dashboard-chart" role="img" aria-label={trendMetric === 'score' ? 'Water Saver Score across assessments' : 'Daily water consumption across assessments'}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trends} margin={{ top: 12, right: 12, left: -16, bottom: 0 }}>
                      <defs>
                        <linearGradient id="waterTrendFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="var(--brand-teal-500)" stopOpacity={0.18} />
                          <stop offset="100%" stopColor="var(--brand-teal-500)" stopOpacity={0.015} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} stroke="var(--border-light)" strokeDasharray="3 5" />
                      <XAxis dataKey="date" axisLine={false} tickLine={false} tickMargin={12} minTickGap={28} tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }} tickFormatter={shortDate} />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        width={55}
                        tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }}
                        tickFormatter={(value) => numberFormat.format(value)}
                        domain={trendMetric === 'score' ? [0, 100] : ['auto', 'auto']}
                      />
                      <Tooltip content={<TrendTooltip metric={trendMetric} />} cursor={{ stroke: 'var(--brand-teal-400)', strokeDasharray: '4 4' }} />
                      <Area
                        type="monotone"
                        dataKey={trendMetric === 'score' ? 'water_saver_score' : 'daily_consumption'}
                        stroke="var(--brand-teal-500)"
                        strokeWidth={2.5}
                        fill="url(#waterTrendFill)"
                        activeDot={{ r: 5, fill: 'var(--bg-surface)', stroke: 'var(--brand-teal-500)', strokeWidth: 2 }}
                        dot={trends.length < 2 ? { r: 4, fill: 'var(--brand-teal-500)', strokeWidth: 0 } : false}
                        isAnimationActive={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="dashboard-chart-empty">
                  <Icon name="trend" size={22} />
                  <p>No trend points are available yet.</p>
                  <span>Your next assessment will appear here.</span>
                </div>
              )}
              {trends.length === 1 && <p className="trend-footnote">Complete another assessment to see how your water use changes over time.</p>}
            </motion.section>

            <motion.section className="dashboard-panel recommendations-panel" {...fadeUp(0.2)} aria-labelledby="recommendations-title">
              <div className="dashboard-panel-header recommendations-header">
                <div>
                  <p className="dashboard-eyebrow">PRACTICAL NEXT STEPS</p>
                  <h3 id="recommendations-title">Recommended for you</h3>
                </div>
                <Link to="/recommendations" className="view-all-link">All plans <Icon name="arrowRight" size={15} /></Link>
              </div>
              {recommendations.length ? (
                <div className="dashboard-recommendation-list">
                  {recommendations.slice(0, 3).map((rec, index) => (
                    <Link to="/recommendations" className="dashboard-recommendation" key={rec.id ?? `${rec.title}-${index}`}>
                      <span className="dashboard-recommendation-icon"><Icon name="water" size={18} /></span>
                      <span className="dashboard-recommendation-copy">
                        <span className="dashboard-recommendation-category">{rec.category || 'Water saving'}</span>
                        <strong>{rec.title}</strong>
                        <span className="dashboard-recommendation-description">{rec.description}</span>
                      </span>
                      {Number(rec.potential_saving) > 0 && (
                        <span className="dashboard-saving-value">{numberFormat.format(rec.potential_saving)}<small>L/day</small></span>
                      )}
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="dashboard-recommendation-empty">
                  <Icon name="recommendations" size={21} />
                  <p>No recommendations to show yet.</p>
                  <span>New actions will appear after your next assessment.</span>
                </div>
              )}
            </motion.section>
          </div>
        </>
      )}
    </motion.div>
  );
};

export default Dashboard;
