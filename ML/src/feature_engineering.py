"""
feature_engineering.py - computes contextual match-state features (phase, RR, targets)
"""
import logging
import numpy as np
import pandas as pd


def engineer_features(df):
    """
    Engineers all match-state features needed for pressure and context calculation.
    """
    logging.info("Engineering features: Phase, Context, and Situation flags...")

    # derive 0-indexed over number from the ball (e.g. 15.2 -> 15)
    if 'ball' in df.columns:
        df['over'] = df['ball'].apply(lambda x: int(x))

    # sort rows to ensure cumulative sums (runs, wickets) are chronologically correct
    if {'match_id', 'innings', 'over', 'ball'}.issubset(df.columns):
        df = df.sort_values(
            by=['match_id', 'innings', 'over', 'ball']
        ).reset_index(drop=True)

    # categorize match phase: powerplay (0-5), middle (6-14), or death (15+)
    df['phase'] = 'Middle'
    df.loc[df['over'] <= 5,  'phase'] = 'Powerplay'
    df.loc[df['over'] >= 15, 'phase'] = 'Death'

    # innings-specific cumulative runs (independent for each team)
    df['team_runs_cum'] = df.groupby(
        ['match_id', 'innings'])['total_runs'].cumsum()

    # innings-specific cumulative wickets fallen
    df['wickets_fallen'] = df.groupby(
        ['match_id', 'innings'])['is_wicket'].cumsum()

    # identify legal balls (exclude wides and no-balls which are re-bowled)
    df['is_legal_delivery'] = (
        (df['wides'] == 0) & (df['noballs'] == 0)
    ).astype(int)

    # count total legal balls bowled in the innings so far
    df['balls_bowled'] = df.groupby(
        ['match_id', 'innings'])['is_legal_delivery'].cumsum()

    # current run rate: total runs / overs faced (capped at ball 1)
    df['current_rr'] = (
        df['team_runs_cum'] / np.maximum(df['balls_bowled'], 1)
    ) * 6

    # overs remaining: how many 6-ball overs are left in the 20-over quota
    df['overs_remaining'] = np.maximum(20 - (df['balls_bowled'] / 6), 0.1)

    # wickets remaining: starts at 10, floor at 1 for formula stability
    df['wickets_remaining'] = np.maximum(10 - df['wickets_fallen'], 1)

    # determine chase target for innings 2 (first innings total + 1)
    # uses 160 as a neutral baseline for innings 1 context
    innings1_totals = (
        df[df['innings'] == 1]
        .groupby('match_id')['total_runs']
        .sum()
    )
    df['target'] = df['match_id'].map(innings1_totals).fillna(160) + 1
    df.loc[df['innings'] == 1, 'target'] = 160

    # required run rate: runs needed / overs remaining (floor at 0.1)
    df['required_rr'] = np.maximum(
        (df['target'] - df['team_runs_cum']) / df['overs_remaining'],
        0.1
    )

    logging.info(
        f"Features engineered. "
        f"Phase distribution: { df['phase'].value_counts().to_dict() } | "
        f"Target range: {df['target'].min():.0f}–{df['target'].max():.0f} | "
        f"Wickets remaining range: {df['wickets_remaining'].min():.0f}–{df['wickets_remaining'].max():.0f}"
    )

    return df