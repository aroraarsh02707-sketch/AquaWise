import test from 'node:test';
import assert from 'node:assert/strict';
import { getAuthErrorMessage, getSafeAuthErrorDetails } from './src/utils/authError.js';

test('auth errors prefer the message returned by the API', () => {
  const error = { response: { data: { error: { message: 'Invalid email or password.' } } } };
  assert.equal(getAuthErrorMessage(error), 'Invalid email or password.');
});

test('auth network errors explain that the API or origin may be unreachable', () => {
  const error = { message: 'Network Error', request: {} };
  assert.match(getAuthErrorMessage(error), /Could not reach the AquaWise API/);
  assert.deepEqual(getSafeAuthErrorDetails(error), {
    message: 'Network Error',
    code: null,
    status: null,
  });
});

test('safe auth diagnostics omit request data and credentials', () => {
  const error = {
    message: 'Request failed',
    code: 'ERR_BAD_REQUEST',
    response: { status: 400 },
    config: { data: '{"email":"private@example.com","password":"secret"}' },
  };
  assert.deepEqual(getSafeAuthErrorDetails(error), {
    message: 'Request failed',
    code: 'ERR_BAD_REQUEST',
    status: 400,
  });
  assert.doesNotMatch(JSON.stringify(getSafeAuthErrorDetails(error)), /private@example.com|secret/);
});
