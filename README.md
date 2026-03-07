# Cricket Impact Metric (IM)

> **Hackathon Project — Null Pointers**
>
> *"When the game gets tough… how impactful is this player?"*

A data-driven, context-aware metric that quantifies how much a cricketer truly influences the outcome of a match. Built on IPL ball-by-ball data, normalized on a **0–100 scale**, calculated over a **rolling last 10 innings**, and visualized through a full-stack web dashboard.

---

## Table of Contents

- [What is the Impact Metric?](#what-is-the-impact-metric)
- [How It Works](#how-it-works)
- [Mathematical Formulation](#mathematical-formulation)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Running Locally](#setup--running-locally)
- [API Reference](#api-reference)
- [Score Interpretation](#score-interpretation)
- [Design Choices](#design-choices)

---

## What is the Impact Metric?

Traditional cricket statistics — batting average, strike rate, economy rate — measure **how much** and **how fast** a player performs. They don't capture what actually matters:

> **Did this player change the outcome of the game?**

The Impact Metric (IM) answers this by combining three dimensions:

```
Impact = Performance × Match Context × Game Situation
```

| Dimension | What It Measures |
|---|---|
| **Performance** | Runs, wickets, economy, dot balls, boundaries |
| **Match Context** | Required run rate, wickets fallen, phase of innings, opposition quality |
| **Game Situation** | Pressure intensity, match importance (league vs playoff), current form |

A 60-run knock chasing 190 with 5 wickets down in the death overs scores far higher than the same innings in a comfortable chase — the metric quantifies exactly that difference.

---

## How It Works

The pipeline runs in 6 stages on startup:

```
Ball-by-Ball CSV Data
       │
       ▼
  1. Data Loader          — Standardizes columns, derives wickets, extras
       │
       ▼
  2. Feature Engineering  — Adds phase, CRR, RRR, wickets fallen, overs remaining
       │
       ▼
  3. Performance Score    — Batting (runs, SR, boundaries) + Bowling (wickets, economy, dots)
       │
       ▼
  4. Context & Situation  — Pressure index, BatContext, BowlContext, match importance
       │
       ▼
  5. Impact Model         — RawImpact → logistic normalization → Impact Score [0–99]
       │
       ▼
  6. Rolling Metric       — Recency-weighted average of last 10 innings → Rolling Impact [0–100]
```

---

## Mathematical Formulation

### Batting Performance

```
Run_Impact      = clip( log1p(runs) / log(80),       0,   1.5 )
SR_Impact       = clip( (strike_rate - 120) / 60 + 1, 0.5, 1.5 )
Boundary_Impact = clip( sqrt(boundaries) / 3,         0,   1.3 )

Performance_bat = (0.60 × Run_Impact + 0.25 × SR_Impact + 0.15 × Boundary_Impact)
                  × BatWorkloadFactor

BatWorkloadFactor = clip( 0.4 + 0.6 × (balls_faced / 30), 0, 1 )
```

### Bowling Performance

```
Wicket_Impact  = clip( wickets / 2,            0, 2.5 )
Economy_Impact = clip( 8.0 / economy_rate,     0, 2.0 )
Dot_Impact     = clip( dot_ball% / 0.35,       0, 2.0 )

Performance_bowl = (0.50 × Wicket_Impact + 0.30 × Economy_Impact + 0.20 × Dot_Impact)
                   × BowlWorkloadFactor

BowlWorkloadFactor = clip( sqrt(overs_bowled / 4), 0, 1 )
```

### Context & Situation

```
Pressure_Index = clip( (required_rr / current_rr) × (10 / wickets_remaining) × (20 / overs_remaining), 0, 10 )

BatContext  = clip( 1 + 0.20×(avg_req_rr/10) + 0.10×(WicketsLost/10) + 0.15×(avg_pressure/10),  0.9, 1.5 )
BowlContext = clip( 1 + 0.15×(avg_req_rr/10) + 0.20×(avg_pressure/10),                           0.9, 1.5 )

match_importance = 1.3  (Playoffs / Finals)
                   1.2  (Eliminators / Qualifiers)
                   1.0  (League stage)

Situation = clip( match_importance × (avg_pressure / 5.0), 1.0, 1.5 )
```

### Final Impact Score

```
RawImpact    = (Performance_bat × BatContext  +  Performance_bowl × BowlContext)  ×  Situation
Impact_Score = 100 / (1 + exp(−5 × (RawImpact − 1.0)))    →  clipped to [0, 99]
```

The sigmoid is anchored so that **RawImpact = 1.0 → Impact Score = 50** (the neutral baseline).

### Rolling Impact (Last 10 Innings)

```
Weights  =  [0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]
            ← oldest inning                               most recent inning →

Rolling_Impact = dot( last_10_scores, weights )   # weights always sum to 1.0

Out-of-form penalty: if all last 3 scores < 40  →  Rolling_Impact × 0.90
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Engine | Python 3.10+, NumPy, Pandas, scikit-learn |
| ML API | FastAPI + Uvicorn |
| Backend Proxy | Node.js + Express |
| Frontend | React 18 + Vite |
| Charts | Recharts, react-gauge-chart |
| Routing | React Router DOM |
| HTTP Client | Axios |

---

## Project Structure

```
Cricket-Impact-Metric/
│
├── ipl_male_csv2/              ← Ball-by-ball IPL CSV data files (required)
│
├── ML/
│   ├── api_server.py           ← FastAPI server (exposes all ML endpoints)
│   ├── requirements.txt        ← Python dependencies
│   └── src/
│       ├── pipeline.py         ← Main orchestrator (runs all stages)
│       ├── data_loader.py      ← Reads & standardizes CSV files
│       ├── feature_engineering.py  ← Adds phase, RRR, CRR, pressure features
│       ├── performance.py      ← Batting & bowling performance scores
│       ├── context_situation.py    ← Pressure index, context & situation multipliers
│       ├── impact_model.py     ← RawImpact → logistic Impact Score
│       ├── rolling_metric.py   ← Recency-weighted rolling impact (last 10 innings)
│       └── visualization.py    ← Generates charts saved to disk
│
├── backend/
│   ├── index.js                ← Express proxy server
│   ├── routes/                 ← Route definitions
│   └── controllers/            ← Request handlers
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx            ← Landing page
│   │   │   ├── Leaderboard.jsx     ← Top players ranked by Rolling Impact
│   │   │   ├── PlayerDashboard.jsx ← Per-player impact trend & stats
│   │   │   ├── HeadToHead.jsx      ← Compare two players side-by-side
│   │   │   └── About.jsx           ← Methodology explanation
│   │   ├── components/         ← Reusable UI components
│   │   ├── services/           ← Axios API service calls
│   │   └── index.css           ← Global styles
│   └── vite.config.js
│
└── README.md
```

---

## Prerequisites

Make sure you have the following installed:

- **Python 3.10 or higher** — [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** — [Download](https://nodejs.org/)
- **npm** (comes with Node.js)
- **IPL Ball-by-Ball CSV Dataset** placed inside `ipl_male_csv2/` folder

---

## Setup & Running Locally

The app has three separate services that need to run together. Open **three terminal windows**.

---

### Terminal 1 — ML API Server (Python / FastAPI)

```bash
cd ML
pip install -r requirements.txt
python api_server.py
```

The server starts at `http://localhost:8000`.
It reads all CSV files from `ipl_male_csv2/` on startup and runs the full pipeline automatically. Wait for the log message:

```
Data loaded perfectly. XXXXX records.
```

---

### Terminal 2 — Backend Proxy (Node.js / Express)

```bash
cd backend
npm install
node index.js
```

The backend starts at `http://localhost:3001`.
It acts as a proxy between the frontend and the ML API.

---

### Terminal 3 — Frontend (React / Vite)

```bash
cd frontend
npm install
npm run dev
```

The frontend starts at `http://localhost:5173`.
Open this URL in your browser to use the app.

---

### Quick Start Summary

| Step | Directory | Command | Port |
|------|-----------|---------|------|
| 1 | `ML/` | `python api_server.py` | 8000 |
| 2 | `backend/` | `node index.js` | 3001 |
| 3 | `frontend/` | `npm run dev` | 5173 |

Then open **http://localhost:5173** in your browser.

---

## API Reference

All endpoints are served by the FastAPI server at `http://localhost:8000`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check — confirms data is loaded |
| `GET` | `/api/leaderboard` | Top players ranked by average Impact Score |
| `GET` | `/api/leaderboard?season=2023` | Leaderboard filtered by IPL season |
| `GET` | `/api/players` | List of all player names |
| `GET` | `/api/player/{name}` | Full impact history for a specific player |
| `GET` | `/api/player/{name}?window=Last 10` | Player data filtered to last 10 innings |
| `GET` | `/api/tournament` | Tournament-level KPIs and top performers |
| `GET` | `/api/tournament?season=2022&role=Batter` | Filtered tournament stats |

---

## Score Interpretation

```
  0 ────── 30 ────── 50 ────── 70 ────── 85 ────── 100
  │ Below  │ Average │  Good  │  Elite  │ Legend  │
    Par
```

| Score Range | Label | What It Means |
|---|---|---|
| 0 – 30 | Below Par | Minimal match contribution |
| 30 – 50 | Average | Serviceable, below neutral |
| 50 – 70 | Good | Above neutral, match-relevant contribution |
| 70 – 85 | Elite | Significant match influence |
| 85 – 100 | Legend | Match-defining, pressure performance |

**50 is the neutral baseline** — a player with a standard performance in average match conditions scores exactly 50.

---

## Design Choices

| Choice | Why |
|---|---|
| **Log scale for runs** | Diminishing returns — 0→20 matters more than 100→120 |
| **Inverse economy rate** | Lower economy = better. `8.0 / eco` maps par (8 rpo) to 1.0 |
| **WorkloadFactor on both roles** | Prevents a 2-ball cameo or 1-over spell from inflating scores |
| **Logistic (sigmoid) normalization** | Dataset-agnostic, bounded [0–99], anchored at 50 by design |
| **Context capped at [0.9 – 1.5]** | Pressure amplifies impact — it cannot manufacture it |
| **Recency weights sum to 1.0** | Rolling Impact stays on the same scale regardless of innings count |
| **Super-over exclusion** | Innings 3+ filtered — super over stats are extreme and non-representative |
| **`is_bowler_wicket` only** | Run-outs and retired-hurt are not credited to the bowler |
| **Out-of-form penalty** | Last 3 innings all below 40 applies a 10% haircut — cold streaks are visible |
| **No real-time updates** | Computed post-match to avoid noise from incomplete innings |
