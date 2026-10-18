import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import { PageHeading, SectionTitle, StatePanel } from '../components/PagePrimitives';
import { getScorePresentation } from '../assessmentTransparency';
import { createDonutSegments } from '../dashboardChart';

const fmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 });
const chartColors = ['#42C7D9', '#58C4A0', '#F0BD70', '#8BE3EC', '#5B8EAC', '#B5A4E8', '#76B89F'];

function Loading() {
  return <div className="page-loading" role="status"><span className="spinner" /><span>Gathering your latest water insights…</span><div className="loading-lines"><i /><i /><i /></div></div>;
}

function Metric({ variant, label, value, unit, icon, note, index, scoreInfo, assessmentId }) {
  const numericScore = variant === 'score' && Number.isFinite(Number(value)) ? Math.max(0, Math.min(100, Number(value))) : 0;
  const circumference = 2 * Math.PI * 24;
  return <article className={`metric-tile metric-tile--${variant} dashboard-reveal`} style={{ '--reveal-delay': `${120 + index * 75}ms` }}>
    <div className="metric-label"><span className="metric-icon"><Icon name={icon} size={18} /></span><span>{label}</span></div>
    <div className="metric-main">
      <p className="metric-value">{value}<small>{unit}</small></p>
      {variant === 'weekly' && <div className="metric-static-mark" aria-hidden="true"><Icon name="calendar" size={27} /><span>7 DAYS</span></div>}
      {variant === 'monthly' && <div className="metric-static-mark metric-static-mark--month" aria-hidden="true"><Icon name="water" size={27} /><span>MONTHLY</span></div>}
      {variant === 'score' && <div className="score-ring" role="img" aria-label={value === '—' ? 'Water Saver Score unavailable' : `${value} out of 100 Water Saver Score`}><svg viewBox="0 0 56 56"><circle className="score-ring-track" cx="28" cy="28" r="24" /><circle className="score-ring-value" cx="28" cy="28" r="24" style={{ strokeDasharray: circumference, strokeDashoffset: circumference * (1 - numericScore / 100) }} /></svg><Icon name="score" size={17} /></div>}
      {variant === 'streak' && <div className="streak-mark" aria-hidden="true"><Icon name="calendar" size={24} /><span>ACTIVE</span><i /></div>}
    </div>
    {variant === 'score' && scoreInfo ? <>
      <span className="metric-note">{scoreInfo.description}</span>
      {scoreInfo.scoreMethod && <span className="score-context-copy">{scoreInfo.scoreMethod}</span>}
      {scoreInfo.completenessNote && <span className="score-completeness-note">{scoreInfo.completenessNote}</span>}
      {scoreInfo.completenessCaveat && <span className="score-qualification">{scoreInfo.completenessCaveat}</span>}
      {scoreInfo.qualification && <span className="score-qualification">{scoreInfo.qualification}</span>}
      {assessmentId && <Link className="score-review-link" to={`/recommendations/${assessmentId}`}>Review assessment details <Icon name="arrowRight" size={13} /></Link>}
    </> : <span className="metric-note">{note}</span>}
  </article>;
}

function recommendationIcon(category = '') {
  const value = category.toLowerCase();
  if (/bath|shower|bathing/.test(value)) return 'shower';
  if (/toilet|flush/.test(value)) return 'toilet';
  if (/leak|repair/.test(value)) return 'leak';
  if (/kitchen|dish/.test(value)) return 'kitchen';
  if (/garden|irrigat|outdoor/.test(value)) return 'leaf';
  return 'water';
}

function RecommendationCard({ recommendation, index }) {
  const { category, priority, title, description, potential_saving: potentialSaving } = recommendation;
  const normalizedPriority = String(priority || '').toLowerCase();
  const hasPriority = ['high', 'medium', 'low'].includes(normalizedPriority);
  const label = hasPriority ? `${normalizedPriority} priority` : 'Suggested';
  return <Link to="/recommendations" className={`next-step dashboard-reveal${index === 0 ? ' next-step--lead' : ''}`} style={{ '--reveal-delay': `${480 + index * 70}ms` }}>
    <span className="next-step-icon"><Icon name={recommendationIcon(category)} size={20} /></span>
    <span className="next-step-copy"><span className="next-step-meta"><small>{category || 'Water saving'}</small><i className={`priority-badge priority-badge--${hasPriority ? normalizedPriority : 'neutral'}`}>{label}</i></span><strong>{title}</strong><span>{description}</span></span>
    <span className="next-step-action">{Number(potentialSaving) > 0 && <b>{fmt.format(potentialSaving)}<small> L/day</small></b>}<span>View action <Icon name="arrowRight" size={15} /></span></span>
  </Link>;
}

function WaterComposition({ categories, dailyTotal }) {
  const chartData = createDonutSegments(categories, chartColors);
  if (!chartData.length) {
    return <section className="surface-panel overview-composition dashboard-reveal">
      <SectionTitle eyebrow="LATEST ASSESSMENT" title="Your daily water profile" />
      <div className="overview-composition-empty"><Icon name="water" size={24} /><strong>Category details unavailable</strong><span>Your latest assessment does not contain category volumes yet.</span></div>
    </section>;
  }

  return <section className="surface-panel overview-composition dashboard-reveal">
    <SectionTitle eyebrow="LATEST ASSESSMENT" title="Your daily water profile" aside={<span className="composition-tag"><i /> ESTIMATED USE</span>} />
    <p className="overview-composition-intro">See how your latest estimated water use is distributed across categories.</p>
    <div className="overview-composition-body">
      <div className="overview-donut-wrap" role="img" aria-label="Doughnut chart of daily water use by category">
        <svg className="overview-donut-svg" viewBox="0 0 240 240" aria-hidden="true" focusable="false">
          <defs>
            <mask id="overview-donut-draw-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="240" height="240">
              <circle className="overview-donut-draw-mask-path" cx="120" cy="120" r="95" fill="none" />
            </mask>
          </defs>
          <circle className="overview-donut-track" cx="120" cy="120" r="95" fill="none" />
          <g className="overview-donut-segments" mask="url(#overview-donut-draw-mask)">
            {chartData.map((entry) => {
              const share = Number(entry.percentage);
              const shareLabel = Number.isFinite(share) ? ` · ${fmt.format(share)}%` : '';
              return <path key={entry.category} d={entry.path} fill={entry.color} stroke="#101F30" strokeWidth="3">
                <title>{`${entry.category}: ${fmt.format(entry.value)} L/day${shareLabel}`}</title>
              </path>;
            })}
          </g>
        </svg>
        <div className="overview-donut-center" aria-hidden="true">
          <span>DAILY TOTAL</span>
          <strong>{fmt.format(dailyTotal)}<small>L</small></strong>
          <span>latest estimate</span>
        </div>
      </div>
      <div className="overview-composition-legend">
        <div className="overview-legend-head"><span>USE CATEGORY</span><span>SHARE</span></div>
        <ul>{chartData.map((item) => <li key={item.category}>
          <span className="overview-legend-swatch" style={{ '--swatch': item.color }} />
          <span className="overview-legend-name">{item.category}<small>{fmt.format(item.value)} L/day</small></span>
          <strong>{fmt.format(Number(item.percentage) || 0)}%</strong>
        </li>)}</ul>
      </div>
    </div>
  </section>;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const response = await dashboardService.getDashboard();
      if (!response.data.success) throw new Error();
      setData(response.data.data);
      setError('');
    } catch {
      setError('Your water overview could not be loaded. Check your connection and retry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  if (loading) return <Loading />;
  if (error) return <StatePanel tone="error" title="Your overview is unavailable" description={error} icon="warning" action={<button className="button button-primary" onClick={() => { setLoading(true); load(); }}>Retry</button>} />;

  const hasData = Number(data?.assessment_count) > 0;
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there';
  const recs = data?.recommendations || [];
  const categories = (data?.category_breakdown || [])
    .filter((item) => Number(item.litres_per_day) > 0)
    .sort((a, b) => Number(b.litres_per_day) - Number(a.litres_per_day));

  return <div className="dashboard-page dashboard-reveal">
    <PageHeading eyebrow="WATER USE / OVERVIEW" title={`Your water, in focus, ${firstName}.`} description="A clear snapshot of your latest estimate and practical ways to conserve." action={<Link to="/assessment" className="button button-primary"><Icon name="assessment" size={17} />{hasData ? 'New assessment' : 'Start assessment'}<Icon name="arrowRight" size={16} /></Link>} />
    {!hasData ? <section className="welcome-feature">
      <div className="welcome-copy"><span className="eyebrow">YOUR BASELINE STARTS HERE</span><h2>Understand where your water goes.</h2><p>AquaWise turns a few details about your household into a useful water-use estimate and actions you can take next.</p><Link className="button button-primary" to="/assessment">Build your first water profile <Icon name="arrowRight" size={17} /></Link></div>
      <div className="water-orbit" aria-hidden="true"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><span className="orbit-center"><Icon name="water" size={36} /></span><b>Measure</b><b>Understand</b><b>Conserve</b></div>
    </section> : <>
      <WaterComposition categories={categories} dailyTotal={Number(data.latest_daily_consumption) || 0} />

      <section className="metrics-row" aria-label="Water use metrics">
        <Metric index={0} variant="weekly" label="Weekly estimate" value={fmt.format(data.latest_weekly_consumption ?? 0)} unit="L" icon="calendar" note="Based on your latest assessment" />
        <Metric index={1} variant="monthly" label="Monthly estimate" value={fmt.format(data.latest_monthly_consumption ?? 0)} unit="L" icon="water" note="Based on your latest assessment" />
        <Metric index={2} variant="score" label="Water Saver Score" value={data.latest_water_saver_score ?? '—'} unit={data.latest_water_saver_score != null ? '/100' : ''} icon="score" note="Your latest assessment score" scoreInfo={getScorePresentation(data.latest_assessment_type, data.latest_calculation)} assessmentId={data.latest_assessment_id} />
        <Metric index={3} variant="streak" label="Current streak" value={data.current_streak ?? 0} unit="days" icon="trend" note="Consecutive days active" />
      </section>

      <section className="surface-panel next-steps">
        <SectionTitle eyebrow="BASED ON YOUR PROFILE" title="Recommended next steps" aside={<Link className="text-link" to="/recommendations">Assessment history <Icon name="arrowRight" size={15} /></Link>} />
        {recs.length ? <div className="next-step-list">{recs.slice(0, 3).map((r, i) => <RecommendationCard recommendation={r} index={i} key={r.id ?? `${r.title}-${i}`} />)}</div> : <div className="inline-empty"><Icon name="recommendations" size={20} /><p>No recommendations to show yet. New actions appear after your next assessment.</p><Link to="/assessment">Complete an assessment</Link></div>}
      </section>
    </>}
  </div>;
}
