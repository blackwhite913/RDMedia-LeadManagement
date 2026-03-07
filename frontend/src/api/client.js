/**
 * API Client for RD Media Lead Management System
 * Wrapper around axios for all backend API calls
 */
import axios from 'axios';

// Base API URL
const API_BASE = 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * API methods
 */
export const api = {
  /**
   * Upload CSV file
   * @param {File} file - CSV file to upload
   * @returns {Promise} Upload result with stats
   */
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE}/upload-csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  /**
   * Get statistics
   * @returns {Promise} Stats object
   */
  getStats: async () => {
    const response = await apiClient.get('/stats');
    return response.data;
  },

  /**
   * Get paginated list of leads
   * @param {number} page - Page number (default: 1)
   * @param {number} limit - Items per page (default: 50)
   * @returns {Promise} Paginated leads
   */
  getLeads: async (page = 1, limit = 50) => {
    const response = await apiClient.get('/leads', {
      params: { page, limit },
    });
    return response.data;
  },

  /**
   * Search leads by email or company
   * @param {string} query - Search query
   * @param {number} page - Page number (default: 1)
   * @param {number} limit - Items per page (default: 50)
   * @returns {Promise} Search results
   */
  searchLeads: async (query, page = 1, limit = 50) => {
    const response = await apiClient.get('/leads/search', {
      params: { q: query, page, limit },
    });
    return response.data;
  },

  /**
   * Health check
   * @returns {Promise} Health status
   */
  healthCheck: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  /**
   * Create a new export batch
   * @param {number} percentage - Percentage of eligible leads to export
   * @param {string} batchName - Name for this export batch
   * @param {Object} filters - Optional filters (country, etc.)
   * @returns {Promise} Export result with CSV data
   */
  createExport: async (percentage, batchName, filters = {}, qualifiedOnly = true) => {
    const response = await apiClient.post('/export', null, {
      params: {
        percentage,
        batch_name: batchName,
        qualified_only: qualifiedOnly,
        ...filters,
      },
    });
    return response.data;
  },

  /**
   * Preview export counts without creating the export
   * @param {number} percentage - Percentage to preview
   * @param {Object} filters - Optional filters
   * @returns {Promise} Preview data
   */
  previewExport: async (percentage, filters = {}, qualifiedOnly = true) => {
    const response = await apiClient.get('/export/preview', {
      params: { percentage, qualified_only: qualifiedOnly, ...filters },
    });
    return response.data;
  },

  /**
   * Get export history
   * @param {number} page - Page number (default: 1)
   * @param {number} limit - Items per page (default: 20)
   * @returns {Promise} Paginated exports
   */
  getExports: async (page = 1, limit = 20) => {
    const response = await apiClient.get('/exports', {
      params: { page, limit },
    });
    return response.data;
  },

  /**
   * Get import history
   * @param {number} page - Page number (default: 1)
   * @param {number} limit - Items per page (default: 20)
   * @returns {Promise} Paginated imports
   */
  getImports: async (page = 1, limit = 20) => {
    const response = await apiClient.get('/imports', {
      params: { page, limit },
    });
    return response.data;
  },

  /**
   * Preview qualification: domains/leads count and estimated time (seconds).
   * @returns {Promise} { domains_count, leads_count, estimated_seconds }
   */
  qualifyPreview: async () => {
    const response = await apiClient.get('/qualify-leads/preview');
    return response.data;
  },

  /**
   * Run AI qualification on unscored leads (Perplexity).
   * Groups by company domain, one call per domain, updates icp_score and tags.
   * Can take several minutes for many leads; 30 min timeout.
   * @returns {Promise} { companies_evaluated, leads_updated, errors }
   */
  qualifyLeads: async () => {
    const response = await apiClient.post('/qualify-leads', null, {
      timeout: 30 * 60 * 1000, // 30 minutes for large runs
    });
    return response.data;
  },
};

export default api;
