"""
api_server.py - FastAPI backend for serving impact metrics and leaderboard data
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import math
from src.pipeline import CricketImpactMetric
from src.data_loader import load_data as _load_raw
from src.rolling_metric import compute_rolling_impact

app = FastAPI(title="Cricket Impact API")

# enable cross-origin requests for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIRECTORY = os.environ.get(
    "CRICKET_DATA_DIR",
    os.path.join(BASE_DIR, "..", "ipl_male_csv2")
)

# global state caches
impact_df = pd.DataFrame()
rolling_df = pd.DataFrame()

def classify_role(avg_bat_perf, avg_bowl_perf):
    """
    Categorizes players based on their average performance contribution.
    """
    is_bat  = avg_bat_perf  > 0.25
    is_bowl = avg_bowl_perf > 0.25
    if is_bat and is_bowl: return "Allrounder"
    if is_bat:             return "Batter"
    if is_bowl:            return "Bowler"
    return "Utility"

def clean_data(df):
    """
    Strips NaNs for JSON serialization.
    """
    return df.fillna("").to_dict(orient="records")

def _build_player_team(raw_df):
    """
    Build a (match_id, player) -> team lookup from ball-by-ball data.
    """
    frames = []
    # extract teams for strikers
    if 'batting_team' in raw_df.columns and 'striker' in raw_df.columns:
        bat = (
            raw_df[['match_id', 'striker', 'batting_team']]
            .rename(columns={'striker': 'player', 'batting_team': 'team'})
            .drop_duplicates(['match_id', 'player'])
        )
        frames.append(bat)
    # extract teams for bowlers
    if 'bowling_team' in raw_df.columns and 'bowler' in raw_df.columns:
        bowl = (
            raw_df[['match_id', 'bowler', 'bowling_team']]
            .rename(columns={'bowler': 'player', 'bowling_team': 'team'})
            .drop_duplicates(['match_id', 'player'])
        )
        frames.append(bowl)
    if not frames:
        return pd.DataFrame(columns=['match_id', 'player', 'team'])
    return (
        pd.concat(frames)
        .drop_duplicates(['match_id', 'player'])
        .reset_index(drop=True)
    )

@app.on_event("startup")
def startup_load():
    """
    Initializes the in-memory data cache when the server starts.
    """
    global impact_df, rolling_df
    print(f"Loading data from {DATA_DIRECTORY}...")
    try:
        # run the full calculation pipeline
        metric = CricketImpactMetric(DATA_DIRECTORY)
        impact_df, rolling_df = metric.run_pipeline()

        # ── Role classification ────────────────────────────────────────────
        # assign primary roles based on performance distribution
        player_role_map = (
            impact_df.groupby("player")
            .agg(avg_bat=("perf_bat","mean"), avg_bowl=("perf_bowl","mean"))
            .apply(lambda r: classify_role(r["avg_bat"], r["avg_bowl"]), axis=1)
            .rename("role")
        )
        impact_df = impact_df.merge(player_role_map.reset_index(), on="player", how="left")
        rolling_df = rolling_df.merge(player_role_map.reset_index(), on="player", how="left")

        # ── Team extraction ───────────────────────────────────────────────
        # associate players with their IPL franchises
        raw_df = _load_raw(DATA_DIRECTORY)
        player_team = _build_player_team(raw_df)

        if not player_team.empty:
            impact_df = impact_df.merge(
                player_team, on=['match_id', 'player'], how='left'
            )
            impact_df['team'] = impact_df['team'].fillna('Unknown')

            # assign the most frequent team to the rolling form view
            team_mode = (
                impact_df.groupby('player')['team']
                .agg(lambda x: x.mode().iloc[0] if not x.empty else 'Unknown')
                .rename('team')
                .reset_index()
            )
            rolling_df = rolling_df.merge(team_mode, on='player', how='left')
            rolling_df['team'] = rolling_df['team'].fillna('Unknown')

        print(f"Data loaded successfully. {len(impact_df)} records | "
              f"{impact_df['team'].nunique() if 'team' in impact_df.columns else 0} teams detected.")
    except Exception as e:
        print(f"Error loading data: {e}")

@app.get("/api/health")
def health():
    """
    Basic health check for the API.
    """
    return {"status": "ok", "records": len(impact_df)}

@app.get("/api/tournament")
def tournament_data(season: str = "All Time", role: str = "All"):
    """
    Returns global tournament stats and top players for a given season or role.
    """
    df = impact_df.copy()
    if season != "All Time" and not df.empty:
        df = df[df["season"].astype(str) == season]
    if role != "All" and not df.empty:
        df = df[df["role"] == role]
        
    if df.empty:
        return {"kpis": {}, "top_rolling": [], "top_matches": [], "impact_distribution": []}

    # re-calculate rolling impact for the filtered subset
    roll_df = compute_rolling_impact(df)
    if "role" in df.columns:
        player_roles = df.groupby("player")["role"].first().reset_index()
        roll_df = roll_df.merge(player_roles, on="player", how="left")

    avg_im  = float(df["Impact_Score"].mean())
    top_im  = float(df["Impact_Score"].max())
    best_p_idx = df["Impact_Score"].idxmax()
    top_p   = df.loc[best_p_idx, "player"]
    n_90    = int((df["Impact_Score"] >= 90).sum())
    
    top10_rolling = roll_df.head(10).copy()
    top_matches = df.sort_values("Impact_Score", ascending=False).head(10).copy()
    
    return {
        "kpis": {
            "Total Matches": int(df["match_id"].nunique()),
            "Total Players": int(df["player"].nunique()),
            "Avg Impact Score": round(avg_im, 1),
            "Highest IM": round(top_im, 1),
            "Highest Player": top_p,
            "90+ IM Innings": n_90
        },
        "top_rolling": clean_data(top10_rolling[["player","Rolling_Impact","role"]]),
        "top_matches": clean_data(top_matches),
        "impact_distribution": clean_data(df[["Impact_Score"]])
    }

@app.get("/api/leaderboard")
def leaderboards(season: str = "All Time", team: str = "All"):
    """
    Returns segmented leaderboards (Batters, Bowlers, Allrounders).
    """
    df = impact_df.copy()
    if df.empty: return {}

    if season != "All Time":
        df = df[df["season"].astype(str) == season]

    if team != "All" and 'team' in df.columns:
        df = df[df["team"] == team]

    roll_df_computed = compute_rolling_impact(df)

    def get_role_lb(r_name):
        df_r = df if r_name == "All" else df[df["role"] == r_name]
        if df_r.empty: return []

        # ensure chronological sort for accurate 'recent' stats
        if "start_date" in df_r.columns:
            df_r = df_r.copy()
            df_r["_dt"] = pd.to_datetime(df_r["start_date"], errors="coerce")
            df_r = df_r.sort_values(by="_dt")

        agg_cols = dict(
            Avg_IM=("Impact_Score", "mean"),
            Peak_IM=("Impact_Score", "max"),
            Matches=("match_id", "nunique"),
            Avg_Bat=("perf_bat", "mean"),
            Avg_Bowl=("perf_bowl", "mean"),
            role=("role", "first"),
        )
        if 'team' in df_r.columns:
            agg_cols['team'] = ('team', 'first')

        lb = df_r.groupby("player").agg(**agg_cols).round(2).reset_index()

        lb = lb.merge(roll_df_computed[["player", "Rolling_Impact"]], on="player", how="left")
        lb["Rolling_Impact"] = lb["Rolling_Impact"].fillna(lb["Avg_IM"])

        # filter out outliers: minimum match requirements
        if season == "All Time":
            min_matches = 30 if team == "All" else 15
        else:
            min_matches = 3
        lb = lb[lb["Matches"] >= min_matches]

        lb = lb.sort_values("Avg_IM", ascending=False)
        return clean_data(lb)

    return {
        "All": get_role_lb("All"),
        "Batter": get_role_lb("Batter"),
        "Bowler": get_role_lb("Bowler"),
        "Allrounder": get_role_lb("Allrounder")
    }

@app.get("/api/players")
def all_players():
    """
    Returns alphabetical list of all players in the dataset.
    """
    if impact_df.empty: return {"players": []}
    players = sorted(impact_df["player"].dropna().unique())
    return {"players": players}

@app.get("/api/teams")
def all_teams():
    """
    Returns unique IPL franchise names.
    """
    if impact_df.empty or 'team' not in impact_df.columns:
        return {"teams": []}
    teams = sorted([
        t for t in impact_df["team"].dropna().unique()
        if t and t != 'Unknown'
    ])
    return {"teams": teams}

@app.get("/api/player/{player_name}")
def player_profile(player_name: str, window: str = "All Time", season: str = "All"):
    """
    Returns detailed match-by-match metrics for a single player.
    """
    if impact_df.empty: return {"error": "No data"}
    
    player_df = impact_df[impact_df["player"] == player_name].copy()
    if player_df.empty: return {"error": "Player not found"}
        
    if "start_date" in player_df.columns:
        player_df["start_date_dt"] = pd.to_datetime(player_df["start_date"], errors="coerce")
        player_df = player_df.sort_values("start_date_dt")
    
    p_seasons = sorted(player_df["season"].astype(str).unique(), reverse=True)
    
    # apply categorical filters
    if season != "All" and season in p_seasons:
        player_df = player_df[player_df["season"].astype(str) == season]
    
    # slice by recency window
    if window == "Last 10": player_df = player_df.tail(10)
    elif window == "Last 25": player_df = player_df.tail(25)
    elif window == "Last 50": player_df = player_df.tail(50)
    
    if player_df.empty:
         return {"error": "No data in selected filters"}
         
    role = player_df["role"].iloc[0] if "role" in player_df.columns else "Utility"
    
    try:
        roll = rolling_df[rolling_df["player"] == player_name]["Rolling_Impact"].values
        rolling_score = float(roll[0]) if len(roll) > 0 else float(player_df["Impact_Score"].mean())
    except:
        rolling_score = float(player_df["Impact_Score"].mean())
        
    return {
        "summary": {
            "name": player_name,
            "role": role,
            "Innings Played": int(player_df["match_id"].nunique()),
            "Avg Impact": round(float(player_df["Impact_Score"].mean()), 1),
            "Peak Impact": round(float(player_df["Impact_Score"].max()), 1),
            "Last Match IM": round(float(player_df["Impact_Score"].iloc[-1]), 1),
            "Rolling Form": round(rolling_score, 1),
            "Elite Innings": int((player_df["Impact_Score"] >= 85).sum()),
            "Avg Bat Perf": round(float(player_df["perf_bat"].mean()), 2),
            "Avg Bowl Perf": round(float(player_df["perf_bowl"].mean()), 2),
            "Avg Context": round(float(player_df[["BatContext", "BowlContext"]].mean(axis=1).mean()), 2),
            "Avg Situation": round(float(player_df.get("Situation", pd.Series([1.0])).mean()), 2)
        },
        "trend": clean_data(player_df),
        "available_seasons": p_seasons
    }

if __name__ == "__main__":
    import uvicorn
    # run uvicorn server on port 8000
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

