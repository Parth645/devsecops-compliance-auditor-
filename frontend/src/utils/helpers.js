/**
 * Utility functions for the Compliance Auditor frontend
 */

/**
 * Format a file size in bytes to human readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format a duration in seconds to human readable format
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
export const formatDuration = (seconds) => {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

/**
 * Validate if a string is a valid Git repository URL
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid Git URL
 */
export const isValidGitUrl = (url) => {
  if (!url || typeof url !== 'string') return false;
  
  const gitUrlPatterns = [
    /^https?:\/\/(www\.)?(github|gitlab|bitbucket)\.(com|org)\/[\w\-\.]+\/[\w\-\.]+(.git)?$/i,
    /^git@(github|gitlab|bitbucket)\.(com|org):[\w\-\.]+\/[\w\-\.]+(.git)?$/i,
    /^https?:\/\/[\w\-\.]+\/[\w\-\.]+\/[\w\-\.]+(.git)?$/i
  ];
  
  return gitUrlPatterns.some(pattern => pattern.test(url.trim()));
};

/**
 * Extract repository name from Git URL
 * @param {string} url - Git repository URL
 * @returns {string} Repository name
 */
export const extractRepoName = (url) => {
  if (!url) return 'Unknown Repository';
  
  try {
    const cleanUrl = url.replace('.git', '');
    const parts = cleanUrl.split('/');
    const repoName = parts[parts.length - 1];
    const ownerName = parts[parts.length - 2];
    
    return `${ownerName}/${repoName}`;
  } catch (error) {
    return 'Unknown Repository';
  }
};

/**
 * Get severity color based on severity level
 * @param {string} severity - Severity level (high, medium, low)
 * @returns {object} Color configuration
 */
export const getSeverityColor = (severity) => {
  const severityColors = {
    high: { bg: '#fef2f2', color: '#dc2626', border: '#f87171' },
    medium: { bg: '#fef3c7', color: '#d97706', border: '#fbbf24' },
    low: { bg: '#f0fdf4', color: '#166534', border: '#4ade80' },
    info: { bg: '#eff6ff', color: '#2563eb', border: '#60a5fa' }
  };
  
  return severityColors[severity?.toLowerCase()] || severityColors.info;
};

/**
 * Get file extension from filename
 * @param {string} filename - Name of the file
 * @returns {string} File extension
 */
export const getFileExtension = (filename) => {
  if (!filename || typeof filename !== 'string') return '';
  
  const lastDot = filename.lastIndexOf('.');
  return lastDot > 0 ? filename.substring(lastDot) : '';
};

/**
 * Get programming language from file extension
 * @param {string} filename - Name of the file
 * @returns {string} Programming language
 */
export const getLanguageFromFile = (filename) => {
  const ext = getFileExtension(filename).toLowerCase();
  
  const languageMap = {
    '.js': 'JavaScript',
    '.jsx': 'React',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript React',
    '.py': 'Python',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.cs': 'C#',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.json': 'JSON',
    '.xml': 'XML',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.md': 'Markdown',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.dockerfile': 'Docker',
    '.makefile': 'Makefile'
  };
  
  return languageMap[ext] || 'Unknown';
};

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Throttle function to limit function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} True if successful
 */
export const copyToClipboard = async (text) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const result = document.execCommand('copy');
      textArea.remove();
      return result;
    }
  } catch (error) {
    console.error('Failed to copy text: ', error);
    return false;
  }
};

/**
 * Download data as JSON file
 * @param {any} data - Data to download
 * @param {string} filename - Name of the file
 */
export const downloadAsJson = (data, filename) => {
  try {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `data-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to download file: ', error);
    throw error;
  }
};

/**
 * Generate a random ID
 * @param {number} length - Length of the ID
 * @returns {string} Random ID
 */
export const generateId = (length = 8) => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
};

/**
 * Check if the current environment is development
 * @returns {boolean} True if development environment
 */
export const isDevelopment = () => {
  return process.env.NODE_ENV === 'development';
};

/**
 * Log function that only logs in development
 * @param {...any} args - Arguments to log
 */
export const devLog = (...args) => {
  if (isDevelopment()) {
    console.log(...args);
  }
};

/**
 * Format a number with commas as thousands separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
export const formatNumber = (num) => {
  if (typeof num !== 'number') return '0';
  return num.toLocaleString();
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
