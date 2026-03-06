import logging
import numpy as np
import pandas as pd


def compute_performance(df):
    """
    Computes batting and bowling performance sub-scores per player per match.

    Changes from original:
    1. Super over filter — innings 3/4/5/6 excluded (171 deliveries). Super overs
       are 6-ball shootouts with inflated pressure/stats that skew the metric.
    2. is_dot_ball uses runs_off_bat == 0 instead of total_runs == 0.
       total_runs includes legbyes/byes — a defensive shot with a legbye is still
       a dot for the batsman. Undercounted 4,890 dot balls (1.76% of deliveries).
    3. wickets uses is_bowler_wicket instead of is_wicket. is_wicket counted run
       outs (1,153 cases, 8.5% of all wickets) and retired hurt (17 cases) as
       bowler wickets — these are fielding/medical events, not the bowler's credit.
    4. runs_conceded uses bowler_runs instead of total_runs. bowler_runs excludes
       byes and legbyes (6,828 runs across the dataset, 1.82%) which are the
       wicketkeeper's/fielder's responsibility, not the bowler's.
    5. runs_contribution now uses innings_total (per innings) not match_total
       (both innings combined). Using match total halved every batter's contribution
       score — a player scoring 50 in a 180-run innings got 50/320=14.7% instead
       of the correct 50/180=27.8%. Nearly 2x undercount.
    6. Batting groupby now includes 'innings' so per-innings totals join correctly.
    7. is_legal_delivery not recomputed — already exists from feature_engineering.py.
    """
    logging.info("Calculating Performance Scores (Batting & Bowling)...")

    # ── FIX 1: Exclude super overs (innings 3, 4, 5, 6) ───────────────────
    # Super overs exist in the dataset (171 deliveries across all matches).
    # A player batting in innings 3 (super over) after batting in innings 2
    # appears twice in the same match. Super over balls are a 6-ball shootout —
    # keeping them inflates boundary counts and skews economy rates with tiny samples.
    df = df[df['innings'].isin([1, 2])].copy()

    # ── FIX 2: Correct dot ball definition ─────────────────────────────────
    # A dot ball = the BATSMAN scored 0 AND it was a legal delivery.
    # Original used total_runs == 0, which includes extras (byes, legbyes).
    # A delivery with 1 legbye but 0 runs off the bat is STILL a dot for the batter.
    # is_legal_delivery is already computed in feature_engineering.py as an int col.
    df['is_valid_facing'] = (df['wides'] == 0)
    df['is_dot_ball'] = (
        (df['runs_off_bat'] == 0)
        & (df['is_legal_delivery'].astype(bool))
    )

    # ── Per-innings totals (for correct runs_contribution) ──────────────────
    # FIX 5: group by match_id + innings, not just match_id.
    # Original grouped by match_id giving the SUM of both innings (~320 runs).
    # Correct denominator is the innings the batter actually played in (~160 runs).
    innings_totals = (
        df.groupby(['match_id', 'innings'])['total_runs']
        .sum()
        .reset_index()
        .rename(columns={'total_runs': 'innings_total'})
    )

    # ══════════════════════════════════════════════════════════════════════
    #  BATTING PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════

    # FIX 6: groupby includes 'innings' so we can join innings_totals correctly.
    # Each batter appears in exactly 1 innings per match (verified: max 1 after
    # super over filter), so this adds no duplicate rows.
    bat_df = df.groupby(['match_id', 'innings', 'batsman']).agg(
        runs=('runs', 'sum'),
        balls_faced=('is_valid_facing', 'sum'),
        boundaries=('runs', lambda x: (x >= 4).sum())   # catches 4s and 6s
    ).reset_index()

    # FIX 5: merge per-innings total (not whole-match total)
    bat_df = bat_df.merge(innings_totals, on=['match_id', 'innings'])

    # Strike rate: runs per 100 balls faced (wides excluded from balls_faced)
    bat_df['strike_rate'] = (
        bat_df['runs'] / np.maximum(bat_df['balls_faced'], 1)
    ) * 100

    # RunsContribution: share of team's innings total this batter scored
    # Range 0–1 (verified: max never exceeds 1.0 with per-innings denominator)
    bat_df['runs_contribution'] = (
        bat_df['runs'] / np.maximum(bat_df['innings_total'], 1)
    )

    # Performance sub-scores — all clipped to [0, 2] to prevent one dimension
    # dominating the weighted sum
    bat_df['SR_Impact']       = np.clip(bat_df['strike_rate'] / 130, 0, 2)
    bat_df['Boundary_Impact'] = np.clip(bat_df['boundaries']  / 5,   0, 2)

    # Weighted batting performance
    # Weights: Runs 40% (primary output), SR 30% (aggression), Boundaries 30% (ball-striking)
    bat_df['Performance_bat'] = (
        0.4 * bat_df['runs_contribution']
        + 0.3 * bat_df['SR_Impact']
        + 0.3 * bat_df['Boundary_Impact']
    )

    # Workload factor: dampens tiny cameos that inflate SR via small samples.
    # A batter who faced 30+ balls gets full credit (factor = 1.0).
    # A batter who faced 0 balls gets a floor factor of 0.4 (not 0, since
    # bowling/fielding contribution still matters for allrounders).
    # Note: 84.7% of batting entries face < 30 balls in T20 — this factor
    # is intentional, not a bug. It prevents 1-ball sixes from scoring 90+.
    bat_df['BatWorkloadFactor'] = np.clip(
        0.4 + 0.6 * (bat_df['balls_faced'] / 30), 0, 1
    )
    bat_df['Performance_bat'] = bat_df['Performance_bat'] * bat_df['BatWorkloadFactor']

    # ══════════════════════════════════════════════════════════════════════
    #  BOWLING PERFORMANCE
    # ══════════════════════════════════════════════════════════════════════

    bowl_df = df.groupby(['match_id', 'bowler']).agg(
        # FIX 3: is_bowler_wicket excludes run outs (1,153 cases) and
        # retired hurt (17 cases) — these are not the bowler's credit.
        wickets=('is_bowler_wicket', 'sum'),

        # FIX 4: bowler_runs excludes byes + legbyes (6,828 runs total).
        # bowler_runs = runs_off_bat + wides + noballs (computed in data_loader).
        runs_conceded=('bowler_runs', 'sum'),

        # is_legal_delivery already exists from feature_engineering (FIX 7)
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

    # Performance sub-scores
    # Wicket_Impact: 2 wickets = benchmark (1.0 contribution), 5-for = capped at 2.5
    bowl_df['Wicket_Impact']  = np.clip(bowl_df['wickets']      / 2,    0, 2.5)
    # Economy_Impact: inverse — economy of 8.0 = benchmark (1.0 contribution)
    bowl_df['Economy_Impact'] = np.clip(
        8.0 / np.maximum(bowl_df['economy_rate'], 0.1), 0, 2
    )
    # Dot_Impact: 35% dot ball rate = benchmark (1.0 contribution)
    bowl_df['Dot_Impact']     = np.clip(bowl_df['dot_percent']   / 0.35, 0, 2)

    # Weighted bowling performance
    # Weights: Wickets 50% (decisive), Economy 30% (control), Dots 20% (pressure)
    bowl_df['Performance_bowl'] = (
        0.5 * bowl_df['Wicket_Impact']
        + 0.3 * bowl_df['Economy_Impact']
        + 0.2 * bowl_df['Dot_Impact']
    )

    # Workload factor: bowlers who bowl 4 full overs get full credit (1.0).
    # sqrt curve: 1 over=0.50, 2 overs=0.71, 3 overs=0.87, 4 overs=1.0.
    # This fairly dampens part-time bowlers (10.1% bowl < 2 overs) while
    # still rewarding a specialist who bowls 2 tight overs.
    bowl_df['WorkloadFactor'] = np.clip(
        np.sqrt(bowl_df['overs_bowled'] / 4), 0, 1
    )
    bowl_df['Performance_bowl'] = bowl_df['Performance_bowl'] * bowl_df['WorkloadFactor']

    logging.info(
        f"Performance computed: "
        f"{len(bat_df)} batting entries | "
        f"{len(bowl_df)} bowling entries | "
        f"Bat range: [{bat_df['Performance_bat'].min():.3f}, {bat_df['Performance_bat'].max():.3f}] | "
        f"Bowl range: [{bowl_df['Performance_bowl'].min():.3f}, {bowl_df['Performance_bowl'].max():.3f}]"
    )

    return bat_df, bowl_df