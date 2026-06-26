import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8001',  // Updated to port 8001
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API endpoints
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Get API info
  getApiInfo: () => api.get('/'),

  // Git repository scanning
  scanRepository: (repoUrl) => api.get(`/git-scan?git_repo_url=${encodeURIComponent(repoUrl)}`),

  // Detailed repository scanning
  scanRepositoryDetailed: (data) => api.post('/git-scan-detailed', data),

  // AI-powered repository scanning
  aiScanRepository: (data) => api.post('/ai-scan', data),

  // Get scan history
  getScanHistory: (limit = 10) => api.get(`/scan-history?limit=${limit}`),

  // Get compliance rules
  getComplianceRules: () => api.get('/compliance-rules'),
};

export default api;
