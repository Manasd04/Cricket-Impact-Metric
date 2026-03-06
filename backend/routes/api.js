const express = require('express');
const router = express.Router();
const metricsController = require('../controllers/metricsController');

// Health check — useful for verifying ML API connectivity
router.get('/health', metricsController.healthCheck);

// Tournament-level analytics (KPIs, top players, match contexts)
router.get('/tournament', metricsController.getTournamentData);

// Role-split leaderboards (All / Batter / Bowler / Allrounder)
router.get('/leaderboard', metricsController.getLeaderboards);

// Full players list for search dropdowns
router.get('/players', metricsController.getAllPlayers);

// Individual player analytics profile (with optional window and season filters)
router.get('/player/:playerName', metricsController.getPlayerProfile);

module.exports = router;
