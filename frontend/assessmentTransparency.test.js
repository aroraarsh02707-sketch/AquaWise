import test from 'node:test';
import assert from 'node:assert/strict';
import { getAssessmentQuality, getScorePresentation } from './src/assessmentTransparency.js';

test('complete provided-input assessment is not labeled incomplete', () => {
  const quality = getAssessmentQuality({
    calculation_version: 2,
    unavailable_categories: [],
    incomplete_categories: [],
    assumptions: [],
    assumption_litres_per_day: 0,
  });
  assert.equal(quality.status, 'Based on provided values');
  assert.equal(quality.incomplete, false);
  assert.deepEqual(quality.missingCategories, []);
});

test('incomplete assessment identifies missing categories and qualifies the score', () => {
  const calculation = {
    calculation_version: 2,
    unavailable_categories: ['Laundry'],
    incomplete_categories: ['Bathing & showers'],
    assumptions: [],
    assumption_litres_per_day: 0,
  };
  const quality = getAssessmentQuality(calculation);
  assert.equal(quality.status, 'Incomplete estimate');
  assert.deepEqual(quality.missingCategories, ['Laundry', 'Bathing & showers']);
  assert.match(quality.explanation, /may not represent all household water consumption/);
  assert.match(getScorePresentation('household', calculation).qualification, /may affect how representative/);
});

test('household score presentation shows category coverage and missing-use caveat', () => {
  const info = getScorePresentation('household', {
    calculation_version: 2,
    category_count: 5,
    category_total: 7,
    user_input_categories: 4,
    assumption_categories: 1,
    unavailable_categories: ['Laundry', 'Outdoor watering'],
    incomplete_categories: ['Kitchen & dishwashing'],
    assumptions: ['Default kitchen tap flow: 6'],
    assumption_litres_per_day: 30,
  });
  assert.match(info.completenessNote, /Based on 5 of 7 categories/);
  assert.match(info.completenessNote, /2 unavailable, 1 incomplete/);
  assert.match(info.completenessCaveat, /can make the score look better than it is/);
  assert.match(info.description, /Not a measured or validated assessment/);
  assert.match(info.scoreMethod, /150 L\/person\/day figure is a reference point/);
});

test('configured estimates are distinguished from entered values and qualify score', () => {
  const calculation = {
    calculation_version: 2,
    unavailable_categories: [],
    incomplete_categories: [],
    assumptions: ['Default shower flow (L/min): 9'],
    assumption_litres_per_day: 45,
  };
  assert.equal(getAssessmentQuality(calculation).status, 'Configured estimates used');
  assert.match(getScorePresentation('household', calculation).qualification, /Configured estimates contribute/);
});

test('legacy non-household score description uses the generic archived fallback', () => {
  const info = getScorePresentation('farmer', {
    calculation_version: 2,
    unavailable_categories: [],
    incomplete_categories: [],
    assumptions: [],
    assumption_litres_per_day: 0,
  });
  assert.match(info.description, /legacy assessment/);
  assert.match(info.description, /not presented in the current household workspace/);
});

test('older saved assessments without completeness metadata are qualified as unknown', () => {
  const info = getScorePresentation('household', { daily_consumption: 100 });
  assert.equal(getAssessmentQuality({ daily_consumption: 100 }).status, 'Completeness not recorded');
  assert.match(info.qualification, /representativeness is unknown/);
});
