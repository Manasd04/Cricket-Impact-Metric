"""
context_situation.py - evaluates match pressure and tournament situation
"""
import logging
import numpy as np
import pandas as pd


def compute_context_and_situation(df):
    """
    Calculates per-match Context & Situation multipliers and per-player pressure scores.
    """
    logging.info("Evaluating Match Context & Situation constraints...")

    # guard for empty input
    if df.empty:
        logging.warning("compute_context_and_situation received empty DataFrame.")
        return pd.DataFrame(columns=[
            'match_id', 'avg_pressure', 'Context', 'Situation',
            'opponent_strength', 'match_importance', 'player', 'player_pressure'
        ])

    df = df.copy()

    # ==========================
    #  1. PRESSURE INDEX
    # ==========================

    # ensure all req columns exist with defaults before formula
    for col, default in [
        ('current_rr',       0.1),
        ('required_rr',      0.1),
        ('wickets_remaining', 1.0),
        ('overs_remaining',  0.1),
    ]:
        if col not in df.columns:
            logging.warning(f"Column '{col}' missing — using default {default}")
            df[col] = default
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default)
        df[col] = np.maximum(df[col], default if col != 'wickets_remaining' else 1.0)

    # pressure grows when:
    # - required rate is higher than current rate
    # - fewer wickets remain
    # - fewer overs remain
    df["pressure_index"] = np.clip(
        (df["required_rr"] / df["current_rr"])
        * (10 / df["wickets_remaining"])
        * (20 / df["overs_remaining"]),
        0, 10,
    )

    # ==========================
    #  2. PER MATCH PRESSURE
    # ==========================
    match_ctx = (
        df.groupby("match_id", as_index=False)
        .agg(
            avg_pressure=("pressure_index", "mean"),
            avg_req_rr=("required_rr", "mean"),
            avg_wickets_rem=("wickets_remaining", "mean")
        )
    )
    # clean up match-level pressure stats
    match_ctx["avg_pressure"] = match_ctx["avg_pressure"].fillna(0.0)
    match_ctx["avg_req_rr"] = match_ctx["avg_req_rr"].fillna(0.0)
    match_ctx["avg_wickets_rem"] = match_ctx["avg_wickets_rem"].fillna(10.0)
    match_ctx["WicketsLost"] = 10 - match_ctx["avg_wickets_rem"]

    # ==========================
    #  3. OPPOSITION STRENGTH
    # ==========================
    # dynamic strength based on how hard the opponent's bowling is to score against
    if "total_runs" in df.columns and "bowler" in df.columns:
        bowling_stats = (
            df.groupby(["match_id", "bowler"])
            .agg(
                runs_conceded=("total_runs", "sum"),
                balls=("ball", "count"),
            )
            .reset_index()
        )
        bowling_stats["overs"] = bowling_stats["balls"] / 6
        bowling_stats["economy"] = bowling_stats["runs_conceded"] / np.maximum(
            bowling_stats["overs"], 0.1
        )

        match_bowling_strength = (
            bowling_stats.groupby("match_id")["economy"]
            .mean()
            .reset_index()
            .rename(columns={"economy": "avg_bowling_economy"})
        )

        econ_min = match_bowling_strength["avg_bowling_economy"].min()
        econ_max = match_bowling_strength["avg_bowling_economy"].max()

        # normalize economy into [0.85, 1.15] strength range
        denom = max(econ_max - econ_min, 0.1)
        match_bowling_strength["opponent_strength"] = np.clip(
            0.9 + 0.2 * (econ_max - match_bowling_strength["avg_bowling_economy"]) / denom,
            0.85, 1.15
        )

        match_ctx = match_ctx.merge(
            match_bowling_strength[["match_id", "opponent_strength"]],
            on="match_id", how="left",
        )
    else:
        match_ctx["opponent_strength"] = 1.0

    match_ctx["opponent_strength"] = match_ctx["opponent_strength"].fillna(1.0)

    # ==========================
    #  4. CONTEXT
    # ==========================
    # match difficulty = (avg_pressure + baseline) * strength of opposition
    match_ctx["Context"] = np.clip(
        (match_ctx["avg_pressure"] / 8.0 + 0.8) * match_ctx["opponent_strength"],
        0.8, 1.4,
    )
    
    # BatContext: player pressure difficulty for batting
    # boosted by high req run rate, wickets lost, and general match pressure
    match_ctx["BatContext"] = 1 + 0.20 * (match_ctx["avg_req_rr"] / 10) + 0.10 * (match_ctx["WicketsLost"] / 10) + 0.15 * (match_ctx["avg_pressure"] / 10)
    match_ctx["BatContext"] = np.clip(match_ctx["BatContext"], 0.9, 1.5)
    
    # BowlContext: player pressure difficulty for bowling
    # focus on defending required rate and overall situational pressure
    match_ctx["BowlContext"] = 1 + 0.15 * (match_ctx["avg_req_rr"] / 10) + 0.20 * (match_ctx["avg_pressure"] / 10)
    match_ctx["BowlContext"] = np.clip(match_ctx["BowlContext"], 0.9, 1.5)

    # ==========================
    #  6. PER PLAYER PRESSURE
    # ==========================
    player_pressure_frames = []

    # track mean pressure experienced during a batsman's stay
    if "striker" in df.columns:
        player_pressure_frames.append(
            df.groupby(["match_id", "striker"])["pressure_index"]
            .mean().reset_index()
            .rename(columns={"striker": "player", "pressure_index": "player_pressure"})
        )

    # track mean pressure handled by a bowler during their spell
    if "bowler" in df.columns:
        player_pressure_frames.append(
            df.groupby(["match_id", "bowler"])["pressure_index"]
            .mean().reset_index()
            .rename(columns={"bowler": "player", "pressure_index": "player_pressure"})
        )

    # mix and merge to get one entry per (match, player)
    if player_pressure_frames:
        player_pressure_all = (
            pd.concat(player_pressure_frames)
            .groupby(["match_id", "player"])["player_pressure"]
            .max().reset_index()
        )
        match_ctx = match_ctx.merge(player_pressure_all, on="match_id", how="left")
    else:
        match_ctx["player"] = None
        match_ctx["player_pressure"] = np.nan

    match_ctx["player_pressure"] = match_ctx["player_pressure"].fillna(
        match_ctx["avg_pressure"]
    )

    # ==========================
    #  7. MATCH METADATA
    # ==========================
    # adds human-readable labels and season-specific match numbering
    meta_cols = ['match_id', 'season', 'start_date', 'venue', 'batting_team', 'bowling_team']
    available_meta = [c for c in meta_cols if c in df.columns]

    if available_meta:
        meta = df.drop_duplicates("match_id")[available_meta].copy()

        for col in ['season', 'start_date', 'venue', 'batting_team', 'bowling_team']:
            if col not in meta.columns:
                meta[col] = 'Unknown'
            meta[col] = meta[col].fillna('Unknown')

        meta.rename(columns={
            'batting_team': 'batting_first',
            'bowling_team': 'bowling_first'
        }, inplace=True)

        meta["start_date_dt"] = pd.to_datetime(meta["start_date"], errors="coerce")
        meta = meta.sort_values("start_date_dt")
        meta["match_number"] = meta.groupby("season").cumcount() + 1

        meta["match_label"] = (
            meta["batting_first"].astype(str)
            + " vs " + meta["bowling_first"].astype(str)
            + " | IPL " + meta["season"].astype(str)
            + " | Match " + meta["match_number"].astype(str)
        )

        keep_cols = ['match_id', 'season', 'start_date', 'venue',
                     'batting_first', 'bowling_first', 'match_label', 'match_number']
        keep_cols = [c for c in keep_cols if c in meta.columns]
        match_ctx = pd.merge(match_ctx, meta[keep_cols], on="match_id", how="left")

    # ==========================
    #  8. MATCH IMPORTANCE & SITUATION
    # ==========================
    # dynamic importance scaling (Finals > league games) based on end-of-season rank
    if 'match_number' in match_ctx.columns and 'season' in match_ctx.columns:
        total_matches_per_season = match_ctx.groupby("season")["match_number"].transform("max")
        stage_rank = total_matches_per_season - match_ctx["match_number"]
        
        conditions = [
            stage_rank == 0,  # match_number == total_matches
            stage_rank == 1,  # match_number == total_matches - 1
            stage_rank == 2,  # match_number == total_matches - 2
            stage_rank == 3   # match_number == total_matches - 3
        ]
        choices = [1.35, 1.25, 1.15, 1.20] # Final, Q2, Eliminator, Q1
        match_ctx['match_importance'] = np.select(conditions, choices, default=1.0)
    else:
        match_ctx['match_importance'] = 1.0

    # Situation represents ONLY tournament importance (group stage vs playoffs vs final)
    match_ctx["Situation"] = np.clip(
        match_ctx["match_importance"],
        1.0,
        1.35
    )

    # final global clipping to keep scales controlled
    match_ctx["Context"]   = np.clip(match_ctx["Context"],   0.8, 1.4)
    match_ctx["Situation"] = np.clip(match_ctx["Situation"], 1.0, 1.35)

    logging.info(
        f"Context computed for {match_ctx['match_id'].nunique()} matches. "
        f"Context range: [{match_ctx['Context'].min():.2f}, {match_ctx['Context'].max():.2f}] | "
        f"Situation range: [{match_ctx['Situation'].min():.2f}, {match_ctx['Situation'].max():.2f}]"
    )

    return match_ctx