const axios = require('axios');

const ML_API_URL = 'http://127.0.0.1:8000/api';

// Shared axios instance with a timeout to prevent hanging requests
const mlClient = axios.create({
    baseURL: ML_API_URL,
    timeout: 60000, // 60s — data processing can take time on first load
});

// Helper: forward ML errors cleanly
const handleError = (res, error, context) => {
    const status = error.response?.status || 500;
    const detail = error.response?.data?.detail || error.message || 'Unknown error';
    console.error(`[${context}] Error:`, detail);
    res.status(status).json({ error: `ML service error: ${detail}` });
};

// GET /api/v1/tournament?season=&role=
exports.getTournamentData = async (req, res) => {
    try {
        const { season, role } = req.query;
        const response = await mlClient.get('/tournament', {
            params: { season, role }
        });
        res.json(response.data);
    } catch (error) {
        handleError(res, error, 'getTournamentData');
    }
};

// GET /api/v1/leaderboard?season=
exports.getLeaderboards = async (req, res) => {
    try {
        const { season } = req.query;
        const response = await mlClient.get('/leaderboard', {
            params: { season }
        });
        res.json(response.data);
    } catch (error) {
        handleError(res, error, 'getLeaderboards');
    }
};

// GET /api/v1/players
exports.getAllPlayers = async (req, res) => {
    try {
        const response = await mlClient.get('/players');
        res.json(response.data);
    } catch (error) {
        handleError(res, error, 'getAllPlayers');
    }
};

// GET /api/v1/player/:playerName?window=&season=
exports.getPlayerProfile = async (req, res) => {
    try {
        const { playerName } = req.params;
        const { window, season } = req.query;

        // Decode in case name was double-encoded by the frontend
        const decodedName = decodeURIComponent(playerName);

        const response = await mlClient.get(`/player/${encodeURIComponent(decodedName)}`, {
            params: { window, season }
        });
        res.json(response.data);
    } catch (error) {
        handleError(res, error, 'getPlayerProfile');
    }
};

// GET /api/v1/health - Check if ML API is reachable
exports.healthCheck = async (req, res) => {
    try {
        const response = await mlClient.get('/health', { timeout: 5000 });
        res.json({
            backend: 'ok',
            ml_api: 'ok',
            ml_records: response.data?.records ?? 0,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(503).json({
            backend: 'ok',
            ml_api: 'unreachable',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
};
