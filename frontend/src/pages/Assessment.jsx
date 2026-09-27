import React, { useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { assessmentService } from '../services/api';
import Icon from '../components/Icon';

const householdSteps = [
  {
    title: 'People & daily routines',
    description: 'Estimate everyday indoor use for your household. Shower and toilet counts are per person; kitchen tap time is for everyone together.',
    fields: [
      { name: 'household_size', label: 'People in the household', type: 'number', unit: 'people', min: 1, max: 50, step: 1, required: true, hint: 'This helps account for shared daily activities.' },
      { name: 'showers_per_day', label: 'Showers per person', type: 'number', unit: 'per day', min: 0, max: 20, step: 1, required: true },
      { name: 'shower_duration_minutes', label: 'Average shower duration', type: 'number', unit: 'minutes', min: 0, max: 60, required: true },
      { name: 'toilet_uses_per_day', label: 'Toilet flushes per person', type: 'number', unit: 'per day', min: 0, max: 60, step: 1, required: true },
      { name: 'kitchen_usage_minutes', label: 'Kitchen tap use', type: 'number', unit: 'minutes per day', min: 0, max: 180, required: true, hint: 'Estimate total tap-on time for the household.' },
      { name: 'laundry_loads_per_week', label: 'Laundry loads', type: 'number', unit: 'per week', min: 0, max: 30, step: 1, required: true },
    ],
  },
  {
    title: 'Outdoor & other use',
    description: 'Add regular outdoor activities or other water use. Leave these at zero if they do not apply.',
    fields: [
      { name: 'gardening_frequency', label: 'Gardening sessions', type: 'number', unit: 'per week', min: 0, max: 14, step: 1 },
      { name: 'gardening_duration_minutes', label: 'Gardening time per session', type: 'number', unit: 'minutes', min: 0, max: 240 },
      { name: 'vehicle_washing_frequency', label: 'Vehicle washes', type: 'number', unit: 'per week', min: 0, max: 14, step: 1 },
      { name: 'other_usage_litres', label: 'Other water use', type: 'number', unit: 'litres per day', min: 0, max: 1000, hint: 'Include any daily use not covered above.' },
    ],
  },
];

const farmerSteps = [
  {
    title: 'Farm & crop details',
    description: 'Start with the size of the area you manage and the crop you grow.',
    fields: [
      { name: 'farm_area', label: 'Farm area', type: 'number', min: 0.001, max: 10000, step: 'any', required: true },
      { name: 'farm_area_unit', label: 'Area unit', type: 'select', required: true, options: [{ value: 'acre', label: 'Acres' }, { value: 'hectare', label: 'Hectares' }] },
      { name: 'crop_type', label: 'Crop type', type: 'text', maxLength: 100, required: true, hint: 'Enter the main crop grown on this farm.' },
    ],
  },
  {
    title: 'Irrigation & water source',
    description: 'Tell us how often you irrigate and which method you use. Optional estimates can make your result more specific.',
    fields: [
      { name: 'irrigation_method', label: 'Irrigation method', type: 'select', required: true, options: [{ value: 'flood', label: 'Flood' }, { value: 'drip', label: 'Drip' }, { value: 'sprinkler', label: 'Sprinkler' }, { value: 'other', label: 'Other' }] },
      { name: 'water_source', label: 'Main water source', type: 'select', options: [{ value: 'groundwater', label: 'Groundwater' }, { value: 'canal', label: 'Canal' }, { value: 'rainwater', label: 'Rainwater' }, { value: 'tank', label: 'Tank' }, { value: 'other', label: 'Other' }] },
      { name: 'irrigation_frequency', label: 'Irrigation sessions', type: 'number', unit: 'per week', min: 0, max: 30, step: 1 },
      { name: 'irrigation_duration_minutes', label: 'Irrigation time per session', type: 'number', unit: 'minutes', min: 0, max: 1440 },
      { name: 'estimated_irrigation_litres', label: 'Estimated irrigation volume', type: 'number', unit: 'litres per session', min: 0, max: 1000000, hint: 'Optional override. Enter your observed volume for one session, if known.' },
    ],
  },
];

const initialValues = {
  household: {
    assessment_type: 'household',
    household_size: 1,
    showers_per_day: 1,
    shower_duration_minutes: 5,
    toilet_uses_per_day: 4,
    laundry_loads_per_week: 2,
    kitchen_usage_minutes: 15,
    vehicle_washing_frequency: 0,
    gardening_frequency: 0,
    gardening_duration_minutes: 0,
    other_usage_litres: 0,
  },
  farmer: {
    assessment_type: 'farmer',
    farm_area: 1,
    farm_area_unit: 'acre',
    crop_type: '',
    irrigation_method: 'drip',
    water_source: 'groundwater',
    irrigation_frequency: 1,
    irrigation_duration_minutes: 60,
    estimated_irrigation_litres: 0,
  },
};

const formatValue = (field, value) => {
  if (field.type === 'select') {
    return field.options.find((option) => option.value === value)?.label || 'Not selected';
  }
  if (value === '' || value == null) return 'Not entered';
  if (field.type === 'number') return `${value}${field.unit ? ` ${field.unit}` : ''}`;
  return value;
};

const Assessment = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isHousehold = user?.user_type === 'household';
  const assessmentType = isHousehold ? 'household' : 'farmer';
  const steps = isHousehold ? householdSteps : farmerSteps;
  const [formData, setFormData] = useState(() => ({ ...initialValues[assessmentType] }));
  const [currentStep, setCurrentStep] = useState(0);
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formRef = useRef(null);
  const headingRef = useRef(null);
  const shouldFocusStep = useRef(false);
  const submissionLock = useRef(false);

  const allFields = useMemo(() => steps.flatMap((step) => step.fields), [steps]);
  const activeStep = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  const changeStep = (step) => {
    shouldFocusStep.current = true;
    setCurrentStep(step);
    setFormError('');
  };

  const handleChange = (event) => {
    const { name, value, type } = event.target;
    setFormData((previous) => ({
      ...previous,
      [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value,
    }));
    setFieldErrors((previous) => {
      if (!previous[name]) return previous;
      const next = { ...previous };
      delete next[name];
      return next;
    });
    setFormError('');
  };

  const goToNextStep = () => {
    if (!formRef.current?.reportValidity()) return;
    setFieldErrors({});
    changeStep(currentStep + 1);
  };

  const goToPreviousStep = () => {
    if (currentStep > 0) changeStep(currentStep - 1);
  };

  const applyValidationErrors = (details) => {
    if (!details || typeof details !== 'object') return false;
    setFieldErrors(details);
    const firstInvalidField = allFields.find((field) => details[field.name]);
    if (firstInvalidField) {
      const invalidStep = steps.findIndex((step) => step.fields.some((field) => field.name === firstInvalidField.name));
      if (invalidStep !== -1 && invalidStep !== currentStep) changeStep(invalidStep);
    }
    setFormError(Object.values(details)[0] || 'Please review the highlighted fields.');
    return true;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (submissionLock.current || !formRef.current?.reportValidity()) return;

    submissionLock.current = true;
    setIsSubmitting(true);
    setFormError('');
    setFieldErrors({});
    try {
      const payload = { ...formData };
      allFields.forEach((field) => {
        if (field.type === 'number' && !field.required && payload[field.name] === '') {
          payload[field.name] = 0;
        }
      });
      const response = await assessmentService.createAssessment(payload);
      if (!response?.data?.success) {
        const details = response?.data?.error?.details;
        if (!applyValidationErrors(details)) {
          setFormError(response?.data?.error?.message || 'We couldn’t confirm your assessment. Please review your answers and try again.');
        }
        return;
      }

      const assessmentId = response.data.data?.id;
      if (assessmentId == null) {
        setFormError('Your assessment response was incomplete. Your answers are still here; please try submitting again.');
        return;
      }

      navigate(`/recommendations/${assessmentId}`);
    } catch (error) {
      const details = error.response?.data?.error?.details;
      if (!applyValidationErrors(details)) {
        setFormError(error.response?.data?.error?.message || 'We couldn’t submit your assessment. Check your connection and try again.');
      }
    } finally {
      submissionLock.current = false;
      setIsSubmitting(false);
    }
  };

  const renderField = (field) => {
    const errorId = `${field.name}-error`;
    const hintId = `${field.name}-hint`;
    const describedBy = [field.hint ? hintId : null, fieldErrors[field.name] ? errorId : null].filter(Boolean).join(' ') || undefined;
    const commonProps = {
      id: field.name,
      name: field.name,
      required: Boolean(field.required),
      disabled: isSubmitting,
      'aria-invalid': Boolean(fieldErrors[field.name]),
      'aria-describedby': describedBy,
      onChange: handleChange,
    };

    return (
      <div className={`assessment-field ${fieldErrors[field.name] ? 'has-error' : ''}`} key={field.name}>
        <div className="assessment-field-heading">
          <label htmlFor={field.name}>{field.label}</label>
          <span className={`assessment-field-requirement ${field.required ? 'required' : ''}`}>
            {field.required ? 'Required' : 'Optional'}
          </span>
        </div>
        <div className={field.unit && field.type === 'number' ? 'assessment-input-with-unit' : undefined}>
          {field.type === 'select' ? (
            <select {...commonProps} value={formData[field.name] ?? ''}>
              {!field.required && <option value="">Not sure</option>}
              {field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          ) : (
            <input
              {...commonProps}
              type={field.type}
              inputMode={field.type === 'number' ? 'decimal' : undefined}
              value={formData[field.name] ?? ''}
              min={field.min}
              max={field.max}
              step={field.step ?? (field.type === 'number' ? 'any' : undefined)}
              maxLength={field.maxLength}
              autoComplete="off"
            />
          )}
          {field.unit && field.type === 'number' && <span className="assessment-input-unit" aria-hidden="true">{field.unit}</span>}
        </div>
        {field.hint && <p className="assessment-field-hint" id={hintId}>{field.hint}</p>}
        {fieldErrors[field.name] && <p className="assessment-field-error" id={errorId}>{fieldErrors[field.name]}</p>}
      </div>
    );
  };

  return (
    <motion.div className="assessment-page" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <header className="page-header assessment-page-header">
        <div>
          <p className="assessment-eyebrow">WATER USE CHECK-IN</p>
          <h2>Water usage assessment</h2>
          <p className="subtitle">A few details help us build a useful picture of your {isHousehold ? 'household' : 'farm'} water use.</p>
        </div>
        <Link to="/dashboard" className="assessment-cancel-link">Back to overview</Link>
      </header>

      <section className="assessment-container" aria-label={`${isHousehold ? 'Household' : 'Farm'} water assessment`}>
        <div className="assessment-type-notice">
          <span className="assessment-type-icon"><Icon name={isHousehold ? 'water' : 'assessment'} size={19} /></span>
          <div>
            <strong>{isHousehold ? 'Household assessment' : 'Farm assessment'}</strong>
            <p>This follows the account type on your profile. You can update it from Profile.</p>
          </div>
        </div>

        <div className="assessment-progress">
          <div className="assessment-progress-copy">
            <span>Step {currentStep + 1} of {steps.length}</span>
            <span>{currentStep === steps.length - 1 ? 'Final step' : `${steps.length - currentStep - 1} step${steps.length - currentStep - 1 === 1 ? '' : 's'} remaining`}</span>
          </div>
          <div className="assessment-progress-track" role="progressbar" aria-label="Assessment progress" aria-valuemin={1} aria-valuemax={steps.length} aria-valuenow={currentStep + 1} aria-valuetext={`Step ${currentStep + 1} of ${steps.length}`}>
            <span style={{ width: `${progress}%` }} />
          </div>
          <div className="assessment-step-labels" aria-hidden="true">
            {steps.map((step, index) => (
              <span className={index <= currentStep ? 'complete' : ''} key={step.title}>{step.title}</span>
            ))}
          </div>
        </div>

        <form ref={formRef} className="assessment-form" onSubmit={handleSubmit} aria-busy={isSubmitting}>
          {formError && (
            <div className="assessment-form-error" role="alert">
              <Icon name="warning" size={17} />
              <span>{formError}</span>
            </div>
          )}

          <AnimatePresence mode="wait" initial={false}>
            <motion.section
              className="assessment-step"
              key={activeStep.title}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.16 }}
              onAnimationComplete={() => {
                if (shouldFocusStep.current) {
                  headingRef.current?.focus();
                  shouldFocusStep.current = false;
                }
              }}
              aria-labelledby="assessment-step-title"
            >
              <div className="assessment-step-heading">
                <h3 id="assessment-step-title" ref={headingRef} tabIndex={-1}>{activeStep.title}</h3>
                <p>{activeStep.description}</p>
              </div>
              <div className="assessment-fields-grid">
                {activeStep.fields.map(renderField)}
              </div>

              {currentStep === steps.length - 1 && (
                <div className="assessment-review" aria-labelledby="assessment-review-title">
                  <div className="assessment-review-heading">
                    <span><Icon name="assessment" size={17} /></span>
                    <div>
                      <h4 id="assessment-review-title">Before you submit</h4>
                      <p>Review the information entered. Your water estimate is calculated after submission.</p>
                    </div>
                  </div>
                  <dl className="assessment-review-list">
                    {steps.flatMap((step) => step.fields).map((field) => (
                      <div className="assessment-review-item" key={field.name}>
                        <dt>{field.label}</dt>
                        <dd>{formatValue(field, formData[field.name])}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}
            </motion.section>
          </AnimatePresence>

          <div className="assessment-navigation">
            {currentStep > 0 ? (
              <button type="button" className="btn-secondary" onClick={goToPreviousStep} disabled={isSubmitting}>
                <Icon name="arrowLeft" size={17} /> Back
              </button>
            ) : (
              <span className="assessment-nav-note">Fields marked required must be completed.</span>
            )}
            {currentStep < steps.length - 1 ? (
              <button type="button" className="btn-primary" onClick={goToNextStep} disabled={isSubmitting}>
                Continue <Icon name="arrowRight" size={17} />
              </button>
            ) : (
              <button type="submit" className="btn-primary assessment-submit" disabled={isSubmitting}>
                {isSubmitting ? <><span className="spinner assessment-submit-spinner" />Saving assessment…</> : <>Submit assessment <Icon name="arrowRight" size={17} /></>}
              </button>
            )}
          </div>
        </form>
      </section>
    </motion.div>
  );
};

export default Assessment;
