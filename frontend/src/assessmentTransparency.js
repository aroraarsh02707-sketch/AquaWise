const names = (items) => Array.isArray(items) ? items.filter((item) => typeof item === 'string' && item.trim()) : [];

export function getAssessmentQuality(calculation) {
  if (!calculation || calculation.calculation_version !== 2) {
    return {
      status: 'Completeness not recorded',
      incomplete: false,
      missingCategories: [],
      explanation: 'This saved assessment does not include category-completeness metadata, so its total may not represent all water use.',
      hasAssumptions: false,
    };
  }

  const unavailable = names(calculation.unavailable_categories);
  const incomplete = names(calculation.incomplete_categories);
  const missingCategories = [...new Set([...unavailable, ...incomplete])];
  const isIncomplete = missingCategories.length > 0;
  const hasAssumptions = names(calculation.assumptions).length > 0 || Number(calculation.assumption_litres_per_day) > 0;

  return {
    status: isIncomplete ? 'Incomplete estimate' : hasAssumptions ? 'Configured estimates used' : 'Based on provided values',
    incomplete: isIncomplete,
    missingCategories,
    hasAssumptions,
    hasUnavailableCategories: unavailable.length > 0,
    completenessNote: Number.isFinite(Number(calculation.category_count)) && Number.isFinite(Number(calculation.category_total))
      ? `Based on ${Number(calculation.category_count)} of ${Number(calculation.category_total)} categories${Number(calculation.user_input_categories) || Number(calculation.assumption_categories) || unavailable.length || incomplete.length ? `: ${Number(calculation.user_input_categories) || 0} include entered values, ${Number(calculation.assumption_categories) || 0} include configured estimates, ${unavailable.length} unavailable, ${incomplete.length} incomplete` : ''}.`
      : '',
    explanation: isIncomplete
      ? 'Known values are included, but the total may not represent all household water consumption.'
      : hasAssumptions
        ? 'Configured defaults contribute to this estimate; actual use may differ.'
        : 'The estimate uses the values entered. Entered values are not necessarily meter-measured.',
  };
}

export function getScorePresentation(assessmentType, calculation) {
  const isHousehold = assessmentType === 'household';
  const description = isHousehold
    ? 'Estimated indicator based on the information you entered. Not a measured or validated assessment.'
    : 'Saved score from a legacy assessment. Its calculation method is not presented in the current household workspace.';
  const quality = getAssessmentQuality(calculation);

  let qualification = '';
  if (quality.incomplete) {
    qualification = 'Incomplete usage details may affect how representative this score is. The score itself is unchanged.';
  } else if (quality.hasAssumptions) {
    qualification = 'Configured estimates contribute to this score, so actual use may differ. The score itself is unchanged.';
  } else if (quality.status === 'Completeness not recorded') {
    qualification = 'Completeness information is not stored for this assessment, so score representativeness is unknown.';
  }

  const scoreMethod = isHousehold
    ? 'Household score uses estimated daily use per person, with fixed shower, vehicle-washing, and kitchen adjustments. The 150 L/person/day figure is a reference point.'
    : '';
  const completenessCaveat = quality.hasUnavailableCategories
    ? 'Unavailable categories may be omitted, which can make the score look better than it is.'
    : '';

  return { description, qualification, completenessNote: quality.completenessNote, completenessCaveat, scoreMethod };
}
