import logging
import numpy as np
import pandas as pd


def compute_context_and_situation(df):
    """
    Calculates per-match Context & Situation multipliers and per-player
    pressure scores used in the impact model.

    Edge Cases Handled:
    1. Empty DataFrame input — returns minimal valid structure immediately.
    2. Missing pressure-related columns — filled with safe defaults.
    3. Division-by-zero in pressure_index — clipped to [0, 10].
    4. Empty match groups after groupby — handled via fillna chain.
    5. Economy-rate division by zero — uses np.maximum(..., 0.1).
    6. econ_min == econ_max (all same economy) — max denominator guard.
    7. match_number missing — match_importance defaults to 1.0.
    8. Missing season/venue/team columns — filled with 'Unknown'.
    9. All NaN in opponent_strength — filled with 1.0 (neutral).
    10. Context/Situation always clipped to defined range before returning.
    """
    logging.info("Evaluating Match Context & Situation constraints...")

    # ── Guard: empty input ─────────────────────────────────────────────────────
    if df.empty:
        logging.warning("compute_context_and_situation received empty DataFrame.")
        return pd.DataFrame(columns=[
            'match_id', 'avg_pressure', 'Context', 'Situation',
            'opponent_strength', 'match_importance', 'player', 'player_pressure'
        ])

    df = df.copy()

    # ── 1. PRESSURE INDEX ─────────────────────────────────────────────────────
    # FIX 2: ensure all pressure columns exist with safe defaults before use
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

    # FIX 3: clip pressure_index to [0, 10] to prevent end-of-innings explosion
    df["pressure_index"] = np.clip(
        (df["required_rr"] / df["current_rr"])
        * (10 / df["wickets_remaining"])
        * (20 / df["overs_remaining"]),
        0, 10,
    )

    # ── 2. PER MATCH PRESSURE ─────────────────────────────────────────────────
    match_ctx = (
        df.groupby("match_id", as_index=False)
        .agg(
            avg_pressure=("pressure_index", "mean"),
            avg_req_rr=("required_rr", "mean"),
            avg_wickets_rem=("wickets_remaining", "mean")
        )
    )
    # FIX 4: guard NaN avg_pressure (all-NaN group)
    match_ctx["avg_pressure"] = match_ctx["avg_pressure"].fillna(0.0)
    match_ctx["avg_req_rr"] = match_ctx["avg_req_rr"].fillna(0.0)
    match_ctx["avg_wickets_rem"] = match_ctx["avg_wickets_rem"].fillna(10.0)
    match_ctx["WicketsLost"] = 10 - match_ctx["avg_wickets_rem"]

    # ── 3. OPPOSITION STRENGTH ────────────────────────────────────────────────
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
        # FIX 5: guard overs=0
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

        # FIX 6: guard when all economies are identical (econ_max == econ_min)
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

    # FIX 9: fill NaN opponent_strength with neutral 1.0
    match_ctx["opponent_strength"] = match_ctx["opponent_strength"].fillna(1.0)

    # ── 4. CONTEXT ────────────────────────────────────────────────────────────
    match_ctx["Context"] = np.clip(
        (match_ctx["avg_pressure"] / 8.0 + 0.8) * match_ctx["opponent_strength"],
        0.8, 1.4,
    )
    
    # NEW: BatContext and BowlContext
    match_ctx["BatContext"] = 1 + 0.20 * (match_ctx["avg_req_rr"] / 10) + 0.10 * (match_ctx["WicketsLost"] / 10) + 0.15 * (match_ctx["avg_pressure"] / 10)
    match_ctx["BatContext"] = np.clip(match_ctx["BatContext"], 0.9, 1.5)
    
    match_ctx["BowlContext"] = 1 + 0.15 * (match_ctx["avg_req_rr"] / 10) + 0.20 * (match_ctx["avg_pressure"] / 10)
    match_ctx["BowlContext"] = np.clip(match_ctx["BowlContext"], 0.9, 1.5)

    # ── 5. SITUATION (match importance × pressure tier) ───────────────────────
    # FIX 7: match_importance from match_number (later = higher stakes)
    # IPL: ~50 league games, then Eliminator/QF/SF/Final
    if 'match_number' in match_ctx.columns:
        match_ctx['match_importance'] = np.where(
            match_ctx['match_number'] > 56, 1.3,
            np.where(match_ctx['match_number'] > 50, 1.2, 1.0)
        )
    else:
        match_ctx['match_importance'] = 1.0

    match_ctx["Situation"] = np.clip(
        match_ctx['match_importance'] * (match_ctx["avg_pressure"] / 5.0),
        1.0, 1.5,
    )

    # FIX 10: final clip on Context and Situation
    match_ctx["Context"]   = np.clip(match_ctx["Context"],   0.8, 1.4)
    match_ctx["Situation"] = np.clip(match_ctx["Situation"], 1.0, 1.5)

    # ── 6. PER PLAYER PRESSURE ────────────────────────────────────────────────
    player_pressure_frames = []

    if "striker" in df.columns:
        player_pressure_frames.append(
            df.groupby(["match_id", "striker"])["pressure_index"]
            .mean().reset_index()
            .rename(columns={"striker": "player", "pressure_index": "player_pressure"})
        )

    if "bowler" in df.columns:
        player_pressure_frames.append(
            df.groupby(["match_id", "bowler"])["pressure_index"]
            .mean().reset_index()
            .rename(columns={"bowler": "player", "pressure_index": "player_pressure"})
        )

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

    # ── 7. MATCH METADATA ─────────────────────────────────────────────────────
    meta_cols = ['match_id', 'season', 'start_date', 'venue', 'batting_team', 'bowling_team']
    available_meta = [c for c in meta_cols if c in df.columns]

    if available_meta:
        meta = df.drop_duplicates("match_id")[available_meta].copy()

        # FIX 8: fill missing metadata columns
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

    logging.info(
        f"Context computed for {match_ctx['match_id'].nunique()} matches. "
        f"Context range: [{match_ctx['Context'].min():.2f}, {match_ctx['Context'].max():.2f}] | "
        f"Situation range: [{match_ctx['Situation'].min():.2f}, {match_ctx['Situation'].max():.2f}]"
    )

    return match_ctx