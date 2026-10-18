import test from 'node:test';
import assert from 'node:assert/strict';
import { createDonutSegments } from './src/dashboardChart.js';

test('donut segments preserve category values and assigned chart colors', () => {
  const segments = createDonutSegments([
    { category: 'Bathroom taps', litres_per_day: 750, percentage: 75 },
    { category: 'Laundry', litres_per_day: 250, percentage: 25 },
  ], ['#42C7D9', '#58C4A0']);

  assert.equal(segments.length, 2);
  assert.deepEqual(segments.map(({ value }) => value), [750, 250]);
  assert.deepEqual(segments.map(({ color }) => color), ['#42C7D9', '#58C4A0']);
  assert.ok(segments.every(({ path }) => path.startsWith('M ') && path.endsWith(' Z')));
  assert.match(segments[0].path, /A 109 109 0 1 1/);
});

test('donut chart stays empty when there are no positive category volumes', () => {
  assert.deepEqual(createDonutSegments([
    { category: 'Bathroom taps', litres_per_day: 0 },
    { category: 'Laundry', litres_per_day: null },
  ], ['#42C7D9']), []);
});
