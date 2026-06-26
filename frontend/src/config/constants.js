// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Application Configuration
export const APP_CONFIG = {
  APP_NAME: 'Compliance Auditor',
  VERSION: '1.0.0',
  DESCRIPTION: 'Automated Git repository compliance and security scanning tool',
  GITHUB_URL: 'https://github.com',
  DOCS_URL: '/docs',
};

// UI Configuration
export const UI_CONFIG = {
  THEME: {
    PRIMARY_COLOR: '#3b82f6',
    SECONDARY_COLOR: '#64748b',
    SUCCESS_COLOR: '#22c55e',
    WARNING_COLOR: '#f59e0b',
    ERROR_COLOR: '#dc2626',
    BACKGROUND_COLOR: '#f8fafc',
  },
  BREAKPOINTS: {
    MOBILE: '768px',
    TABLET: '1024px',
    DESKTOP: '1200px',
  },
  ANIMATION: {
    DURATION: '0.2s',
    EASING: 'ease',
  },
};

// Scan Configuration
export const SCAN_CONFIG = {
  DEFAULT_BRANCH: 'main',
  ANALYSIS_DEPTHS: [
    { value: 'basic', label: 'Basic' },
    { value: 'detailed', label: 'Detailed' },
    { value: 'full', label: 'Full' },
  ],
  SUPPORTED_PROVIDERS: [
    { id: 'github', name: 'GitHub', url: 'github.com' },
    { id: 'gitlab', name: 'GitLab', url: 'gitlab.com' },
    { id: 'bitbucket', name: 'Bitbucket', url: 'bitbucket.org' },
  ],
  MAX_FILE_DISPLAY: 20,
  MAX_HISTORY_ITEMS: 50,
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
  INVALID_URL: 'Please enter a valid Git repository URL.',
  SCAN_FAILED: 'Repository scan failed. Please check the URL and try again.',
  LOAD_FAILED: 'Failed to load data. Please refresh the page.',
  EXPORT_FAILED: 'Failed to export results. Please try again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  SCAN_COMPLETED: 'Repository scan completed successfully!',
  EXPORT_COMPLETED: 'Results exported successfully!',
  COPY_COMPLETED: 'URL copied to clipboard!',
};
