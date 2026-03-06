import logging
import numpy as np
import pandas as pd


def calculate_raw_and_final_impact(bat_df, bowl_df, match_context):
    """
    Merges batting + bowling performance with match context and computes
    the final logistic-normalized Impact Score (0-99) per player per match.

    Changes from original:
    1. CRITICAL — match_context now has a 'player' column (per-player pressure
       from updated context_situation.py). Merging on match_id only causes a
       21.5x row explosion (25,018 rows → 538,034). Fixed by splitting
       match_context into a match-level part (1 row per match) and a
       player-level part (1 row per match+player) and merging each separately.
    2. NaN guard on Context/Situation before RawImpact — if any match has no
       context data, fallback to neutral values (Context=1.0, Situation=1.0)
       so the pipeline never produces NaN Impact_Scores.
    3. np.exp overflow protection via clipping RawImpact before the sigmoid —
       defensive guard for any future edge cases.
    4. player_pressure merged in as an informational column (useful for app.py
       pressure-vs-impact scatter chart) without affecting the core formula.
    5. Cleaner column selection and logging with row/score diagnostics.
    """
    logging.info("Applying Logistic Scaling to Final Impact Scores...")

    # ── Step 1: Rename bat/bowl keys to 'player' ───────────────────────────
    b = (bat_df[['match_id', 'batsman', 'Performance_bat']]
         .rename(columns={'batsman': 'player', 'Performance_bat': 'perf_bat'}))

    bw = (bowl_df[['match_id', 'bowler', 'Performance_bowl']]
          .rename(columns={'bowler': 'player', 'Performance_bowl': 'perf_bowl'}))

    # ── Step 2: Outer merge bat + bowl on match_id + player ────────────────
    # Outer join so pure batters (no bowling) and pure bowlers (no batting)
    # both appear. fillna(0) means missing contribution = 0, not NaN.
    total_df = pd.merge(b, bw, on=['match_id', 'player'], how='outer').fillna(0)
    total_df['Total_Performance'] = total_df['perf_bat'] + total_df['perf_bowl']

    # ── Step 3: Split match_context into two parts ─────────────────────────
    # context_situation.py now returns one row per (match_id, player) because
    # it computes per-player pressure. Merging the whole DataFrame on match_id
    # alone would multiply every player row by ~22 rows (one per player in that
    # match) → 538,034 rows instead of 25,018. Verified with real data.
    #
    # Fix: extract match-level columns (1 row per match) and player-level
    # pressure (1 row per match+player) separately, then merge each correctly.

    # Match-level columns: identical for every player in a match
    match_level_cols = [
        'match_id', 'avg_pressure', 'Context', 'Situation',
        'season', 'start_date', 'venue',
        'batting_first', 'bowling_first',
        'match_label', 'match_number'
    ]
    # Keep only columns that actually exist (guards against older context output)
    match_level_cols = [c for c in match_level_cols if c in match_context.columns]

    match_level = (match_context[match_level_cols]
                   .drop_duplicates(subset='match_id')
                   .reset_index(drop=True))

    # Merge match-level: match_id only → exactly 1 row per player row (no explosion)
    total_df = total_df.merge(match_level, on='match_id', how='left')

    # Player-level pressure (optional but useful for scatter charts in app.py)
    if 'player' in match_context.columns and 'player_pressure' in match_context.columns:
        player_pressure = match_context[['match_id', 'player', 'player_pressure']].copy()
        total_df = total_df.merge(player_pressure, on=['match_id', 'player'], how='left')

    # ── Step 4: NaN guard on Context and Situation ─────────────────────────
    # If a match somehow has no context data (e.g. truncated file), fallback to
    # neutral multipliers so Impact_Score is still computed (not NaN).
    # Context neutral = 1.0 (midpoint between 0.8 and 1.4)
    # Situation neutral = 1.0 (minimum, no pressure boost)
    if 'Context' in total_df.columns:
        total_df['Context'] = total_df['Context'].fillna(1.0)
    else:
        total_df['Context'] = 1.0

    if 'Situation' in total_df.columns:
        total_df['Situation'] = total_df['Situation'].fillna(1.0)
    else:
        total_df['Situation'] = 1.0

    # ── Step 5: RawImpact = TotalPerformance × Context × Situation ─────────
    total_df['RawImpact'] = (
        total_df['Total_Performance']
        * total_df['Context']
        * total_df['Situation']
    )

    # ── Step 6: Logistic normalization → Impact Score [0, 99] ──────────────
    # Formula: 100 / (1 + exp(-5 × (RawImpact - 1)))
    # Centred at RawImpact=1.0 → Impact_Score=50 (neutral baseline)
    # Steepness=5 → score rises sharply above 1.0, falls sharply below it
    #
    # Overflow guard: clip RawImpact to [-100, 100] before sigmoid.
    # exp(-5 * (-100 - 1)) = exp(505) → float64 overflow → inf → score = 0.
    # clip prevents this. Values beyond ±100 are already at score limits anyway.
    raw_clipped = np.clip(total_df['RawImpact'], -100, 100)
    total_df['Impact_Score'] = 100 / (1 + np.exp(-5 * (raw_clipped - 1.0)))
    total_df['Impact_Score'] = np.clip(total_df['Impact_Score'], 0, 99)

    # ── Diagnostics ────────────────────────────────────────────────────────
    n_players  = total_df['player'].nunique()
    n_matches  = total_df['match_id'].nunique()
    n_elite    = (total_df['Impact_Score'] >= 85).sum()
    nan_scores = total_df['Impact_Score'].isna().sum()

    logging.info(
        f"Impact computed: {len(total_df)} performances | "
        f"{n_players} players | {n_matches} matches | "
        f"{n_elite} elite innings (≥85) | "
        f"{nan_scores} NaN scores (should be 0)"
    )

    return total_df