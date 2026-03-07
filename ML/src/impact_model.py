"""
impact_model.py - integrates performance, context, and situation into the final IM [0-100]
"""
import logging
import numpy as np
import pandas as pd


def calculate_raw_and_final_impact(bat_df, bowl_df, match_context):
    """
    Computes the final logistic-normalized Impact Score (0-99) per player per match.
    """
    logging.info("Applying Logistic Scaling to Final Impact Scores...")

    # guard for empty inputs
    if bat_df.empty and bowl_df.empty:
        logging.warning("Both bat_df and bowl_df are empty. Returning empty impact_df.")
        return pd.DataFrame(columns=['match_id', 'player', 'Impact_Score'])

    # ==========================
    #  1. STANDARDIZE PLAYER KEYS
    # ==========================
    b  = pd.DataFrame(columns=['match_id', 'player', 'perf_bat'])
    bw = pd.DataFrame(columns=['match_id', 'player', 'perf_bowl'])

    # align batting performance
    if not bat_df.empty and 'batsman' in bat_df.columns:
        b = (bat_df[['match_id', 'batsman', 'Performance_bat']]
             .rename(columns={'batsman': 'player', 'Performance_bat': 'perf_bat'})
             .copy())

    # align bowling performance
    if not bowl_df.empty and 'bowler' in bowl_df.columns:
        bw = (bowl_df[['match_id', 'bowler', 'Performance_bowl']]
              .rename(columns={'bowler': 'player', 'Performance_bowl': 'perf_bowl'})
              .copy())

    # ==========================
    #  2. COMBINE PERFORMANCES
    # ==========================
    # outer join so players who only bat or only bowl are both included
    total_df = pd.merge(b, bw, on=['match_id', 'player'], how='outer').fillna(0)

    # total raw performance is the sum of both roles
    total_df['Total_Performance'] = (
        total_df['perf_bat'].fillna(0) + total_df['perf_bowl'].fillna(0)
    )

    if total_df.empty:
        logging.warning("total_df empty after bat/bowl merge.")
        return pd.DataFrame(columns=['match_id', 'player', 'Impact_Score'])

    # ==========================
    #  3. ATTACH CONTEXTS
    # ==========================
    if match_context is None or match_context.empty:
        logging.warning("match_context is empty. Using neutral Contexts, Situation=1.0.")
        total_df['BatContext'] = 1.0
        total_df['BowlContext'] = 1.0
        total_df['Situation'] = 1.0
    else:
        # separate match-level multipliers from player-level stats to prevent merge duplication
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

        # attach per-player pressure handles if available
        if 'player' in match_context.columns and 'player_pressure' in match_context.columns:
            player_pressure = match_context[['match_id', 'player', 'player_pressure']].dropna(subset=['player'])
            total_df = total_df.merge(player_pressure, on=['match_id', 'player'], how='left')

    # fill na multipliers with neutral 1.0
    for col in ['BatContext', 'BowlContext', 'Context', 'Situation']:
        if col not in total_df.columns:
            total_df[col] = 1.0
        else:
            total_df[col] = total_df[col].fillna(1.0)

    # clip values to pre-defined formula boundaries
    total_df['BatContext']  = np.clip(total_df['BatContext'],  0.9, 1.5)
    total_df['BowlContext'] = np.clip(total_df['BowlContext'], 0.9, 1.5)
    total_df['Context']     = np.clip(total_df['Context'],     0.8, 1.4)
    total_df['Situation']   = np.clip(total_df['Situation'],   1.0, 1.35)

    # ==========================
    #  5. RAW IMPACT
    # ==========================
    # raw impact combines performance adjusted by situational multipliers
    total_df['RawImpact'] = (
        (total_df['perf_bat'] * total_df['BatContext'])
        + (total_df['perf_bowl'] * total_df['BowlContext'])
    ) * total_df['Situation']
    total_df['RawImpact'] = total_df['RawImpact'].fillna(0)

    # ==========================
    #  6. FINAL IMPACT [0-99]
    # ==========================
    # logistic normalization anchors RawImpact=1.0 at 50 points
    # RawImpact > 1.0 grows toward 99; RawImpact < 1.0 shrinks toward 0
    raw_clipped = np.clip(total_df['RawImpact'], -100, 100)
    total_df['Impact_Score'] = 100 / (1 + np.exp(-5 * (raw_clipped - 1.0)))
    total_df['Impact_Score'] = np.clip(total_df['Impact_Score'], 0, 99)
    total_df['Impact_Score'] = total_df['Impact_Score'].fillna(50)

    # fallback for missing player pressure
    if 'player_pressure' in total_df.columns and 'avg_pressure' in total_df.columns:
        total_df['player_pressure'] = total_df['player_pressure'].fillna(
            total_df['avg_pressure']
        )

    logging.info(
        f"Impact computed: {len(total_df)} performances | "
        f"{total_df['player'].nunique()} players | {total_df['match_id'].nunique()} matches"
    )

    return total_df