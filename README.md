# 🏏 Cricket Impact Metric (IM) Framework

**A Full-Stack, Context-Aware, Data-Driven Metric for Measuring True Match Output**

## 🌟 Overview

The **Cricket Impact Metric** is a state-of-the-art sports analytics dashboard designed to accurately evaluate player performance beyond traditional cricket averages. 

Traditional metrics (like batting average or raw strike rate) fail to measure *when* those runs were scored or wickets were taken. A 30-run knock in a high-pressure chase is significantly more valuable than 30 runs in a dead-rubber match. 

This project solves this by computing a robust, non-gameable **Impact Metric (IM)** that factors in:
1. **Match Context**: Required run rate, current run rate, and wickets fallen per ball.
2. **Game Situation**: Playoff/Final match multipliers and pressure-adjusted game states.
3. **Role Normalization**: Mathematically balances Batters, Bowlers, and Allrounders so a rapid 30-run knock equals a tight 2-wicket spell in the final scoring.

---

## 🏗️ Architecture

The project is built using a modern, scalable full-stack architecture:

- **Frontend (React + Vite)**: A premium, glassmorphic analytics dashboard featuring dynamic Recharts (Radar, Spline, KPI widgets) for deep metric visualization.
- **Backend (Node.js + Express)**: A fast, asynchronous proxy layer that handles API routing and protects the ML engine from being overwhelmed.
- **ML Engine (Python + FastAPI + Pandas)**: The core analytical engine that ingests hundreds of thousands of rows of ball-by-ball IPL data, normalizes the performance metrics around a mathematical median, and outputs a refined 0-99 Impact Score via a Logistic Sigmoid curve.

### 📂 Directory Structure

```text
Null_pointers/
├── ML/                  # Python Engine: DataFrame processing & Math Algorithms
│   ├── src/             # Core logic (performance, impact_model, rolling_metric)
│   ├── api_server.py    # FastAPI endpoints
│   └── requirements.txt # Python dependencies
├── backend/             # Node.js Express Proxy
│   ├── controllers/     # API request handlers
│   ├── routes/          # Express route definitions
│   ├── index.js         # Server entry point
│   └── package.json     # Node dependencies
├── frontend/            # React UI Dashboard
│   ├── src/             
│   │   ├── components/  # Reusable UI (PlayerCard, RadarChart, Navbar)
│   │   ├── pages/       # Views (Home, PlayerDashboard, Leaderboard, HeadToHead)
│   │   ├── services/    # Axios API client (api.js)
│   │   └── index.css    # Global Glassmorphic CSS Theme
│   └── package.json     # React dependencies
└── ipl_male_csv2/       # Raw IPL ball-by-ball CSV Datasets
```

---

## 🚀 How to Run Locally

You will need three terminal windows to run the full stack simultaneously.

### 1. Start the Python ML Engine
This engine parses the CSV datasets and exposes the mathematical calculations.
```bash
cd ML
pip install -r requirements.txt
python api_server.py
```
*(Runs on `http://127.0.0.1:8000`)*

### 2. Start the Node.js Backend Proxy
This server acts as the bridge between the frontend UI and the Python engine.
```bash
cd backend
npm install
node index.js
```
*(Runs on `http://127.0.0.1:5000`)*

### 3. Start the React Frontend Dashboard
This launches the beautiful, interactive user interface.
```bash
cd frontend
npm install
npm run dev
```
*(Runs on `http://localhost:5173`)*

---

## 📊 Key Features

- **Kinetic Form Gauge**: A visual speedometer showing a player's recent Impact score.
- **Role-Balanced Leaderboard**: Discover who the truly most impactful players are across all time or specific seasons, fairly ranked regardless of whether they bat or bowl.
- **Head-to-Head Radar**: Compare any two players directly against each other across multiple analytical axes (Batting, Bowling, Context, Situation).
- **Glassmorphic UI**: Beautiful dark-mode design with glowing neon accents, frosted glass cards, and staggered CSS load animations.

---

## 💡 The Math Behind the Metric

The final Impact Metric (IM) uses the following formula before normalisation:
`IM = Performance × Match_Context × Game_Situation`

Final IM is then:
- Normalized to a **0–99 scale** via logistic transformation.
- **50** = Neutral baseline (average player, average conditions).
- Aggregated over a recency-weighted rolling window of the last 10 innings to precisely track a player's current "form".
