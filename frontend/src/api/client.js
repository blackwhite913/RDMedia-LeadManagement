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
  createExport: async (percentage, batchName, filters = {}) => {
    const response = await apiClient.post('/export', null, {
      params: {
        percentage,
        batch_name: batchName,
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
  previewExport: async (percentage, filters = {}) => {
    const response = await apiClient.get('/export/preview', {
      params: { percentage, ...filters },
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
   * Delete one lead by ID
   * @param {number} id - Lead ID
   * @returns {Promise} Deletion response
   */
  deleteLead: async (id) => {
    const response = await apiClient.delete(`/leads/${id}`);
    return response.data;
  },

  /**
   * Delete multiple leads by IDs
   * @param {number[]} ids - Lead IDs
   * @returns {Promise} Deletion response
   */
  deleteLeadsBulk: async (ids) => {
    const response = await apiClient.post('/leads/delete-bulk', { ids });
    return response.data;
  },

};

export default api;
