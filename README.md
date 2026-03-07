<![CDATA[<div align="center">

![Cricket Impact Metric – Cinematic Banner](./banner.png)

# 🏏 Cricket Impact Metric (IM)

### *When the game gets tough… how impactful is this player?*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Node.js](https://img.shields.io/badge/Node.js-Express-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Recharts](https://img.shields.io/badge/Recharts-Visualization-FF7300?style=for-the-badge)](https://recharts.org)

> A **data-driven, context-aware, non-gameable** Impact Metric that quantifies how much a cricketer truly influences the outcome of a match — normalized on a **0–100 scale**, aggregated over the **rolling last 10 innings**, updated after every match.

</div>

---

## 📌 Table of Contents

1. [What is Impact?](#-1-what-is-impact)
2. [Mathematical Formulation](#-2-mathematical-formulation)
3. [Model & Algorithm Explanation](#-3-model--algorithm-explanation)
4. [Assumptions & Design Choices](#-4-assumptions--design-choices)
5. [Sample Outputs](#-5-sample-outputs)
6. [Robustness & Edge Cases](#-6-robustness--edge-cases)
7. [Tech Stack & Architecture](#-7-tech-stack--architecture)
8. [Project Structure](#-8-project-structure)
9. [Getting Started](#-9-getting-started)
10. [Visualization](#-10-visualization)

---

## 🧠 1. What is Impact?

Traditional metrics — batting average, strike rate, economy rate — measure **how much** and **how fast** a player performs. They don't answer the only question that matters in a high-stakes match:

> **Did this player change the outcome of the game?**

Impact is the product of three orthogonal dimensions:

```
Impact = Performance × Match Context × Game Situation
```

| Dimension | What It Captures |
|---|---|
| **Performance** | Measurable output: runs, wickets, economy, dot balls, boundaries |
| **Match Context** | State of the game: RRR, wickets fallen, phase of innings, opposition quality |
| **Game Situation** | Pressure intensity, match importance (league vs. playoff), current form streak |

A 40-ball 60 chasing 180 with 5 wickets down in the death overs is categorically more impactful than a 40-ball 60 in a low-pressure 140-target. This metric quantifies exactly that gap.

---

## 📐 2. Mathematical Formulation

### 2.1 Performance Score

#### Batting (`Performance_bat`)

| Sub-score | Formula | Weight |
|---|---|---|
| `Run_Impact` | `clip(log1p(runs) / log(80), 0, 1.5)` | **60%** |
| `SR_Impact` | `clip((SR − 120) / 60 + 1, 0.5, 1.5)` | **25%** |
| `Boundary_Impact` | `clip(√boundaries / 3, 0, 1.3)` | **15%** |

```
Performance_bat = (0.60 × Run_Impact + 0.25 × SR_Impact + 0.15 × Boundary_Impact)
                  × BatWorkloadFactor
```

where:
```
BatWorkloadFactor = clip(0.4 + 0.6 × (balls_faced / 30), 0, 1)
```

> **Why log scale for runs?** Raw runs have diminishing marginal returns — the difference between scoring 0 and 20 is far more impactful than the difference between scoring 100 and 120. `log1p` captures this naturally.

#### Bowling (`Performance_bowl`)

| Sub-score | Formula | Weight |
|---|---|---|
| `Wicket_Impact` | `clip(wickets / 2, 0, 2.5)` | **50%** |
| `Economy_Impact` | `clip(8.0 / economy_rate, 0, 2.0)` | **30%** |
| `Dot_Impact` | `clip(dot_ball% / 0.35, 0, 2.0)` | **20%** |

```
Performance_bowl = (0.50 × Wicket_Impact + 0.30 × Economy_Impact + 0.20 × Dot_Impact)
                   × BowlWorkloadFactor
```

where:
```
BowlWorkloadFactor = clip(√(overs_bowled / 4), 0, 1)
```

> **Why inverse economy?** A bowler with 6.0 economy conceding 2 wickets is better than one with 12.0 economy. `8.0 / eco` maps to 1.0 at the T20 par economy of 8 rpo.

---

### 2.2 Match Context (`BatContext`, `BowlContext`)

The **Pressure Index** is computed ball-by-ball:

```
Pressure_Index = clip(
    (required_rr / current_rr) × (10 / wickets_remaining) × (20 / overs_remaining),
    0, 10
)
```

Context multipliers are derived per match:

```
BatContext  = clip(1 + 0.20×(avg_req_rr/10) + 0.10×(WicketsLost/10) + 0.15×(avg_pressure/10), 0.9, 1.5)
BowlContext = clip(1 + 0.15×(avg_req_rr/10) + 0.20×(avg_pressure/10), 0.9, 1.5)
```

Opposition strength is measured by the **bowling economy** of the opponent:

```
opponent_strength = clip(0.9 + 0.2 × (econ_max − match_economy) / (econ_max − econ_min), 0.85, 1.15)
```

> Tougher bowling attacks (lower economy) yield a higher `opponent_strength` multiplier for batting performances.

---

### 2.3 Game Situation (`Situation`)

```
match_importance = 1.3  if match_number > 56  (Knockouts / Finals)
                 = 1.2  if match_number > 50  (Eliminators / Qualifiers)
                 = 1.0  otherwise             (League stage)

Situation = clip(match_importance × (avg_pressure / 5.0), 1.0, 1.5)
```

---

### 2.4 Raw Impact → Impact Score (Logistic Normalization)

```
RawImpact    = (perf_bat × BatContext + perf_bowl × BowlContext) × Situation

Impact_Score = 100 / (1 + exp(−5 × (RawImpact − 1.0)))
Impact_Score = clip(Impact_Score, 0, 99)
```

**Anchor points:**

| RawImpact | Impact Score | Interpretation |
|---|---|---|
| 0.0 | ≈ 7 | Negligible contribution |
| 0.5 | ≈ 27 | Below par |
| **1.0** | **50** | **Neutral baseline** ✅ |
| 1.5 | ≈ 73 | Clearly above par |
| 2.0 | ≈ 88 | Elite innings |
| 2.5+ | ≈ 97 | Match-defining performance |

> **Why logistic/sigmoid?** It provides a smooth, bounded (0–99) scale with a calibrated midpoint at 50. Unlike linear normalization, it naturally compresses outliers — a superhuman 200-run knock doesn't push the score to infinity.

---

### 2.5 Rolling Impact (Last 10 Innings, Recency-Weighted)

```
weights = [0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]
          ← oldest                                               most recent →

Rolling_Impact = dot(last_10_scores, weights)   # weights sum to 1.0
```

If fewer than 10 innings are available, weights are sliced from the tail and **renormalized** so they still sum to 1.0.

**Out-of-form penalty:**
```
if last_3_scores all < 40:
    Rolling_Impact *= 0.90   # –10% haircut for cold streak
    in_poor_form = True
```

---

## ⚙️ 3. Model & Algorithm Explanation

### Pipeline Overview

```
Ball-by-Ball CSV Data
        │
        ▼
 ┌──────────────────┐
 │   Data Loader    │  Standardize columns, derive is_wicket, extras
 └──────┬───────────┘
        │
        ▼
 ┌──────────────────┐
 │ Feature Engineer │  Phase (PP/Middle/Death), CRR, RRR,
 │                  │  wickets_fallen, overs_remaining
 └──────┬───────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │         Performance Score                    │
 │  Batting: Run_Impact + SR_Impact + Boundary  │
 │  Bowling: Wicket + Economy + Dot efficiency  │
 │  Both dampened by WorkloadFactor             │
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │       Context & Situation                    │
 │  Pressure Index (ball-by-ball)               │
 │  BatContext, BowlContext, Situation          │
 │  Opposition Strength, Match Importance       │
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │           Impact Model                       │
 │  RawImpact = (bat×BatCtx + bowl×BowlCtx)×Sit│
 │  Impact_Score = Logistic(RawImpact)  [0–99] │
 └──────┬───────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │        Rolling Metric                        │
 │  Last 10 innings, recency-weighted           │
 │  Out-of-form penalty if last 3 < 40          │
 │  Rolling_Impact in [0, 100]                  │
 └──────┬───────────────────────────────────────┘
        │
        ▼
   FastAPI → Express → React Dashboard
```

### Recency Weighting Strategy

Weights increase linearly from oldest (0.04) to most recent (0.18). This ensures:
- A single brilliant performance long ago doesn't dominate current form
- A recent collapse meaningfully lowers the score
- Players returning from injury start at an honest baseline

---

## 🔧 4. Assumptions & Design Choices

| Decision | Rationale |
|---|---|
| **Super-over exclusion** | Innings 3–6 filtered out — super over stats are artificially extreme and non-representative |
| **Dot ball uses `runs_off_bat == 0`** | `total_runs` includes legbyes which inflate dot counts incorrectly |
| **`is_bowler_wicket` for wickets** | Excludes run-outs and retired-hurt — bowler didn't earn those |
| **Innings-level totals for contribution%** | Using match-level total would conflate two separate innings |
| **WorkloadFactor on both bat & bowl** | A 2-ball cameo or 1-over spell must not be treated equally to a full performance |
| **Logistic sigmoid over min-max norm** | Min-max depends on dataset extremes and can shift; logistic is dataset-agnostic |
| **Context caps [0.8 – 1.5]** | Pressure should amplify impact, never manufacture it from thin air |
| **Weights sum to 1.0 always** | Rolling Impact stays on the same 0–100 scale regardless of innings count |
| **50 = neutral baseline** | Midpoint of 0–100, anchored at RawImpact = 1.0 by sigmoid design |
| **No real-time updates** | Computed post-match to avoid noise from partial innings |

---

## 📊 5. Sample Outputs

### Example: High-Impact Innings

> **Scenario:** Virat Kohli scores 82 off 54 balls chasing 190. 3 wickets have fallen. Match is a Qualifier (match #52).

```
runs           = 82       →  Run_Impact    = log1p(82)/log(80) = 0.98
strike_rate    = 151.8    →  SR_Impact     = (151.8-120)/60+1  = 1.53 → clipped 1.5
boundaries     = 9        →  Boundary_Impact = √9/3            = 1.0

Performance_bat = 0.60×0.98 + 0.25×1.5 + 0.15×1.0 = 0.588+0.375+0.15 = 1.11
BatWorkloadFactor = clip(0.4+0.6×(54/30), 0, 1) = 1.0

avg_req_rr = 11.8,  WicketsLost = 3,  avg_pressure = 7.2
BatContext = clip(1 + 0.20×1.18 + 0.10×0.3 + 0.15×0.72, 0.9, 1.5) = 1.37

match_importance = 1.2  (Qualifier)
Situation        = clip(1.2 × 7.2/5, 1.0, 1.5) = 1.5

RawImpact    = 1.11 × 1.37 × 1.5 = 2.28
Impact_Score = 100/(1+exp(-5×(2.28-1.0))) = 95.1  ✅ Elite
```

### Example: Low-Impact Innings

> **Scenario:** Opening bat scores 12 off 18 balls in a low-pressure league game (target 140).

```
RawImpact    ≈ 0.18 × 1.0 × 1.0 = 0.18
Impact_Score ≈ 100/(1+exp(-5×(0.18-1.0))) = 19.7  ❌ Below par
```

### Leaderboard Sample

| Rank | Player | Rolling Impact | Innings | Form |
|---|---|---|---|---|
| 1 | Suryakumar Yadav | 87.4 | 10 | 🔥 Hot |
| 2 | Jasprit Bumrah | 83.1 | 9 | 🔥 Hot |
| 3 | Rohit Sharma | 76.8 | 10 | ✅ Good |
| 4 | Rashid Khan | 74.2 | 8 | ✅ Good |
| 5 | David Warner | 61.5 | 10 | ❄️ Cold |

---

## 🛡️ 6. Robustness & Edge Cases

The model handles **30+ documented edge cases** across all modules:

| Category | Edge Case | Handling |
|---|---|---|
| **Data** | Empty ball-by-ball CSV | Returns empty DataFrames with correct columns at each stage |
| **Data** | Missing columns (RRR, wickets, etc.) | Defaults: `current_rr=0.1`, `wickets_remaining=1.0`, etc. |
| **Batting** | Batter never bowled | `Performance_bowl = 0`, not `NaN` |
| **Bowling** | Bowler never batted | `Performance_bat = 0`, not `NaN` |
| **Bowling** | Economy = 0 (impossible, but guard) | `np.maximum(overs, 0.1)` prevents div-by-zero |
| **Context** | All matches same economy | `econ_max == econ_min` → denominator forced to `0.1` |
| **Context** | Match number missing | `match_importance = 1.0` |
| **Impact** | `exp()` overflow in sigmoid | `RawImpact` clipped to `[-100, 100]` before exponentiation |
| **Impact** | NaN Impact Score after sigmoid | Fallback to neutral `50` |
| **Rolling** | Player with only 1 inning | Weights sliced to length 1, renormalized → still valid |
| **Rolling** | All NaN Impact Scores for a player | Pre-filled with `50` before rolling computation |
| **Rolling** | Out-of-form penalty | Applied only if ≥3 innings exist AND all last 3 < 40 |
| **Rolling** | NaN after dot product | Fallback to `np.nanmean(window)` |
| **Super Over** | Innings 3/4/5/6 | Hard-filtered before any computation |
| **Score** | Final `Rolling_Impact` | `clip(0, 100)` unconditionally at the end |

**Anti-gaming properties:**
- `WorkloadFactor` — 3-ball cameos score near 0, not inflated
- Logistic ceiling — no score can exceed 99, regardless of RawImpact magnitude
- Out-of-form penalty — can't hide behind a single old good innings
- Context `cap [0.8–1.5]` — pressure amplifies but cannot manufacture impact
- `weights.sum() == 1.0` always — reordering match order cannot game the aggregation

---

## 🏗️ 7. Tech Stack & Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                  │
│  Home │ Leaderboard │ Player Dashboard │ Head-to-Head │ About   │
│  Recharts: Line, Bar, Gauge │ react-gauge-chart │ lucide-react  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (Axios)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND (Node.js / Express)                    │
│              Proxy layer, CORS, route management                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               ML API SERVER (Python / FastAPI)                  │
│  /api/leaderboard  /api/player/<name>  /api/head-to-head        │
│  /api/players      /api/stats/summary                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ pandas / numpy
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           IMPACT METRIC ENGINE (Python Modules)                 │
│  data_loader → feature_engineering → performance →              │
│  context_situation → impact_model → rolling_metric              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                  IPL Ball-by-Ball CSVs
                  (ipl_male_csv2/)
```

### Tech Choices

| Layer | Technology | Why |
|---|---|---|
| ML Engine | Python + NumPy + Pandas | Fast vectorized computation over ball-by-ball data |
| API Server | FastAPI + Uvicorn | Async, auto-documented, fast startup |
| Backend Proxy | Express.js | Decouples ML server from frontend; handles CORS cleanly |
| Frontend | React 18 + Vite | Fast HMR, component reusability, SPA routing |
| Charting | Recharts + react-gauge-chart | Declarative, responsive cricket visualizations |
| Styling | Vanilla CSS | No framework overhead, full design control |

---

## 📁 8. Project Structure

```
Cricket-Impact-Metric/
├── ML/
│   ├── api_server.py              # FastAPI server exposing all ML endpoints
│   ├── requirements.txt
│   └── src/
│       ├── data_loader.py         # Reads & standardizes ball-by-ball CSVs
│       ├── feature_engineering.py # Phase, RRR, CRR, wickets_fallen, overs_remaining
│       ├── performance.py         # Batting & bowling Performance sub-scores
│       ├── context_situation.py   # Pressure index, BatContext, BowlContext, Situation
│       ├── impact_model.py        # RawImpact → logistic Impact_Score [0–99]
│       ├── rolling_metric.py      # Recency-weighted Rolling Impact (last 10 innings)
│       ├── visualization.py       # Matplotlib/Plotly charts saved to disk
│       └── pipeline.py            # CricketImpactMetric class — orchestrates all steps
│
├── backend/
│   ├── index.js                   # Express proxy server
│   ├── routes/                    # Route handlers
│   └── controllers/               # Business logic
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx           # Landing page
│   │   │   ├── Leaderboard.jsx    # Top players ranked by Rolling Impact
│   │   │   ├── PlayerDashboard.jsx# Impact trend, quick stats, form indicator
│   │   │   ├── HeadToHead.jsx     # Compare two players side by side
│   │   │   └── About.jsx          # Methodology explanation
│   │   ├── components/            # Reusable UI components
│   │   ├── services/              # Axios API calls
│   │   └── index.css              # Global design system
│   └── vite.config.js
│
└── ipl_male_csv2/                 # Ball-by-ball IPL match data (CSVs)
```

---

## 🚀 9. Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- IPL ball-by-ball CSV dataset in `ipl_male_csv2/`

---

### Step 1 — Start the ML API Server

```bash
cd ML
pip install -r requirements.txt
python api_server.py
# Runs on http://localhost:8000
```

The server automatically processes all CSVs on startup and exposes:

| Endpoint | Description |
|---|---|
| `GET /api/leaderboard` | Top players by Rolling Impact |
| `GET /api/player/{name}` | Full match-by-match impact history |
| `GET /api/players` | All player names (for search/autocomplete) |
| `GET /api/head-to-head` | Compare two players |
| `GET /api/stats/summary` | Dataset-level statistics |

---

### Step 2 — Start the Backend Proxy

```bash
cd backend
npm install
node index.js
# Runs on http://localhost:3001
```

---

### Step 3 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📈 10. Visualization

The dashboard provides four views:

| View | Description |
|---|---|
| **Impact Meter** | Gauge (0–100) showing current Rolling Impact with color zones |
| **Impact Trend** | Line graph of match-by-match Impact Scores over last 10/25/50 innings |
| **Leaderboard** | Ranked table with form indicator (🔥 Hot / ✅ Good / ❄️ Cold) |
| **Head-to-Head** | Side-by-side comparison of two players across all metrics |

### Score Interpretation Guide

```
  0 ──────── 30 ──────── 50 ──────── 70 ──────── 85 ────── 100
  │   Below   │  Average  │   Good   │    Elite   │  Legend  │
  │    Par    │           │          │            │          │
  🔴          🟠          🟡         🟢           🔵
```

| Range | Label | Interpretation |
|---|---|---|
| 0 – 30 | Below Par | Minimal match impact |
| 30 – 50 | Average | Serviceable contribution |
| 50 – 70 | Good | Above neutral, match-relevant |
| 70 – 85 | Elite | Significant match influence |
| 85 – 100 | Legend | Match-defining performance |

---

## 👥 Team

**Null Pointers** — Built for the Cricket Impact Metric Hackathon Challenge

---

<div align="center">

*"Raw stats tell you what happened. Impact tells you why it mattered."*

</div>
]]>
