import logging
import numpy as np
import pandas as pd


def compute_performance(df):
    """
    Computes batting and bowling performance sub-scores per player per match.

    Edge Cases Handled:
    1. Super over filter — innings 3/4/5/6 excluded (super overs have inflated stats).
    2. Dot ball uses runs_off_bat == 0 (not total_runs which includes legbyes).
    3. wickets uses is_bowler_wicket (excludes run outs, retired hurt).
    4. runs_conceded uses bowler_runs (excludes byes/legbyes).
    5. innings_total computed per innings (not per match) for accurate contribution %.
    6. innings_total=0 guard: players in abandoned innings or no legitimate balls.
    7. NaN guard on all sub-scores before weighted sum.
    8. Players who appear ONLY as bowler (never batted) → Performance_bat = 0, not NaN.
    9. Players who appear ONLY as batter (never bowled) → Performance_bowl = 0, not NaN.
    10. Empty bat_df or bowl_df → returns empty DataFrames instead of crashing.
    11. All output columns clipped to valid range before returning.
    """
    logging.info("Calculating Performance Scores (Batting & Bowling)...")

    # ── Guard: empty input ─────────────────────────────────────────────────────
    if df.empty:
        logging.warning("compute_performance received empty DataFrame. Returning empty results.")
        empty_bat  = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])
        empty_bowl = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])
        return empty_bat, empty_bowl

    # ── FIX 1: Exclude super overs ─────────────────────────────────────────────
    df = df[df['innings'].isin([1, 2])].copy()

    if df.empty:
        logging.warning("No regular-innings data after super-over filter.")
        empty_bat  = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])
        empty_bowl = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])
        return empty_bat, empty_bowl

    # ── FIX 2: Correct dot ball definition ────────────────────────────────────
    if 'wides' not in df.columns:
        df['wides'] = 0
    df['wides'] = df['wides'].fillna(0)

    df['is_valid_facing'] = (df['wides'] == 0)
    df['is_dot_ball'] = (
        (df['runs_off_bat'].fillna(0) == 0)
        & (df['is_legal_delivery'].astype(bool))
    )

    # ── Per-innings totals ──────────────────────────────────────────────────────
    innings_totals = (
        df.groupby(['match_id', 'innings'])['total_runs']
        .sum()
        .reset_index()
        .rename(columns={'total_runs': 'innings_total'})
    )

    # ══════════════════════════════════════════════════════════════════════
    #  BATTING PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════

    required_bat_cols = ['match_id', 'innings', 'batsman', 'runs', 'is_valid_facing']
    missing_bat = [c for c in required_bat_cols if c not in df.columns]
    if missing_bat:
        logging.warning(f"Missing batting columns: {missing_bat}. Returning empty bat_df.")
        bat_df = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])
    else:
        bat_df = df.groupby(['match_id', 'innings', 'batsman']).agg(
            runs=('runs', 'sum'),
            balls_faced=('is_valid_facing', 'sum'),
            boundaries=('runs', lambda x: (x >= 4).sum())
        ).reset_index()

        bat_df = bat_df.merge(innings_totals, on=['match_id', 'innings'], how='left')

        # FIX 7: guard innings_total = 0 (abandoned/no-result innings)
        bat_df['innings_total'] = bat_df['innings_total'].fillna(1).replace(0, 1)

        bat_df['strike_rate'] = (
            bat_df['runs'] / np.maximum(bat_df['balls_faced'], 1)
        ) * 100

        # Normalize metrics so an "average" performance equals around 1.0
        # Average runs ~ 30, average SR ~ 135, average boundaries ~ 4
        bat_df['Runs_Impact']     = np.clip(bat_df['runs'] / 30, 0, 2.5)
        bat_df['SR_Impact']       = np.clip(bat_df['strike_rate'] / 135, 0, 2.5)
        bat_df['Boundary_Impact'] = np.clip(bat_df['boundaries'] / 4, 0, 2.5)

        # FIX 7: fill NaN before weighted sum
        bat_df[['Runs_Impact', 'SR_Impact', 'Boundary_Impact']] = (
            bat_df[['Runs_Impact', 'SR_Impact', 'Boundary_Impact']].fillna(0)
        )

        bat_df['Performance_bat'] = (
            0.5 * bat_df['Runs_Impact']
            + 0.3 * bat_df['SR_Impact']
            + 0.2 * bat_df['Boundary_Impact']
        )

        bat_df['BatWorkloadFactor'] = np.clip(
            0.4 + 0.6 * (bat_df['balls_faced'] / 20), 0, 1.2
        )
        bat_df['Performance_bat'] = np.clip(
            bat_df['Performance_bat'] * bat_df['BatWorkloadFactor'], 0, 5
        )

    # ══════════════════════════════════════════════════════════════════════
    #  BOWLING PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════

    required_bowl_cols = ['match_id', 'bowler', 'is_bowler_wicket', 'bowler_runs', 'is_legal_delivery']
    missing_bowl = [c for c in required_bowl_cols if c not in df.columns]
    if missing_bowl:
        logging.warning(f"Missing bowling columns: {missing_bowl}. Returning empty bowl_df.")
        bowl_df = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])
    else:
        bowl_df = df.groupby(['match_id', 'bowler']).agg(
            wickets=('is_bowler_wicket', 'sum'),
            runs_conceded=('bowler_runs', 'sum'),
            balls_bowled=('is_legal_delivery', 'sum'),
            dot_balls=('is_dot_ball', 'sum')
        ).reset_index()

        bowl_df['overs_bowled']  = bowl_df['balls_bowled'] / 6
        bowl_df['economy_rate']  = (
            bowl_df['runs_conceded'] / np.maximum(bowl_df['overs_bowled'], 0.1)
        )
        bowl_df['dot_percent']   = (
            bowl_df['dot_balls'] / np.maximum(bowl_df['balls_bowled'], 1)
        )

        bowl_df['Wicket_Impact']  = np.clip(bowl_df['wickets']      / 2,    0, 2.5)
        bowl_df['Economy_Impact'] = np.clip(
            8.0 / np.maximum(bowl_df['economy_rate'], 0.1), 0, 2
        )
        bowl_df['Dot_Impact']     = np.clip(bowl_df['dot_percent']   / 0.35, 0, 2)

        # FIX 7: fill NaN sub-scores before weighted sum
        bowl_df[['Wicket_Impact', 'Economy_Impact', 'Dot_Impact']] = (
            bowl_df[['Wicket_Impact', 'Economy_Impact', 'Dot_Impact']].fillna(0)
        )

        bowl_df['Performance_bowl'] = (
            0.5 * bowl_df['Wicket_Impact']
            + 0.3 * bowl_df['Economy_Impact']
            + 0.2 * bowl_df['Dot_Impact']
        )

        bowl_df['WorkloadFactor'] = np.clip(
            np.sqrt(bowl_df['overs_bowled'] / 4), 0, 1
        )
        bowl_df['Performance_bowl'] = np.clip(
            bowl_df['Performance_bowl'] * bowl_df['WorkloadFactor'], 0, 5
        )

    logging.info(
        f"Performance computed: "
        f"{len(bat_df)} batting entries | "
        f"{len(bowl_df)} bowling entries"
    )

    return bat_df, bowl_df