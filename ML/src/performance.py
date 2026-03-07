"""
performance.py - computes base batting and bowling scores per match
"""
import logging
import numpy as np
import pandas as pd

def compute_performance(df):
    """
    Computes batting and bowling performance sub-scores per player per match.
    """

    logging.info("Calculating Performance Scores (Batting & Bowling)...")

    # input safety check
    if df.empty:
        logging.warning("compute_performance received empty DataFrame. Returning empty results.")
        empty_bat  = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])
        empty_bowl = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])
        return empty_bat, empty_bowl

    # ignore super overs (innings > 2) as they contain outliers
    df = df[df['innings'].isin([1, 2])].copy()

    if df.empty:
        logging.warning("No regular-innings data after super-over filter.")
        empty_bat  = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])
        empty_bowl = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])
        return empty_bat, empty_bowl

    # define valid facing: excludes wides (which don't count as a ball faced)
    df['is_valid_facing'] = (df['wides'].fillna(0) == 0)

    # define dot ball: legal delivery where 0 runs were scored off the bat
    df['is_dot_ball'] = (
        (df['runs_off_bat'].fillna(0) == 0)
        & (df['is_legal_delivery'].astype(bool))
    )

    # get total runs scored in each innings for contribution benchmarking
    innings_totals = (
        df.groupby(['match_id', 'innings'])['total_runs']
        .sum()
        .reset_index()
        .rename(columns={'total_runs': 'innings_total'})
    )

    # ==========================
    #  BATTING PERFORMANCE
    # ==========================

    required_bat_cols = ['match_id', 'innings', 'batsman', 'runs', 'is_valid_facing']
    missing_bat = [c for c in required_bat_cols if c not in df.columns]

    if missing_bat:
        logging.warning(f"Missing batting columns: {missing_bat}. Returning empty bat_df.")
        bat_df = pd.DataFrame(columns=['match_id', 'innings', 'batsman', 'Performance_bat'])

    else:
        # aggregate raw batting stats
        bat_df = df.groupby(['match_id', 'innings', 'batsman']).agg(
            runs=('runs', 'sum'),
            balls_faced=('is_valid_facing', 'sum'),
            boundaries=('runs', lambda x: x.isin([4, 6]).sum())
        ).reset_index()

        # join innings total for relative contribution scoring
        bat_df = bat_df.merge(innings_totals, on=['match_id', 'innings'], how='left')
        bat_df['innings_total'] = bat_df['innings_total'].fillna(1).replace(0, 1)

        # strike rate: runs scored per 100 balls
        bat_df['strike_rate'] = (
            bat_df['runs'] / np.maximum(bat_df['balls_faced'], 1)
        ) * 100

        # runs contribution: player's share of the team's total runs
        bat_df['runs_contribution'] = (
            bat_df['runs'] / bat_df['innings_total']
        ).fillna(0)

        # ── SCALING & NORMALIZATION ──

        # run impact: log-scaled runs (diminishing returns for very high scores)
        bat_df['Run_Impact'] = np.clip(
            np.log1p(bat_df['runs']) / np.log(80),
            0,
            1.5
        )

        # strike rate impact: centered at 120 (par T20 SR)
        bat_df['SR_Impact'] = np.clip(
            (bat_df['strike_rate'] - 120) / 60 + 1,
            0.5,
            1.5
        )

        # boundary impact: rewards ability to hit 4s and 6s
        bat_df['Boundary_Impact'] = np.clip(
            np.sqrt(bat_df['boundaries']) / 3,
            0,
            1.3
        )

        bat_df[['Run_Impact','SR_Impact','Boundary_Impact']] = (
            bat_df[['Run_Impact','SR_Impact','Boundary_Impact']].fillna(0)
        )

        # weighted composite batting score
        bat_df['Performance_bat'] = (
              0.6 * bat_df['Run_Impact']
            + 0.25 * bat_df['SR_Impact']
            + 0.15 * bat_df['Boundary_Impact']
        )

        # workload factor: penalizes cameos with very few balls faced
        bat_df['BatWorkloadFactor'] = np.clip(
            0.4 + 0.6 * (bat_df['balls_faced'] / 30),
            0,
            1
        )

        # final batting performance dampened by workload
        bat_df['Performance_bat'] = np.clip(
            bat_df['Performance_bat'] * bat_df['BatWorkloadFactor'],
            0,
            5
        )

    # ==========================
    #  BOWLING PERFORMANCE
    # ==========================

    required_bowl_cols = ['match_id', 'bowler', 'is_bowler_wicket', 'bowler_runs', 'is_legal_delivery']
    missing_bowl = [c for c in required_bowl_cols if c not in df.columns]

    if missing_bowl:
        logging.warning(f"Missing bowling columns: {missing_bowl}. Returning empty bowl_df.")
        bowl_df = pd.DataFrame(columns=['match_id', 'bowler', 'Performance_bowl'])

    else:
        # aggregate raw bowling stats
        bowl_df = df.groupby(['match_id', 'bowler']).agg(
            wickets=('is_bowler_wicket', 'sum'),
            runs_conceded=('bowler_runs', 'sum'),
            balls_bowled=('is_legal_delivery', 'sum'),
            dot_balls=('is_dot_ball', 'sum')
        ).reset_index()

        # convert balls to overs
        bowl_df['overs_bowled']  = bowl_df['balls_bowled'] / 6

        # economy rate: runs allowed per over
        bowl_df['economy_rate']  = (
            bowl_df['runs_conceded'] / np.maximum(bowl_df['overs_bowled'], 0.1)
        )

        # dot percent: ratio of non-scoring legal deliveries
        bowl_df['dot_percent']   = (
            bowl_df['dot_balls'] / np.maximum(bowl_df['balls_bowled'], 1)
        )

        # ── SCALING & NORMALIZATION ──

        # wicket impact: rewards taking wickets (base unit = 2 wickets)
        bowl_df['Wicket_Impact']  = np.clip(bowl_df['wickets'] / 2, 0, 2.5)

        # economy impact: inverse scaling (lower economy = higher score)
        # anchored at 8.0 rpo = 1.0 impact
        bowl_df['Economy_Impact'] = np.clip(
            8.0 / np.maximum(bowl_df['economy_rate'], 0.1),
            0,
            2
        )

        # dot impact: rewards control and pressure building
        bowl_df['Dot_Impact'] = np.clip(
            bowl_df['dot_percent'] / 0.35,
            0,
            2
        )

        bowl_df[['Wicket_Impact','Economy_Impact','Dot_Impact']] = (
            bowl_df[['Wicket_Impact','Economy_Impact','Dot_Impact']].fillna(0)
        )

        # weighted composite bowling score
        bowl_df['Performance_bowl'] = (
            0.5 * bowl_df['Wicket_Impact']
            + 0.3 * bowl_df['Economy_Impact']
            + 0.2 * bowl_df['Dot_Impact']
        )

        # workload factor: penalizes short spells (< 4 overs)
        # sqrt scaling ensures 1 over still gets ~50% credit
        bowl_df['WorkloadFactor'] = np.clip(
            np.sqrt(bowl_df['overs_bowled'] / 4),
            0,
            1
        )

        # final bowling performance dampened by workload
        bowl_df['Performance_bowl'] = np.clip(
            bowl_df['Performance_bowl'] * bowl_df['WorkloadFactor'],
            0,
            5
        )

    logging.info(
        f"Performance computed: "
        f"{len(bat_df)} batting entries | "
        f"{len(bowl_df)} bowling entries"
    )

    return bat_df, bowl_df