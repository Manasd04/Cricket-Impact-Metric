import logging
import numpy as np
import pandas as pd


def calculate_raw_and_final_impact(bat_df, bowl_df, match_context):
    """
    Merges batting + bowling performance with match context and computes
    the final logistic-normalized Impact Score (0-99) per player per match.

    Edge Cases Handled:
    1. Empty bat_df or bowl_df — outer merge still produces valid output.
    2. Empty match_context — fills Context/Situation with neutral defaults.
    3. match_context player column causes row explosion — split match-level vs player-level.
    4. Missing Context/Situation columns — default to neutral (1.0 / 1.0).
    5. NaN in Context or Situation — fillna(1.0) before multiplication.
    6. Total_Performance = NaN — fillna(0) before RawImpact.
    7. np.exp overflow in sigmoid — RawImpact clipped to [-100, 100].
    8. NaN Impact_Score after sigmoid — fillna(50) neutral baseline fallback.
    9. All-NaN player merge — player_pressure filled with match avg_pressure.
    10. Empty total_df after merge — returns empty DataFrame with correct columns.
    """
    logging.info("Applying Logistic Scaling to Final Impact Scores...")

    # ── Guard: empty inputs ───────────────────────────────────────────────────
    if bat_df.empty and bowl_df.empty:
        logging.warning("Both bat_df and bowl_df are empty. Returning empty impact_df.")
        return pd.DataFrame(columns=['match_id', 'player', 'Impact_Score'])

    # ── Step 1: Rename bat/bowl keys to 'player' ──────────────────────────────
    b  = pd.DataFrame(columns=['match_id', 'player', 'perf_bat'])
    bw = pd.DataFrame(columns=['match_id', 'player', 'perf_bowl'])

    if not bat_df.empty and 'batsman' in bat_df.columns:
        b = (bat_df[['match_id', 'batsman', 'Performance_bat']]
             .rename(columns={'batsman': 'player', 'Performance_bat': 'perf_bat'})
             .copy())

    if not bowl_df.empty and 'bowler' in bowl_df.columns:
        bw = (bowl_df[['match_id', 'bowler', 'Performance_bowl']]
              .rename(columns={'bowler': 'player', 'Performance_bowl': 'perf_bowl'})
              .copy())

    # ── Step 2: Outer merge bat + bowl ────────────────────────────────────────
    # FIX 1: outer join so pure batters and pure bowlers both appear
    total_df = pd.merge(b, bw, on=['match_id', 'player'], how='outer').fillna(0)

    # FIX 6: guard NaN Total_Performance
    total_df['Total_Performance'] = (
        total_df['perf_bat'].fillna(0) + total_df['perf_bowl'].fillna(0)
    )

    # ── Guard: empty after merge ──────────────────────────────────────────────
    if total_df.empty:
        logging.warning("total_df empty after bat/bowl merge.")
        return pd.DataFrame(columns=['match_id', 'player', 'Impact_Score'])

    # ── Step 3: Split match_context → match-level and player-level ────────────
    # FIX 3: merging full match_context on match_id alone creates row explosion
    # when match_context has 1 row per (match_id, player). Split into two parts.

    if match_context is None or match_context.empty:
        # FIX 2: no context data → neutral defaults
        logging.warning("match_context is empty. Using neutral Contexts, Situation=1.0.")
        total_df['BatContext'] = 1.0
        total_df['BowlContext'] = 1.0
        total_df['Situation'] = 1.0
    else:
        match_level_cols = [
            'match_id', 'avg_pressure', 'Context', 'BatContext', 'BowlContext', 'Situation',
            'opponent_strength', 'match_importance',
            'season', 'start_date', 'venue',
            'batting_first', 'bowling_first',
            'match_label', 'match_number'
        ]
        match_level_cols = [c for c in match_level_cols if c in match_context.columns]

        match_level = (match_context[match_level_cols]
                       .drop_duplicates(subset='match_id')
                       .reset_index(drop=True))

        total_df = total_df.merge(match_level, on='match_id', how='left')

        # Merge per-player pressure separately
        if 'player' in match_context.columns and 'player_pressure' in match_context.columns:
            player_pressure = match_context[['match_id', 'player', 'player_pressure']].dropna(subset=['player'])
            total_df = total_df.merge(player_pressure, on=['match_id', 'player'], how='left')

    # ── Step 4: NaN guards on Context and Situation ───────────────────────────
    # FIX 4 & 5: ensure multipliers always exist and are not NaN
    if 'BatContext' not in total_df.columns:
        total_df['BatContext'] = 1.0
    else:
        total_df['BatContext'] = total_df['BatContext'].fillna(1.0)

    if 'BowlContext' not in total_df.columns:
        total_df['BowlContext'] = 1.0
    else:
        total_df['BowlContext'] = total_df['BowlContext'].fillna(1.0)

    if 'Context' not in total_df.columns:
        total_df['Context'] = 1.0
    else:
        total_df['Context'] = total_df['Context'].fillna(1.0)

    if 'Situation' not in total_df.columns:
        total_df['Situation'] = 1.0
    else:
        total_df['Situation'] = total_df['Situation'].fillna(1.0)

    # Clip to valid ranges before multiplication
    total_df['BatContext']  = np.clip(total_df['BatContext'],  0.9, 1.5)
    total_df['BowlContext'] = np.clip(total_df['BowlContext'], 0.9, 1.5)
    total_df['Context']     = np.clip(total_df['Context'],     0.8, 1.4)
    total_df['Situation']   = np.clip(total_df['Situation'],   1.0, 1.5)

    # ── Step 5: RawImpact ─────────────────────────────────────────────────────
    total_df['RawImpact'] = (
        (total_df['perf_bat'] * total_df['BatContext'])
        + (total_df['perf_bowl'] * total_df['BowlContext'])
    ) * total_df['Situation']
    # FIX 6: guard any remaining NaN in RawImpact
    total_df['RawImpact'] = total_df['RawImpact'].fillna(0)

    # ── Step 6: Logistic normalization → Impact Score [0, 99] ─────────────────
    # FIX 7: clip before sigmoid to prevent float64 overflow
    raw_clipped = np.clip(total_df['RawImpact'], -100, 100)
    total_df['Impact_Score'] = 100 / (1 + np.exp(-5 * (raw_clipped - 1.0)))
    total_df['Impact_Score'] = np.clip(total_df['Impact_Score'], 0, 99)

    # FIX 8: NaN fallback (should never happen after clip, but defensive)
    total_df['Impact_Score'] = total_df['Impact_Score'].fillna(50)

    # FIX 9: fill player_pressure from match avg_pressure if missing
    if 'player_pressure' in total_df.columns and 'avg_pressure' in total_df.columns:
        total_df['player_pressure'] = total_df['player_pressure'].fillna(
            total_df['avg_pressure']
        )

    # ── Diagnostics ───────────────────────────────────────────────────────────
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