import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { assessmentService, recommendationService } from '../services/api';
import Icon from '../components/Icon';
import { PageHeading, StatePanel } from '../components/PagePrimitives';

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
      </div>
    </section>
  );
}

function ResultOverview({ assessment }) {
  const result = assessment.calculation || {};
  const details = assessment.details || {};
  const people = Number(details.household_size) || 1;
  const daily = Number(assessment.daily_consumption) || 0;
  const perPerson = result.daily_per_person ?? (daily / people);
  return (
    <section className="results-overview" aria-label="Assessment results">
      <div className="results-summary"><span className="eyebrow">ESTIMATED HOUSEHOLD WATER USE</span><p className="results-primary-number">{formatNumber(daily)}<small> L/day</small></p><span className="results-summary-note">Estimated from your answers; actual use varies by fixtures and behavior.</span><div className="results-stat-row"><div><span>PER PERSON / DAY</span><strong>{formatNumber(perPerson)} <small>L</small></strong></div><div><span>PER WEEK</span><strong>{formatNumber(assessment.weekly_consumption)} <small>L</small></strong></div><div><span>PER 30 DAYS</span><strong>{formatNumber(assessment.monthly_consumption)} <small>L</small></strong></div></div>{result.calculation_version === 2 && <div className="results-source-split"><div><span>FROM PROVIDED VALUES</span><strong>{formatNumber(result.user_input_litres_per_day)} <small>L/day</small></strong><em>{result.user_input_categories} categories</em></div><div><span>FROM CONFIGURED ESTIMATES</span><strong>{formatNumber(result.assumption_litres_per_day)} <small>L/day</small></strong><em>{result.assumption_categories} categories</em></div></div>}</div>
      {result.assumptions?.length > 0 && <details className="assumptions-details"><summary>Assumptions & confidence <span>{result.estimate_kind === 'rough' ? 'Rough estimate' : 'Input-based estimate'}</span></summary><p>{result.assumption_disclaimer}</p><ul>{result.assumptions.map((item,index)=><li key={`${item}-${index}`}>{item}</li>)}</ul></details>}
      {result.calculation_version === 2 && !result.assumptions?.length && <details className="assumptions-details"><summary>Assumptions & confidence <span>{result.estimate_kind || 'Input-based estimate'}</span></summary><p>{result.assumption_disclaimer}</p></details>}
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
  const [enhancing, setEnhancing] = useState(false);
  const [enhancementStatus, setEnhancementStatus] = useState(null);

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
          setEnhancementStatus(pageData.plan.enhanced
            ? { type: 'success', message: 'AI has personalized the wording. AquaWise’s estimates and priorities are unchanged.' }
            : null);
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
      setEnhancementStatus(null);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [id]);

  const updateWording = async (enhance) => {
    if (enhancing || !data?.plan?.recommendations?.length) return;
    setEnhancing(true);
    setEnhancementStatus(null);
    try {
      const response = await recommendationService.getRecommendations(id, enhance);
      const result = response?.data?.success ? response.data.data : null;
      if (!Array.isArray(result?.recommendations)) throw new Error('Personalized wording unavailable.');

      if (data.plan.recommendations.length && result.recommendations.length === 0) {
        setEnhancementStatus({ type: 'fallback', message: 'The requested wording is unavailable right now. Your current AquaWise recommendations remain in view.' });
        return;
      }

      setData((previous) => ({ ...previous, plan: result }));
      setEnhancementStatus(enhance
        ? result.enhanced
          ? { type: 'success', message: 'AI has personalized the wording. AquaWise’s estimated savings and priorities are unchanged.' }
          : { type: 'fallback', message: 'AI wording is unavailable right now. These are the original AquaWise recommendations.' }
        : { type: 'original', message: 'Original AquaWise recommendation wording is shown.' });
    } catch {
      setEnhancementStatus({ type: 'error', message: enhance
        ? 'We couldn’t load personalized wording. Your existing recommendations are unchanged.'
        : 'We couldn’t reload the original wording. Your current recommendations are unchanged.' });
    } finally {
      setEnhancing(false);
    }
  };

  if (loading) return <PlanLoading />;

  if (error || !data) {
    return <div className="plan-error-page"><StatePanel tone="error" title="This action plan isn’t available" description="It may have been removed or temporarily unavailable. You can retry or choose another assessment." icon="warning" action={<><button type="button" onClick={retry} className="button button-primary">Try again</button><Link to="/recommendations" className="button button-quiet">All plans</Link></>}/></div>;
  }

  const { plan, assessment } = data;
  const recommendations = plan.recommendations;
  const isEnhanced = Boolean(plan.enhanced);

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
          <section className="recommendation-ai-panel" aria-labelledby="recommendation-ai-title"><div className="recommendation-ai-copy"><span className="recommendation-ai-icon"><Icon name="water" size={19}/></span><div><span className="eyebrow">OPTIONAL PERSONALIZATION</span><h3 id="recommendation-ai-title">Adjust the language to your context</h3><p>AquaWise calculates recommendations, priorities, and savings. AI only personalizes titles and explanations.</p></div></div><div className="recommendation-ai-actions">
              {isEnhanced ? (
                <button type="button" className="btn-secondary" onClick={() => updateWording(false)} disabled={enhancing}>
                  {enhancing ? 'Loading…' : 'Show original wording'}
                </button>
              ) : (
                <button type="button" className="btn-secondary recommendation-ai-button" onClick={() => updateWording(true)} disabled={enhancing}>
                  {enhancing && <span className="spinner recommendation-ai-spinner" />}
                  {enhancing ? 'Personalizing wording…' : 'Personalize wording with AI'}
                </button>
              )}
            </div>
            <AnimatePresence initial={false}>
              {enhancementStatus && (
                <motion.p
                  className={`recommendation-ai-status status-${enhancementStatus.type}`}
                  role={enhancementStatus.type === 'error' ? 'alert' : 'status'}
                  aria-live="polite"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  {enhancementStatus.message}
                </motion.p>
              )}
            </AnimatePresence>
          </section>
        </>}
    </motion.div>
  );
};

export default Recommendations;
