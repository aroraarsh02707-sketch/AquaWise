export function getAuthErrorMessage(error, fallback = 'The request could not be completed. Please try again.') {
  const apiMessage = error?.response?.data?.error?.message;
  if (typeof apiMessage === 'string' && apiMessage.trim()) return apiMessage;

  if (error?.request) {
    return 'Could not reach the AquaWise API. Check that it is running and allows this frontend origin.';
  }

  if (typeof error?.message === 'string' && error.message.trim()) return error.message;
  return fallback;
}

export function getSafeAuthErrorDetails(error) {
  return {
    message: typeof error?.message === 'string' ? error.message : 'Unknown error',
    code: typeof error?.code === 'string' ? error.code : null,
    status: Number.isInteger(error?.response?.status) ? error.response.status : null,
  };
}
