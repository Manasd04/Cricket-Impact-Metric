import logging
import numpy as np
import pandas as pd


def engineer_features(df):
    """
    Engineers all match-state features needed for pressure and context calculation.

    Changes from original:
    1. Derives 'over' column from 'ball' (was missing — caused phase to always
       be 'Middle' and sort to be silently skipped for all 278,205 deliveries).
    2. Sort now works correctly since 'over' is available before the sort check.
    3. wickets_remaining floor changed from 0.1 → 1 (floor of 0.1 caused
       pressure_index = 10/0.1 = 100x multiplier when last wicket falls).
    4. Real target used for innings 2 (innings 1 total + 1) instead of hardcoded
       160 for every match. Hardcoded 160 caused required_rr error up to 5 runs/over
       in 5,586 deliveries across 100 matches tested.
    5. is_legal_delivery explicitly cast to int before cumsum (cleaner, avoids
       bool cumsum edge cases in older pandas versions).
    """
    logging.info("Engineering features: Phase, Context, and Situation flags...")

    # ── FIX 1: Derive 'over' from 'ball' column ────────────────────────────
    # The dataset has NO 'over' column — only 'ball' with values like 0.1, 1.3, 15.6.
    # int(ball) gives the over number (0-indexed: over 0 = first over, over 19 = last).
    # Without this line: the sort is silently skipped AND every delivery is labelled
    # 'Middle' because both conditions check 'if over in df.columns'.
    if 'ball' in df.columns:
        df['over'] = df['ball'].apply(lambda x: int(x))

    # ── FIX 2: Sort correctly (now works since 'over' exists) ─────────────
    # Cumulative features (team_runs_cum, wickets_fallen, balls_bowled) rely on
    # rows being in the correct ball-by-ball sequence. 6 match-innings combos in
    # the dataset are not naturally sorted — without sorting, cumsum gives wrong
    # running totals for those matches.
    # Sort on ['match_id', 'innings', 'over', 'ball'] to get exact delivery order:
    #   over  → which over (0-19)
    #   ball  → position within the over (0.1, 0.2 ... 0.6, including wides/no-balls)
    if {'match_id', 'innings', 'over', 'ball'}.issubset(df.columns):
        df = df.sort_values(
            by=['match_id', 'innings', 'over', 'ball']
        ).reset_index(drop=True)

    # ── Match Phase ────────────────────────────────────────────────────────
    # Over numbering (0-indexed from 'ball' column):
    #   0–5   = Powerplay  (overs 1–6):  only 2 fielders allowed outside 30-yard circle
    #   6–14  = Middle     (overs 7–15): consolidation + rotation
    #   15–19 = Death      (overs 16–20): all-out attack, highest pressure
    df['phase'] = 'Middle'
    df.loc[df['over'] <= 5,  'phase'] = 'Powerplay'
    df.loc[df['over'] >= 15, 'phase'] = 'Death'

    # ── Cumulative Match State ─────────────────────────────────────────────
    # All cumulative features must be computed AFTER sorting.
    # Grouped by ['match_id', 'innings'] so innings 1 and innings 2 are tracked
    # independently — runs don't carry over between innings.
    df['team_runs_cum'] = df.groupby(
        ['match_id', 'innings'])['total_runs'].cumsum()

    df['wickets_fallen'] = df.groupby(
        ['match_id', 'innings'])['is_wicket'].cumsum()

    # Legal delivery: only counts when no wide AND no no-ball
    # Wides and no-balls are re-bowled — they don't count towards the 6-ball over.
    df['is_legal_delivery'] = (
        (df['wides'] == 0) & (df['noballs'] == 0)
    ).astype(int)   # explicit int cast: avoids bool cumsum issues in pandas < 1.3

    df['balls_bowled'] = df.groupby(
        ['match_id', 'innings'])['is_legal_delivery'].cumsum()

    # ── Run Rates ──────────────────────────────────────────────────────────
    # current_rr: runs scored so far / overs faced so far
    # np.maximum(..., 1) guards against division by zero on the very first ball
    df['current_rr'] = (
        df['team_runs_cum'] / np.maximum(df['balls_bowled'], 1)
    ) * 6

    # overs_remaining: how many 6-ball overs are left in this innings
    # Floor at 0.1 (not 0) so required_rr doesn't divide by zero on the last ball.
    # The pressure explosion this causes (20/0.1 = 200x) is handled downstream
    # by capping pressure_index at 10 in context_situation.py.
    df['overs_remaining'] = np.maximum(20 - (df['balls_bowled'] / 6), 0.1)

    # ── FIX 3: wickets_remaining floor changed 0.1 → 1 ────────────────────
    # Original used max(..., 0.1) which gave 10/0.1 = 100x in the pressure formula
    # when the 10th wicket fell. Floor of 1 means "at least 1 wicket still standing"
    # which is the correct cricket interpretation (you need a batter at each end).
    df['wickets_remaining'] = np.maximum(10 - df['wickets_fallen'], 1)

    # ── FIX 4: Real target for innings 2 ──────────────────────────────────
    # Original hardcoded target = 160 for every delivery in every match.
    # Problem: a team chasing 220 vs chasing 140 have completely different
    # pressure profiles. Using 160 for both caused required_rr errors of up to
    # 5 runs/over in real data (e.g. match where innings 1 total was 261).
    #
    # Fix:
    #   Innings 1 → target = 160 (par / benchmark; no actual target exists yet)
    #   Innings 2 → target = innings 1 total + 1 (actual runs needed to win)
    innings1_totals = (
        df[df['innings'] == 1]
        .groupby('match_id')['total_runs']
        .sum()
    )
    # Map real target to every row by match_id; fallback to 160 if innings 1
    # data is somehow missing (e.g. truncated match file)
    df['target'] = df['match_id'].map(innings1_totals).fillna(160) + 1
    # Innings 1 always uses the par benchmark (160)
    df.loc[df['innings'] == 1, 'target'] = 160

    # required_rr: run rate needed from this point to reach the target
    # Floor at 0.1 so it's always a positive number (handles target already exceeded)
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