import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { assessmentService, recommendationService } from '../services/api';
import Icon from '../components/Icon';
import { PageHeading, StatePanel } from '../components/PagePrimitives';
import { getAssessmentQuality, getScorePresentation } from '../assessmentTransparency';

const formatDate = (value) => {
  if (!value) return null;
  const datePart = value.slice(0, 10);
  const [year, month, day] = datePart.split('-').map(Number);
  if (!year || !month || !day) return null;
  return new Intl.DateTimeFormat(undefined, { month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(year, month - 1, day));
};

const formatNumber = (value) => {
  if (value == null || value === '') return '—';
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString(undefined, { maximumFractionDigits: 1 }) : '—';
};

const priorityName = (priority) => {
  const normalized = String(priority || '').toLowerCase();
  return ['high', 'medium', 'low'].includes(normalized) ? normalized : null;
};

async function getPlanPageData(assessmentId) {
  const [recommendationResponse, assessmentResponse] = await Promise.all([
    recommendationService.getRecommendations(assessmentId),
    assessmentService.getAssessment(assessmentId).catch(() => null),
  ]);
  if (!recommendationResponse?.data?.success) throw new Error('Action plan unavailable.');

  const plan = recommendationResponse.data.data;
  if (!Array.isArray(plan?.recommendations)) throw new Error('Action plan unavailable.');

  return {
    plan,
    assessment: assessmentResponse?.data?.success ? assessmentResponse.data.data : null,
  };
}

function PlanLoading() {
  return (
    <div className="recommendation-plan-loading" role="status" aria-live="polite">
      <span className="sr-only">Loading your action plan</span>
      <div className="recommendation-skeleton-heading" />
      <div className="recommendation-skeleton-context" />
      <div className="recommendation-skeleton-row" />
      <div className="recommendation-skeleton-row" />
    </div>
  );
}

function AssessmentContext({ assessment }) {
  if (!assessment) return null;
  const scoreInfo = getScorePresentation(assessment.assessment_type, assessment.calculation);
  return (
    <section className="recommendation-assessment-context" aria-label="Assessment context">
      <div className="recommendation-context-date">
        <Icon name="assessment" size={18} />
        <span>
          <strong>{assessment.assessment_type === 'farmer' ? 'Farm' : 'Household'} assessment</strong>
          {formatDate(assessment.assessment_date) && <small>{formatDate(assessment.assessment_date)}</small>}
        </span>
      </div>
      <div className="recommendation-context-stat">
        <span>Estimated daily use</span>
        <strong>{formatNumber(assessment.daily_consumption)} <small>L/day</small></strong>
      </div>
      <div className="recommendation-context-stat">
        <span>Water Saver Score</span>
        <strong>{assessment.water_saver_score ?? '—'} <small>/100</small></strong>
        <small className="score-context-copy">{scoreInfo.description}</small>
        <small className="score-context-copy">{scoreInfo.scoreMethod}</small>
        {assessment.assessment_type === 'household' && scoreInfo.completenessNote && <small className="score-completeness-note">{scoreInfo.completenessNote}</small>}
        {assessment.assessment_type === 'household' && scoreInfo.completenessCaveat && <small className="score-qualification">{scoreInfo.completenessCaveat}</small>}
        {scoreInfo.qualification && <small className="score-qualification">{scoreInfo.qualification}</small>}
      </div>
    </section>
  );
}

function ResultOverview({ assessment }) {
  const result = assessment.calculation || {};
  const quality = getAssessmentQuality(result);
  const details = assessment.details || {};
  const people = Number(details.household_size) || 1;
  const daily = Number(assessment.daily_consumption) || 0;
  const perPerson = result.daily_per_person ?? (daily / people);
  const answers = details.extended_answers || {};
  const calculationInputs = [
    ["Household size", details.household_size, "people"],
    ["Showers per person per day", answers.showers_per_person_per_day, "showers"],
    ["Shower duration", answers.shower_duration_minutes, "min"],
    ["Known shower flow", answers.shower_flow_rate_lpm, "L/min"],
    ["Bucket baths per person per day", answers.bucket_baths_per_person_per_day, "baths"],
    ["Buckets per bath", answers.buckets_per_bath, "buckets"],
    ["Known bucket capacity", answers.bucket_capacity_litres, "L/bucket"],
    ["Toilet flushes per person per day", answers.toilet_flushes_per_person_per_day, "flushes"],
    ["Known toilet flush volume", answers.toilet_flush_volume_litres, "L/flush"],
    ["Bathroom tap time per person per day", answers.bathroom_tap_minutes_per_person_per_day, "min"],
    ["Known bathroom tap flow", answers.bathroom_tap_flow_rate_lpm, "L/min"],
    ["Kitchen tap time per day", answers.kitchen_tap_minutes_per_day, "min"],
    ["Known kitchen tap flow", answers.kitchen_tap_flow_rate_lpm, "L/min"],
    ["Dishwashing tap time per day", answers.dishwashing_tap_minutes_per_day, "min"],
    ["Dishwashing volume per day", answers.dishwashing_litres_per_day, "L/day"],
    ["Dishwasher cycles per week", answers.dishwasher_cycles_per_week, "cycles"],
    ["Known dishwasher volume per cycle", answers.dishwasher_litres_per_cycle, "L/cycle"],
    ["Laundry loads per week", answers.laundry_loads_per_week, "loads"],
    ["Known laundry volume per load", answers.laundry_litres_per_load, "L/load"],
    ["Hand-wash volume per load", answers.handwash_litres_per_load, "L/load"],
    ["Hand-wash buckets per load", answers.handwash_buckets_per_load, "buckets"],
    ["Cleaning sessions per week", answers.cleaning_sessions_per_week, "sessions"],
    ["Cleaning minutes per session", answers.cleaning_minutes_per_session, "min"],
    ["Known cleaning flow", answers.cleaning_flow_rate_lpm, "L/min"],
    ["Cleaning volume per session", answers.cleaning_litres_per_session, "L/session"],
    ["Garden sessions per week", answers.garden_sessions_per_week, "sessions"],
    ["Garden minutes per session", answers.garden_minutes_per_session, "min"],
    ["Known garden flow", answers.garden_flow_rate_lpm, "L/min"],
    ["Garden volume per session", answers.garden_litres_per_session, "L/session"],
  ].filter(([, value]) => value !== undefined && value !== null && value !== "");
  return (
    <section className="results-overview" aria-label="Assessment results">
      <div className="results-summary"><span className="eyebrow">ESTIMATED HOUSEHOLD WATER USE</span><p className="results-primary-number">{formatNumber(daily)}<small> L/day</small></p><span className="results-summary-note">Estimated from your answers; actual use varies by fixtures and behavior.</span><div className="results-stat-row"><div><span>PER PERSON / DAY</span><strong>{formatNumber(perPerson)} <small>L</small></strong></div><div><span>PER WEEK</span><strong>{formatNumber(assessment.weekly_consumption)} <small>L</small></strong></div><div><span>PER 30 DAYS</span><strong>{formatNumber(assessment.monthly_consumption)} <small>L</small></strong></div></div>{result.calculation_version === 2 && <div className="results-source-split"><div><span>FROM ENTERED VALUES</span><strong>{formatNumber(result.user_input_litres_per_day)} <small>L/day</small></strong><em>{result.user_input_categories} categories</em></div><div><span>FROM CONFIGURED ESTIMATES</span><strong>{formatNumber(result.assumption_litres_per_day)} <small>L/day</small></strong><em>{result.assumption_categories} categories</em></div></div>}{result.calculation_version === 2 && <p className="results-source-note">Entered values are supplied by you and are not necessarily meter-measured. Configured estimates are disclosed below.</p>}{result.mixed_categories > 0 && <p className="results-source-note">{result.mixed_categories} {result.mixed_categories === 1 ? 'category combines' : 'categories combine'} entered values with configured estimates; the litre totals above separate those contributions.</p>}</div>
      {result.calculation_version === 2 && <section className={`results-quality-banner${quality.incomplete ? ' is-incomplete' : ''}`} aria-label="Assessment completeness">
        <div><span className="eyebrow">{quality.status}</span><p>{quality.explanation}</p>
          {quality.missingCategories.length > 0 && <p className="results-missing-categories"><strong>Unavailable or incomplete:</strong> {quality.missingCategories.join(', ')}.</p>}
          {result.assumptions?.length > 0 && <p className="results-source-note">Configured estimates were used in {result.assumption_categories ?? 0} categories. See “Assumptions & confidence” for each default.</p>}
        </div>
        <Link className="button button-quiet" to={`/assessment?edit=${assessment.id}`}>Review inputs <Icon name="arrowRight" size={15}/></Link>
      </section>}
      {result.calculation_version === 2 && calculationInputs.length > 0 && <details className="category-calculation-details"><summary>Inputs used in this estimate <span>{calculationInputs.length} values</span></summary><ul>{calculationInputs.map(([label, value, unit]) => <li key={label}><span>{label}</span><strong>{formatNumber(value)} <small>{unit}</small></strong></li>)}</ul><p>Per-person activities are scaled by household size. Weekly activities are averaged over seven days. When an active category needs a missing fixture rate, the configured value is disclosed below.</p></details>}
      {result.calculation_version === 2 && result.breakdown?.length > 0 && <details className="category-calculation-details"><summary>Daily category breakdown <span>{result.breakdown.length} categories</span></summary><ul>{result.breakdown.map((item) => { const source = result.category_sources?.[item.category]; const sourceLabel = source === 'assumption' ? 'Configured estimate' : source === 'mixed' ? 'Provided + estimated' : 'Provided values'; return <li key={item.category}><span>{item.category}<small>{sourceLabel}</small></span><strong>{formatNumber(item.litres_per_day)} <small>L/day</small></strong><em>{formatNumber(item.percentage)}%</em></li>; })}</ul><p>Weekly projection = daily estimate × 7. Monthly projection = daily estimate × 30 days. The disclosed fixture and appliance rates appear below.</p></details>}
      {result.assumptions?.length > 0 && <details className="assumptions-details"><summary>Assumptions & confidence <span>{result.estimate_kind === 'rough' ? 'Rough estimate' : 'Input-based estimate'}</span></summary><p>{result.assumption_disclaimer}</p>{result.incomplete_categories?.length > 0 && <p className="results-partial-note">Known values are included, but these categories are incomplete: {result.incomplete_categories.join(', ')}.</p>}<ul>{result.assumptions.map((item,index)=><li key={`${item}-${index}`}>{item}</li>)}</ul></details>}
      {result.calculation_version === 2 && !result.assumptions?.length && <details className="assumptions-details"><summary>Assumptions & confidence <span>{result.estimate_kind || 'Input-based estimate'}</span></summary><p>{result.assumption_disclaimer}</p>{result.incomplete_categories?.length > 0 && <p className="results-partial-note">Known values are included, but these categories are incomplete: {result.incomplete_categories.join(', ')}.</p>}</details>}
    </section>
  );
}

function RecommendationCard({ recommendation, index }) {
  const priority = priorityName(recommendation.priority);
  const saving = Number(recommendation.potential_saving);
  const hasSaving = Number.isFinite(saving) && saving > 0;

  return (
    <motion.article
      className={`recommendation-action-card ${priority ? `priority-${priority}` : ''}`}
      initial={{ opacity: 0, y: 7 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: Math.min(index * 0.045, 0.22) }}
    >
      <span className="action-index">{String(index + 1).padStart(2, '0')}</span>
      <div className="recommendation-action-main">
        <div className="recommendation-action-topline"><span className="recommendation-category-label">{recommendation.category || 'Water conservation'}</span>{priority && <span className={`recommendation-priority priority-label-${priority}`}>{priority} priority</span>}</div>
        <h3>{recommendation.title || 'Water-saving action'}</h3>
        <div className="recommendation-why"><h4>Why it matters</h4><p>{recommendation.description || 'AquaWise has not provided further details for this action.'}</p></div>
      </div>
      <aside className="recommendation-savings-panel" aria-label="Estimated potential water savings">
        <span className="recommendation-savings-icon"><Icon name="water" size={19} /></span>
        <span className="recommendation-savings-label">POTENTIAL SAVING</span>
          {hasSaving && (!recommendation.evidence || recommendation.evidence.saving_basis) ? (
          <>
            <strong>{formatNumber(saving)} <small>L/day</small></strong>
            <span className="recommendation-savings-footnote">AquaWise estimate</span>
          </>
          ) : (
          <span className="recommendation-saving-unavailable">No estimate available</span>
        )}
      </aside>
    </motion.article>
  );
}

const Recommendations = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!id) {
      navigate('/recommendations', { replace: true });
      return undefined;
    }

    let current = true;
    const loadPlan = async () => {
      try {
        const pageData = await getPlanPageData(id);
        if (current) {
          setData(pageData);
        }
      } catch {
        if (current) setError(true);
      } finally {
        if (current) setLoading(false);
      }
    };
    loadPlan();
    return () => { current = false; };
  }, [id, navigate]);

  const retry = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const pageData = await getPlanPageData(id);
      setData(pageData);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [id]);

  if (loading) return <PlanLoading />;

  if (error || !data) {
    return <div className="plan-error-page"><StatePanel tone="error" title="This action plan isn’t available" description="It may have been removed or temporarily unavailable. You can retry or choose another assessment." icon="warning" action={<><button type="button" onClick={retry} className="button button-primary">Try again</button><Link to="/recommendations" className="button button-quiet">All plans</Link></>}/></div>;
  }

  const { plan, assessment } = data;
  const recommendations = plan.recommendations;

  return (
    <motion.div className="recommendations-page rebuilt-page" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      <PageHeading eyebrow="WATER USE / ACTION PLAN" title="Your conservation plan." description="Prioritized actions based on the information in your assessment." meta={<span className="plan-count">{plan.count ?? recommendations.length}<small> actions</small></span>} action={<Link to="/recommendations" className="quiet-link"><Icon name="arrowLeft" size={16}/> All plans</Link>} />
      <AssessmentContext assessment={assessment} />
      {assessment && assessment.assessment_type === 'household' && assessment.calculation?.calculation_version === 2 && <ResultOverview assessment={assessment} />}
      {recommendations.length === 0 ? <section className="plans-empty compact-empty"><span className="eyebrow">NO ACTIONS IN THIS PLAN</span><h2>No recommendations were returned.</h2><p>This assessment has no saved recommendations to display. Review another plan or complete a new assessment.</p><div className="recommendation-empty-actions"><Link to="/assessment" className="button button-primary">New assessment <Icon name="arrowRight" size={16}/></Link><Link to="/recommendations" className="button button-quiet">View other plans</Link></div></section> : <>
          <div className="action-plan-intro"><div><span className="eyebrow">PRIORITIZED FOR YOUR WATER USE</span><h2>Start with the biggest opportunity.</h2></div><p>Potential savings are illustrative scenarios where shown. Leak actions do not include an assumed leak volume.</p></div>
          {recommendations.some((item) => item.category === 'Leaks') && <section className="urgent-actions"><span className="eyebrow">ATTENTION FIRST</span><h2>Inspect reported leaks</h2><div className="recommendation-actions-list">{recommendations.map((recommendation,index)=>recommendation.category==='Leaks' ? <RecommendationCard recommendation={recommendation} index={index} key={recommendation.id ?? `leak-${index}`}/> : null)}</div></section>}
          <div className="recommendation-actions-list">{recommendations.filter((item)=>item.category!=='Leaks').map((recommendation, index) => <RecommendationCard recommendation={recommendation} index={index} key={recommendation.id ?? `${recommendation.title}-${index}`}/>)}</div>
          {assessment?.assessment_type === 'household' && <div className="results-management"><div><span className="eyebrow">CHANGE YOUR INPUTS</span><p>Review or adjust your answers, then calculate a new assessment. Your previous assessment remains in your history.</p></div><Link className="button button-quiet" to={`/assessment?edit=${id}`}>Review answers <Icon name="arrowRight" size={15}/></Link></div>}
        </>}
    </motion.div>
  );
};

export default Recommendations;
