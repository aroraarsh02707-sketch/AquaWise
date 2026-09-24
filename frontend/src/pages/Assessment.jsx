import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessmentService } from '../services/api';
import { motion } from 'framer-motion';

const HOUSEHOLD_GROUPS = [
  {
    label: 'Household',
    hint: 'How many people share this water supply?',
    fields: [
      { name: 'household_size', label: 'Number of People', type: 'number', min: 1, max: 50, step: 1, required: true },
    ],
  },
  {
    label: 'Daily Indoor Usage',
    hint: 'Estimate daily activities for the whole household.',
    fields: [
      { name: 'showers_per_day', label: 'Total Showers per Day', type: 'number', min: 0, max: 20, step: 1, required: true },
      { name: 'shower_duration_minutes', label: 'Avg. Shower Duration (minutes)', type: 'number', min: 0, max: 60, required: true },
      { name: 'toilet_uses_per_day', label: 'Total Toilet Flushes per Day', type: 'number', min: 0, max: 60, step: 1, required: true },
      { name: 'kitchen_usage_minutes', label: 'Kitchen Tap Usage (minutes/day)', type: 'number', min: 0, max: 180, required: true },
      { name: 'laundry_loads_per_week', label: 'Laundry Loads per Week', type: 'number', min: 0, max: 30, step: 1, required: true },
    ],
  },
  {
    label: 'Outdoor & Other',
    hint: 'Leave as 0 if not applicable.',
    fields: [
      { name: 'gardening_frequency', label: 'Gardening Sessions per Week', type: 'number', min: 0, max: 14, step: 1 },
      { name: 'gardening_duration_minutes', label: 'Gardening Duration (minutes/session)', type: 'number', min: 0, max: 240 },
      { name: 'vehicle_washing_frequency', label: 'Vehicle Washes per Week', type: 'number', min: 0, max: 14, step: 1 },
      { name: 'other_usage_litres', label: 'Other Usage (litres/day)', type: 'number', min: 0, max: 1000 },
    ],
  },
];

const FARMER_GROUPS = [
  {
    label: 'Farm Details',
    hint: null,
    fields: [
      { name: 'farm_area', label: 'Farm Area', type: 'number', min: 0.001, max: 10000, step: 'any', required: true },
      { name: 'farm_area_unit', label: 'Area Unit', type: 'select', options: [{ value: 'acre', label: 'Acres' }, { value: 'hectare', label: 'Hectares' }], required: true },
      { name: 'crop_type', label: 'Crop Type', type: 'text', maxLength: 100, required: true },
    ],
  },
  {
    label: 'Irrigation',
    hint: null,
    fields: [
      { name: 'irrigation_method', label: 'Irrigation Method', type: 'select', options: [{ value: 'flood', label: 'Flood' }, { value: 'drip', label: 'Drip' }, { value: 'sprinkler', label: 'Sprinkler' }, { value: 'other', label: 'Other' }], required: true },
      { name: 'water_source', label: 'Water Source', type: 'select', options: [{ value: 'groundwater', label: 'Groundwater' }, { value: 'canal', label: 'Canal' }, { value: 'rainwater', label: 'Rainwater' }, { value: 'tank', label: 'Tank' }, { value: 'other', label: 'Other' }] },
      { name: 'irrigation_frequency', label: 'Sessions per Week', type: 'number', min: 0, max: 30, step: 1 },
      { name: 'irrigation_duration_minutes', label: 'Duration per Session (minutes)', type: 'number', min: 0, max: 1440 },
      { name: 'estimated_irrigation_litres', label: 'Est. Volume per Day (litres, optional override)', type: 'number', min: 0, max: 1000000 },
    ],
  },
];

const Assessment = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isHousehold = user?.user_type === 'household';

  const initState = isHousehold
    ? { assessment_type: 'household', household_size: 1, showers_per_day: 1, shower_duration_minutes: 5, toilet_uses_per_day: 4, laundry_loads_per_week: 2, kitchen_usage_minutes: 15, vehicle_washing_frequency: 0, gardening_frequency: 0, gardening_duration_minutes: 0, other_usage_litres: 0 }
    : { assessment_type: 'farmer', farm_area: 1, farm_area_unit: 'acre', crop_type: '', irrigation_method: 'drip', water_source: 'groundwater', irrigation_frequency: 1, irrigation_duration_minutes: 60, estimated_irrigation_litres: 0 };

  const [formData, setFormData] = useState(initState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({ ...prev, [name]: type === 'number' ? (value === '' ? '' : Number(value)) : value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await assessmentService.createAssessment(formData);
      if (response.data.success) {
        navigate(`/recommendations/${response.data.data.id}`);
      }
    } catch (err) {
      if (err.response?.data?.error?.details) {
        const details = err.response.data.error.details;
        setError(Object.values(details)[0] || 'Validation failed. Please check your inputs.');
      } else {
        setError(err.response?.data?.error?.message || 'Failed to submit assessment. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const groups = isHousehold ? HOUSEHOLD_GROUPS : FARMER_GROUPS;

  return (
    <motion.div className="assessment-page"
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}
    >
      <header className="page-header">
        <div>
          <h2>Water Usage Assessment</h2>
          <p className="subtitle">Fill in your water habits so we can calculate your score and recommendations.</p>
        </div>
      </header>

      <div className="assessment-container">
        <div className="assessment-type-notice">
          <span>📋</span>
          <span>Completing a <strong>{isHousehold ? 'Household' : 'Farmer'}</strong> assessment. To change your type, update it in your Profile.</span>
        </div>

        <div className="assessment-body">
          {error && <div className="auth-error" style={{ marginBottom: '1.5rem' }}>{error}</div>}

          <form onSubmit={handleSubmit} noValidate>
            {groups.map((group, gi) => (
              <div key={gi} className="section-group">
                <div className="section-group-label">{group.label}</div>
                {group.hint && <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '1rem', marginTop: '-0.5rem' }}>{group.hint}</p>}
                <div className="form-grid">
                  {group.fields.map((field) => (
                    <div className="form-group" key={field.name}>
                      <label htmlFor={field.name}>{field.label}</label>
                      {field.type === 'select' ? (
                        <select id={field.name} name={field.name} value={formData[field.name] || ''} onChange={handleChange} disabled={isSubmitting} required={field.required}>
                          {field.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      ) : field.type === 'text' ? (
                        <input type="text" id={field.name} name={field.name} maxLength={field.maxLength} required={field.required}
                          value={formData[field.name] || ''} onChange={handleChange} disabled={isSubmitting} />
                      ) : (
                        <input type="number" id={field.name} name={field.name}
                          min={field.min} max={field.max} step={field.step ?? 'any'} required={field.required}
                          value={formData[field.name] ?? 0} onChange={handleChange} disabled={isSubmitting} />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={isSubmitting}
                style={{ padding: '0.8rem 2rem', fontSize: '1rem' }}>
                {isSubmitting
                  ? <><span className="spinner" style={{ width: 18, height: 18, borderWidth: 2, marginRight: '0.5rem' }} />Calculating…</>
                  : 'Submit Assessment →'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </motion.div>
  );
};

export default Assessment;
