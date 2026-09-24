import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessmentService } from '../services/api';
import { motion } from 'framer-motion';

const Assessment = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Initialize form based on user type
  const isHousehold = user?.user_type === 'household';
  
  const initialHouseholdState = {
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
  };
  
  const initialFarmerState = {
    assessment_type: 'farmer',
    farm_area: 1,
    farm_area_unit: 'acre',
    crop_type: '',
    irrigation_method: 'drip',
    water_source: 'groundwater',
    irrigation_frequency: 1,
    irrigation_duration_minutes: 60,
    estimated_irrigation_litres: 0,
  };

  const [formData, setFormData] = useState(isHousehold ? initialHouseholdState : initialFarmerState);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    let parsedValue = value;
    
    if (type === 'number') {
      parsedValue = value === '' ? '' : Number(value);
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: parsedValue
    }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    
    try {
      const response = await assessmentService.createAssessment(formData);
      if (response.data.success) {
        const newAssessmentId = response.data.data.id;
        navigate(`/recommendations/${newAssessmentId}`);
      }
    } catch (err) {
      if (err.response?.data?.error?.details) {
        // Validation errors returned as an object { field: "message" }
        const details = err.response.data.error.details;
        const firstError = Object.values(details)[0];
        setError(firstError || 'Validation failed. Please check your inputs.');
      } else {
        setError(err.response?.data?.error?.message || 'Failed to submit assessment. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div 
      className="assessment-page"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <header className="page-header">
        <div>
          <h2>Water Usage Assessment</h2>
          <p className="subtitle">
            Fill out the details below so we can calculate your Water Saver Score and provide personalized recommendations.
          </p>
        </div>
      </header>

      <div className="assessment-container">
        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="assessment-form">
          {isHousehold ? (
            <>
              <h3 className="section-title">Household Information</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="household_size">Household Size (People)</label>
                  <input type="number" id="household_size" name="household_size" min="1" max="50" required
                    value={formData.household_size} onChange={handleChange} disabled={isSubmitting} />
                </div>
              </div>

              <h3 className="section-title">Indoor Usage</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="showers_per_day">Showers per day (total)</label>
                  <input type="number" id="showers_per_day" name="showers_per_day" min="0" max="20" step="1" required
                    value={formData.showers_per_day} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="shower_duration_minutes">Avg. Shower Duration (minutes)</label>
                  <input type="number" id="shower_duration_minutes" name="shower_duration_minutes" min="0" max="60" required
                    value={formData.shower_duration_minutes} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="toilet_uses_per_day">Toilet Flushes per day (total)</label>
                  <input type="number" id="toilet_uses_per_day" name="toilet_uses_per_day" min="0" max="60" step="1" required
                    value={formData.toilet_uses_per_day} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="kitchen_usage_minutes">Kitchen Tap Usage (minutes/day)</label>
                  <input type="number" id="kitchen_usage_minutes" name="kitchen_usage_minutes" min="0" max="180" required
                    value={formData.kitchen_usage_minutes} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="laundry_loads_per_week">Laundry Loads per week</label>
                  <input type="number" id="laundry_loads_per_week" name="laundry_loads_per_week" min="0" max="30" step="1" required
                    value={formData.laundry_loads_per_week} onChange={handleChange} disabled={isSubmitting} />
                </div>
              </div>

              <h3 className="section-title">Outdoor & Other Usage</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="gardening_frequency">Gardening Sessions per week</label>
                  <input type="number" id="gardening_frequency" name="gardening_frequency" min="0" max="14" step="1"
                    value={formData.gardening_frequency} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="gardening_duration_minutes">Gardening Duration (minutes)</label>
                  <input type="number" id="gardening_duration_minutes" name="gardening_duration_minutes" min="0" max="240"
                    value={formData.gardening_duration_minutes} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="vehicle_washing_frequency">Vehicle Wash per week</label>
                  <input type="number" id="vehicle_washing_frequency" name="vehicle_washing_frequency" min="0" max="14" step="1"
                    value={formData.vehicle_washing_frequency} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="other_usage_litres">Other Usage (litres/day)</label>
                  <input type="number" id="other_usage_litres" name="other_usage_litres" min="0" max="1000"
                    value={formData.other_usage_litres} onChange={handleChange} disabled={isSubmitting} />
                </div>
              </div>
            </>
          ) : (
            <>
              <h3 className="section-title">Farm Details</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="farm_area">Farm Area</label>
                  <input type="number" id="farm_area" name="farm_area" min="0.001" max="10000" step="any" required
                    value={formData.farm_area} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="farm_area_unit">Area Unit</label>
                  <select id="farm_area_unit" name="farm_area_unit" required value={formData.farm_area_unit} onChange={handleChange} disabled={isSubmitting}>
                    <option value="acre">Acres</option>
                    <option value="hectare">Hectares</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="crop_type">Crop Type</label>
                  <input type="text" id="crop_type" name="crop_type" maxLength="100" required
                    value={formData.crop_type} onChange={handleChange} disabled={isSubmitting} />
                </div>
              </div>

              <h3 className="section-title">Irrigation Details</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="irrigation_method">Irrigation Method</label>
                  <select id="irrigation_method" name="irrigation_method" required value={formData.irrigation_method} onChange={handleChange} disabled={isSubmitting}>
                    <option value="flood">Flood</option>
                    <option value="drip">Drip</option>
                    <option value="sprinkler">Sprinkler</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="water_source">Water Source</label>
                  <select id="water_source" name="water_source" required value={formData.water_source} onChange={handleChange} disabled={isSubmitting}>
                    <option value="groundwater">Groundwater</option>
                    <option value="canal">Canal</option>
                    <option value="rainwater">Rainwater</option>
                    <option value="tank">Tank</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="irrigation_frequency">Irrigation Sessions per week</label>
                  <input type="number" id="irrigation_frequency" name="irrigation_frequency" min="0" max="30" step="1"
                    value={formData.irrigation_frequency} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="irrigation_duration_minutes">Irrigation Duration (minutes)</label>
                  <input type="number" id="irrigation_duration_minutes" name="irrigation_duration_minutes" min="0" max="1440"
                    value={formData.irrigation_duration_minutes} onChange={handleChange} disabled={isSubmitting} />
                </div>
                <div className="form-group">
                  <label htmlFor="estimated_irrigation_litres">Estimated Irrigation Volume (litres/day - optional override)</label>
                  <input type="number" id="estimated_irrigation_litres" name="estimated_irrigation_litres" min="0" max="1000000"
                    value={formData.estimated_irrigation_litres} onChange={handleChange} disabled={isSubmitting} />
                </div>
              </div>
            </>
          )}

          <div className="form-actions">
            <button 
              type="submit" 
              className="btn-primary auth-submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Calculating...' : 'Submit Assessment'}
            </button>
          </div>
        </form>
      </div>
    </motion.div>
  );
};

export default Assessment;
