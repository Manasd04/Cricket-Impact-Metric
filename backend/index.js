const express = require('express');
const cors = require('cors');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 5000;

// CORS — allow all origins in development
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// Mount main API
app.use('/api/v1', apiRoutes);

// Root health ping
app.get('/', (req, res) => {
    res.json({
        service: 'Cricket Impact Metric — Backend',
        version: '1.0.0',
        status: 'running',
        endpoints: {
            health:      'GET /api/v1/health',
            tournament:  'GET /api/v1/tournament?season=&role=',
            leaderboard: 'GET /api/v1/leaderboard?season=',
            players:     'GET /api/v1/players',
            player:      'GET /api/v1/player/:name?window=&season=',
        }
    });
});

// Global error handler (catches unhandled errors from routes)
app.use((err, req, res, next) => {
    console.error('[Unhandled Error]', err.stack);
    res.status(500).json({ error: 'Internal server error', detail: err.message });
});

app.listen(PORT, () => {
    console.log(`\n🏏 Cricket Impact Metric Backend`);
    console.log(`✅ Server running at: http://localhost:${PORT}`);
    console.log(`🔗 ML API proxied at: http://127.0.0.1:8000/api`);
    console.log(`📡 Endpoints exposed under: /api/v1\n`);
});
