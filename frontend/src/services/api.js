import axios from 'axios';

// In development: reads from .env.local → http://127.0.0.1:5000/api/v1
// In production (Netlify): reads VITE_API_BASE_URL set in Netlify dashboard
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api/v1';

// Shared axios instance with timeout
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 90s — ML can be slow on cold start
});

// Player profile analytics
export const getPlayerImpact = async (playerName, options = {}) => {
  const { window, season } = options;
  const response = await apiClient.get(`/player/${encodeURIComponent(playerName)}`, {
    params: { window, season }
  });
  return response.data;
};

// All players list (for search dropdown)
export const getPlayersList = async () => {
  const response = await apiClient.get('/players');
  return response.data;
};

// Tournament-level KPIs and top matches
export const getTournamentData = async (season, role) => {
  const response = await apiClient.get('/tournament', {
    params: { season, role }
  });
  return response.data;
};

// Role-split leaderboard (returns { All, Batter, Bowler, Allrounder })
export const getLeaderboard = async (season) => {
  const response = await apiClient.get('/leaderboard', {
    params: { season }
  });
  return response.data;
};

// Health check — ping the backend and ML API
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};
