import logging
import numpy as np
import pandas as pd


def compute_context_and_situation(df):
    """
    Calculates per-match Context & Situation multipliers, plus per-player
    pressure scores used in the impact model.

    Improvements included:
    • Caps pressure_index at 10 to prevent end-of-innings explosions.
    • Calculates per-player pressure instead of only per-match pressure.
    • Adds opponent_strength factor (required by hackathon problem).
    • Safe handling for divisions and missing columns.
    • Extracts metadata (venue, teams, season).
    """

    logging.info("Evaluating Match Context & Situation constraints...")

    df = df.copy()

    # ------------------------------------------------------------------
    # 1. PRESSURE INDEX
    # ------------------------------------------------------------------
    # Formula:
    # (RequiredRR / CurrentRR) * (10 / WicketsRemaining) * (20 / OversRemaining)

    df["current_rr"] = np.maximum(df.get("current_rr", 0.1), 0.1)
    df["required_rr"] = np.maximum(df.get("required_rr", 0.1), 0.1)
    df["wickets_remaining"] = np.maximum(df.get("wickets_remaining", 1), 1)
    df["overs_remaining"] = np.maximum(df.get("overs_remaining", 0.1), 0.1)

    df["pressure_index"] = np.clip(
        (df["required_rr"] / df["current_rr"])
        * (10 / df["wickets_remaining"])
        * (20 / df["overs_remaining"]),
        0,
        10,
    )

    # ------------------------------------------------------------------
    # 2. PER MATCH PRESSURE
    # ------------------------------------------------------------------

    match_ctx = (
        df.groupby("match_id")
        .agg(avg_pressure=("pressure_index", "mean"))
        .reset_index()
    )

    # ------------------------------------------------------------------
    # 3. OPPOSITION STRENGTH
    # ------------------------------------------------------------------
    # Estimate bowling quality from economy rate in that match

    if "total_runs" in df.columns:

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

        # Convert economy → strength multiplier
        econ_min = match_bowling_strength["avg_bowling_economy"].min()
        econ_max = match_bowling_strength["avg_bowling_economy"].max()

        match_bowling_strength["opponent_strength"] = (
            (econ_max - match_bowling_strength["avg_bowling_economy"])
            / max((econ_max - econ_min), 0.1)
        )

        # Scale to reasonable multiplier range
        match_bowling_strength["opponent_strength"] = (
            0.9 + 0.2 * match_bowling_strength["opponent_strength"]
        )

        match_ctx = match_ctx.merge(
            match_bowling_strength[["match_id", "opponent_strength"]],
            on="match_id",
            how="left",
        )

    else:
        match_ctx["opponent_strength"] = 1.0

    match_ctx["opponent_strength"] = match_ctx["opponent_strength"].fillna(1.0)

    # ------------------------------------------------------------------
    # 4. CONTEXT
    # ------------------------------------------------------------------

    match_ctx["Context"] = np.clip(
        (match_ctx["avg_pressure"] / 8.0 + 0.8)
        * match_ctx["opponent_strength"],
        0.8,
        1.4,
    )

    # ------------------------------------------------------------------
    # 5. SITUATION
    # ------------------------------------------------------------------

    match_importance = 1.0

    match_ctx["Situation"] = np.clip(
        match_importance * (match_ctx["avg_pressure"] / 5.0),
        1.0,
        1.5,
    )

    # ------------------------------------------------------------------
    # 6. PER PLAYER PRESSURE
    # ------------------------------------------------------------------

    if "striker" in df.columns:

        player_pressure_bat = (
            df.groupby(["match_id", "striker"])["pressure_index"]
            .mean()
            .reset_index()
            .rename(columns={"striker": "player", "pressure_index": "player_pressure"})
        )

    else:
        player_pressure_bat = pd.DataFrame(
            columns=["match_id", "player", "player_pressure"]
        )

    if "bowler" in df.columns:

        player_pressure_bowl = (
            df.groupby(["match_id", "bowler"])["pressure_index"]
            .mean()
            .reset_index()
            .rename(columns={"bowler": "player", "pressure_index": "player_pressure"})
        )

    else:
        player_pressure_bowl = pd.DataFrame(
            columns=["match_id", "player", "player_pressure"]
        )

    player_pressure_all = (
        pd.concat([player_pressure_bat, player_pressure_bowl])
        .groupby(["match_id", "player"])["player_pressure"]
        .max()
        .reset_index()
    )

    match_ctx = match_ctx.merge(player_pressure_all, on="match_id", how="left")

    # ------------------------------------------------------------------
    # 7. MATCH META DATA
    # ------------------------------------------------------------------

    meta = df.drop_duplicates("match_id").copy()

    meta["season"] = meta["season"] if "season" in meta.columns else "Unknown"
    meta["start_date"] = meta["start_date"] if "start_date" in meta.columns else "Unknown"
    meta["venue"] = meta["venue"] if "venue" in meta.columns else "Unknown"

    meta["batting_first"] = (
        meta["batting_team"] if "batting_team" in meta.columns else "Unknown"
    )
    meta["bowling_first"] = (
        meta["bowling_team"] if "bowling_team" in meta.columns else "Unknown"
    )

    meta["start_date_dt"] = pd.to_datetime(meta["start_date"], errors="coerce")

    meta = meta.sort_values("start_date_dt")

    meta["match_number"] = meta.groupby("season").cumcount() + 1

    meta["match_label"] = (
        meta["batting_first"].astype(str)
        + " vs "
        + meta["bowling_first"].astype(str)
        + " | IPL "
        + meta["season"].astype(str)
        + " | Match "
        + meta["match_number"].astype(str)
    )

    meta = meta[
        [
            "match_id",
            "season",
            "start_date",
            "venue",
            "batting_first",
            "bowling_first",
            "match_label",
            "match_number",
        ]
    ]

    # ------------------------------------------------------------------
    # 8. FINAL MERGE
    # ------------------------------------------------------------------

    match_ctx = pd.merge(match_ctx, meta, on="match_id", how="left")

    logging.info(
        f"Context computed for {match_ctx['match_id'].nunique()} matches. "
        f"Avg pressure range: [{match_ctx['avg_pressure'].min():.2f}, "
        f"{match_ctx['avg_pressure'].max():.2f}]"
    )

    return match_ctx