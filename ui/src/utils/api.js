import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Health check
  getHealth: () => api.get('/health'),

  // RAG queries
  submitQuery: (query) => api.post('/query', { query }),

  // Stats endpoints
  searchPlayers: (name) => api.get(`/stats/search?query=${encodeURIComponent(name)}`),
  getLeaders: (category, limit = 10) => api.get(`/stats/leaders?category=${category}&limit=${limit}`),
  getPlayerStats: (playerId) => api.get(`/stats/player/${playerId}`),
  comparePlayers: (playerIds) => api.post('/stats/compare', { player_ids: playerIds }),

  // Job management
  submitScrapingJob: (urls) => api.post('/scrape/submit', { urls }),
  getJobStatus: (jobId) => api.get(`/scrape/status/${jobId}`),

  // Metrics and monitoring
  getMetrics: () => api.get('/metrics'),
  getSystemMetrics: () => api.get('/metrics/system'),
  getScrapingMetrics: () => api.get('/metrics/scraping'),
  getSystemStats: () => api.get('/stats/system'),
};

export default api;
