from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import math
from src.pipeline import CricketImpactMetric

app = FastAPI(title="Cricket Impact API")

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

# Global dataframes
impact_df = pd.DataFrame()
rolling_df = pd.DataFrame()

def classify_role(avg_bat_perf, avg_bowl_perf):
    is_bat  = avg_bat_perf  > 0.25
    is_bowl = avg_bowl_perf > 0.25
    if is_bat and is_bowl: return "Allrounder"
    if is_bat:             return "Batter"
    if is_bowl:            return "Bowler"
    return "Utility"

def clean_data(df):
    return df.fillna("").to_dict(orient="records")

@app.on_event("startup")
def load_data():
    global impact_df, rolling_df
    print(f"Loading data from {DATA_DIRECTORY}...")
    try:
        metric = CricketImpactMetric(DATA_DIRECTORY)
        impact_df, rolling_df = metric.run_pipeline()

        player_role_map = (
            impact_df.groupby("player")
            .agg(avg_bat=("perf_bat","mean"), avg_bowl=("perf_bowl","mean"))
            .apply(lambda r: classify_role(r["avg_bat"], r["avg_bowl"]), axis=1)
            .rename("role")
        )
        impact_df = impact_df.merge(player_role_map.reset_index(), on="player", how="left")
        rolling_df = rolling_df.merge(player_role_map.reset_index(), on="player", how="left")
        print(f"Data loaded perfectly. {len(impact_df)} records.")
    except Exception as e:
        print(f"Error loading data: {e}")

@app.get("/api/health")
def health():
    return {"status": "ok", "records": len(impact_df)}

@app.get("/api/tournament")
def tournament_data(season: str = "All Time", role: str = "All"):
    df = impact_df.copy()
    roll_df = rolling_df.copy()
    
    if season != "All Time" and not df.empty:
        df = df[df["season"].astype(str) == season]
    if role != "All" and not df.empty:
        df = df[df["role"] == role]
        roll_df = roll_df[roll_df["role"] == role]
        
    if df.empty:
        return {"kpis": {}, "top_rolling": [], "top_matches": [], "impact_distribution": []}

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
def leaderboards(season: str = "All Time"):
    df = impact_df.copy()
    if df.empty: return {}
    
    if season != "All Time":
        df = df[df["season"].astype(str) == season]
        
    def get_role_lb(r_name):
        df_r = df if r_name == "All" else df[df["role"] == r_name]
        if df_r.empty: return []
        lb = (df_r.groupby("player")
            .agg(Avg_IM=("Impact_Score","mean"),
                 Peak_IM=("Impact_Score","max"),
                 Matches=("match_id","nunique"),
                 Avg_Bat=("perf_bat","mean"),
                 Avg_Bowl=("perf_bowl","mean"))
            .round(2)
            .sort_values("Avg_IM", ascending=False)
            .head(15)
            .reset_index())
        return clean_data(lb)

    return {
        "All": get_role_lb("All"),
        "Batter": get_role_lb("Batter"),
        "Bowler": get_role_lb("Bowler"),
        "Allrounder": get_role_lb("Allrounder")
    }

@app.get("/api/players")
def all_players():
    if impact_df.empty: return {"players": []}
    players = sorted(impact_df["player"].dropna().unique())
    return {"players": players}

@app.get("/api/player/{player_name}")
def player_profile(player_name: str, window: str = "All Time", season: str = "All"):
    if impact_df.empty: return {"error": "No data"}
    
    player_df = impact_df[impact_df["player"] == player_name].copy()
    if player_df.empty: return {"error": "Player not found"}
        
    if "start_date" in player_df.columns:
        player_df["start_date_dt"] = pd.to_datetime(player_df["start_date"], errors="coerce")
        player_df = player_df.sort_values("start_date_dt")
        
    if window == "Last 10": player_df = player_df.tail(10)
    elif window == "Last 25": player_df = player_df.tail(25)
    elif window == "Last 50": player_df = player_df.tail(50)
    
    p_seasons = sorted(player_df["season"].astype(str).unique(), reverse=True)
    if season != "All" and season in p_seasons:
        player_df = player_df[player_df["season"].astype(str) == season]
        
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
            "Avg Context": round(float(player_df.get("Context", pd.Series([1.0])).mean()), 2),
            "Avg Situation": round(float(player_df.get("Situation", pd.Series([1.0])).mean()), 2)
        },
        "trend": clean_data(player_df),
        "available_seasons": p_seasons
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
