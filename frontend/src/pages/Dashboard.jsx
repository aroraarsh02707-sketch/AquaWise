import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip as ChartTooltip } from 'recharts';
import { dashboardService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import Icon from '../components/Icon';
import { PageHeading, SectionTitle, StatePanel } from '../components/PagePrimitives';

const fmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 });
const chartColors = ['#42C7D9', '#58C4A0', '#F0BD70', '#8BE3EC', '#5B8EAC', '#B5A4E8', '#76B89F'];
const appear = { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25 } };

function Loading() {
  return <div className="page-loading" role="status"><span className="spinner" /><span>Gathering your latest water insights…</span><div className="loading-lines"><i /><i /><i /></div></div>;
}

function Metric({ label, value, unit, icon, note }) {
  return <article className="metric-tile">
    <div className="metric-label"><span className="metric-icon"><Icon name={icon} size={17} /></span>{label}</div>
    <p className="metric-value">{value}<small>{unit}</small></p>
    <span className="metric-note">{note}</span>
  </article>;
}

function WaterComposition({ categories, dailyTotal }) {
  const chartData = categories.map((item) => ({ ...item, value: Number(item.litres_per_day) || 0 }));
  if (!chartData.length) {
    return <section className="surface-panel overview-composition">
      <SectionTitle eyebrow="LATEST ASSESSMENT" title="Your daily water profile" />
      <div className="overview-composition-empty"><Icon name="water" size={24} /><strong>Category details unavailable</strong><span>Your latest assessment does not contain category volumes yet.</span></div>
    </section>;
  }

  return <section className="surface-panel overview-composition">
    <SectionTitle eyebrow="LATEST ASSESSMENT" title="Your daily water profile" aside={<span className="composition-tag"><i /> ESTIMATED USE</span>} />
    <p className="overview-composition-intro">See how your latest estimated water use is distributed across categories.</p>
    <div className="overview-composition-body">
      <div className="overview-donut-wrap" role="img" aria-label="Doughnut chart of daily water use by category">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={chartData} dataKey="value" nameKey="category" innerRadius="68%" outerRadius="91%" paddingAngle={3} cornerRadius={5} stroke="#101F30" strokeWidth={3} isAnimationActive={false}>
              {chartData.map((entry, index) => <Cell key={entry.category} fill={chartColors[index % chartColors.length]} />)}
            </Pie>
            <ChartTooltip formatter={(value, name, item) => { const share = Number(item?.payload?.percentage); const detail = Number.isFinite(share) ? ` · ${fmt.format(share)}%` : ''; return [`${fmt.format(Number(value))} L/day${detail}`, name]; }} contentStyle={{ background: '#08121F', border: '1px solid #315064', borderRadius: 9, color: '#E5EEF4', fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
        <div className="overview-donut-center" aria-hidden="true">
          <span>DAILY TOTAL</span>
          <strong>{fmt.format(dailyTotal)}<small>L</small></strong>
          <span>latest estimate</span>
        </div>
      </div>
      <div className="overview-composition-legend">
        <div className="overview-legend-head"><span>USE CATEGORY</span><span>SHARE</span></div>
        <ul>{chartData.map((item, index) => <li key={item.category}>
          <span className="overview-legend-swatch" style={{ '--swatch': chartColors[index % chartColors.length] }} />
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

  return <motion.div className="dashboard-page" {...appear}>
    <PageHeading eyebrow="WATER USE / OVERVIEW" title={`Your water, in focus, ${firstName}.`} description="A clear snapshot of your latest estimate and practical ways to conserve." action={<Link to="/assessment" className="button button-primary"><Icon name="assessment" size={17} />{hasData ? 'New assessment' : 'Start assessment'}<Icon name="arrowRight" size={16} /></Link>} />
    {!hasData ? <section className="welcome-feature">
      <div className="welcome-copy"><span className="eyebrow">YOUR BASELINE STARTS HERE</span><h2>Understand where your water goes.</h2><p>AquaWise turns a few details about your household or farm into a useful water-use estimate and actions you can take next.</p><Link className="button button-primary" to="/assessment">Build your first water profile <Icon name="arrowRight" size={17} /></Link></div>
      <div className="water-orbit" aria-hidden="true"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><span className="orbit-center"><Icon name="water" size={36} /></span><b>Measure</b><b>Understand</b><b>Conserve</b></div>
    </section> : <>
      <WaterComposition categories={categories} dailyTotal={Number(data.latest_daily_consumption) || 0} />

      <section className="metrics-row" aria-label="Water use metrics">
        <Metric label="Weekly estimate" value={fmt.format(data.latest_weekly_consumption ?? 0)} unit="L" icon="calendar" note="At your latest usage rate" />
        <Metric label="Monthly estimate" value={fmt.format(data.latest_monthly_consumption ?? 0)} unit="L" icon="water" note="At your latest usage rate" />
        <Metric label="Water Saver Score" value={data.latest_water_saver_score ?? '—'} unit={data.latest_water_saver_score != null ? '/100' : ''} icon="score" note="From your latest assessment" />
        <Metric label="Current streak" value={data.current_streak ?? 0} unit="days" icon="trend" note="Consecutive days active" />
      </section>

      <section className="surface-panel next-steps">
        <SectionTitle eyebrow="BASED ON YOUR PROFILE" title="Recommended next steps" aside={<Link className="text-link" to="/recommendations">Assessment history <Icon name="arrowRight" size={15} /></Link>} />
        {recs.length ? <div className="next-step-list">{recs.slice(0, 3).map((r, i) => <Link to="/recommendations" className="next-step" key={r.id ?? `${r.title}-${i}`}><span className="next-step-number">0{i + 1}</span><span className="next-step-copy"><small>{r.category || 'Water saving'}</small><strong>{r.title}</strong><span>{r.description}</span></span>{Number(r.potential_saving) > 0 && <b>{fmt.format(r.potential_saving)}<small> L/day</small></b>}</Link>)}</div> : <div className="inline-empty"><Icon name="recommendations" size={20} /><p>No recommendations to show yet. New actions appear after your next assessment.</p><Link to="/assessment">Complete an assessment</Link></div>}
      </section>
    </>}
  </motion.div>;
}
