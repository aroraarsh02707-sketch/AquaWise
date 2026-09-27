import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { assessmentService, recommendationService } from '../services/api';
import Icon from '../components/Icon';

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
      <div className="recommendation-action-main">
        <div className="recommendation-action-topline">
          <span className="recommendation-category-label">{recommendation.category || 'Water conservation'}</span>
          {priority && <span className={`recommendation-priority priority-label-${priority}`}>{priority} priority</span>}
        </div>
        <h3>{recommendation.title || 'Water-saving action'}</h3>
        <div className="recommendation-why">
          <h4>Why this can help</h4>
          <p>{recommendation.description || 'AquaWise has not provided further details for this action.'}</p>
        </div>
      </div>
      <aside className="recommendation-savings-panel" aria-label="Estimated potential water savings">
        <span className="recommendation-savings-icon"><Icon name="water" size={19} /></span>
        <span className="recommendation-savings-label">Potential saving</span>
        {hasSaving ? (
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
    return (
      <section className="recommendation-state-card recommendation-error-state" role="alert">
        <span className="recommendation-state-icon"><Icon name="warning" size={22} /></span>
        <div>
          <h1>This action plan isn’t available</h1>
          <p>It may have been removed or temporarily unavailable. You can retry or choose another assessment.</p>
        </div>
        <button type="button" onClick={retry} className="btn-primary">Try again</button>
        <Link to="/recommendations" className="btn-secondary">Action plans</Link>
      </section>
    );
  }

  const { plan, assessment } = data;
  const recommendations = plan.recommendations;
  const isEnhanced = Boolean(plan.enhanced);

  return (
    <motion.div className="recommendations-page" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      <header className="page-header recommendations-page-header recommendations-detail-header">
        <div>
          <Link to="/recommendations" className="recommendation-back-link"><Icon name="arrowLeft" size={16} /> All action plans</Link>
          <p className="recommendations-eyebrow">ASSESSMENT ACTION PLAN</p>
          <h1>Recommended actions</h1>
          <p className="subtitle">Practical changes based on your assessment. Start with the actions that matter most to your water use.</p>
        </div>
        <span className="recommendation-count">{plan.count ?? recommendations.length} {recommendations.length === 1 ? 'action' : 'actions'}</span>
      </header>

      <AssessmentContext assessment={assessment} />

      {recommendations.length === 0 ? (
        <section className="recommendations-empty-state recommendation-plan-empty">
          <span className="recommendations-empty-icon"><Icon name="recommendations" size={27} /></span>
          <p className="recommendations-eyebrow">NO ACTIONS IN THIS PLAN</p>
          <h3>No recommendations were returned</h3>
          <p>This assessment has no saved recommendations to display. You can review another plan or complete a new assessment.</p>
          <div className="recommendation-empty-actions">
            <Link to="/assessment" className="btn-primary">New assessment <Icon name="arrowRight" size={16} /></Link>
            <Link to="/recommendations" className="btn-secondary">View other plans</Link>
          </div>
        </section>
      ) : (
        <>
          <section className="recommendation-list-heading" aria-labelledby="recommendation-list-title">
            <div>
              <h3 id="recommendation-list-title">Your conservation actions</h3>
              <p>Priority and potential savings are set by AquaWise’s assessment rules.</p>
            </div>
            <span>Ordered by potential daily savings</span>
          </section>

          <div className="recommendation-actions-list">
            {recommendations.map((recommendation, index) => (
              <RecommendationCard
                recommendation={recommendation}
                index={index}
                key={recommendation.id ?? `${recommendation.title}-${index}`}
              />
            ))}
          </div>

          <section className="recommendation-ai-panel" aria-labelledby="recommendation-ai-title">
            <div className="recommendation-ai-copy">
              <span className="recommendation-ai-icon"><Icon name="water" size={19} /></span>
              <div>
                <h3 id="recommendation-ai-title">Optional wording personalization</h3>
                <p>AquaWise calculates the recommendations, priorities, and savings. AI can personalize the titles and explanations only.</p>
              </div>
            </div>
            <div className="recommendation-ai-actions">
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
        </>
      )}
    </motion.div>
  );
};

export default Recommendations;
