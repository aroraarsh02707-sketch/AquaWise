import axios from 'axios';

// Local Vite development keeps the Flask API on port 5000. Production serves
// the app and API from Flask, so relative requests keep session cookies same-origin.
const API_BASE_URL = import.meta.env.VITE_API_URL
  || (import.meta.env.PROD ? '/api' : 'http://localhost:5000/api');

// Warm the configured API origin before AuthContext makes its initial session request.
if (typeof document !== 'undefined') {
  try {
    const apiOrigin = new URL(API_BASE_URL, window.location.href).origin;
    if (apiOrigin !== window.location.origin && !document.querySelector(`link[rel="preconnect"][href="${apiOrigin}"]`)) {
      const preconnect = document.createElement('link');
      preconnect.rel = 'preconnect';
      preconnect.href = apiOrigin;
      preconnect.crossOrigin = 'use-credentials';
      document.head.appendChild(preconnect);
    }
  } catch {
    // Let Axios report malformed API URL configuration through the normal request path.
  }
}

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending/receiving Flask session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

let csrfToken = null;
let csrfTokenRequest = null;

api.interceptors.request.use(async (config) => {
  const method = (config.method || 'get').toLowerCase();
  if (!['post', 'put', 'patch', 'delete'].includes(method)) return config;

  if (!csrfToken) {
    csrfTokenRequest ||= api.get('/auth/csrf')
      .then((response) => {
        csrfToken = response.data?.data?.csrf_token || null;
        return csrfToken;
      })
      .finally(() => { csrfTokenRequest = null; });
    await csrfTokenRequest;
  }
  if (csrfToken) config.headers['X-CSRF-Token'] = csrfToken;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error?.code === 'CSRF_TOKEN_INVALID') csrfToken = null;
    return Promise.reject(error);
  },
);

// Auth Services
export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
};

// Dashboard Services
export const dashboardService = {
  getDashboard: () => api.get('/dashboard'),
  getTrends: () => api.get('/dashboard/trends'),
};

// Assessment Services
export const assessmentService = {
  createAssessment: (data) => api.post('/assessments', data),
  getAssessments: () => api.get('/assessments'),
  getAssessment: (id) => api.get(`/assessments/${id}`),
  deleteAssessment: (id) => api.delete(`/assessments/${id}`),
};

// Recommendation Services
export const recommendationService = {
  getRecommendations: (assessmentId, enhance = false) => 
    api.get(`/assessments/${assessmentId}/recommendations?enhance=${enhance}`),
};

// Assistant Services
export const assistantService = {
  chat: (message, conversationId = null) => api.post('/assistant/chat', { message, conversation_id: conversationId }),
  getConversations: () => api.get('/assistant/conversations'),
  getConversation: (id) => api.get(`/assistant/conversations/${id}`),
};

// Profile Services
export const profileService = {
  getProfile: () => api.get('/profile'),
  updateProfile: (data) => api.put('/profile', data),
  getAchievements: () => api.get('/profile/achievements'),
};

export default api;
