"""
rolling_metric.py - aggregates impact scores over time with recency weighting
"""
import logging
import numpy as np
import pandas as pd


def compute_rolling_impact(impact_df):
    """
    Calculates Rolling Impact (RI) using the last 10 innings of each player.
    """
    logging.info("Calculating Recency-Weighted Rolling Impact (Last 10 Innings)...")

    # guard for empty input
    if impact_df is None or impact_df.empty:
        logging.warning("compute_rolling_impact received empty DataFrame.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    df = impact_df.copy()

    # clean and standardize impact scores
    df["Impact_Score"] = pd.to_numeric(df["Impact_Score"], errors="coerce")
    df["Impact_Score"] = df["Impact_Score"].fillna(50) # use neutral 50 as safe default
    df = df.dropna(subset=["Impact_Score"])

    if df.empty:
        logging.warning("No valid Impact_Score rows after cleaning.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    # sort chronologically to ensure the 'last 10' are actually the most recent
    if "start_date" in df.columns:
        df["start_date_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
        df = df.sort_values(["player", "start_date_dt"])
    else:
        df = df.sort_values(["player", "match_id"])

    # define recency weights: scale from 0.04 (oldest) to 0.18 (newest)
    # this ensures that current form carries more weight than performance 2 years ago
    base_weights = np.array([0.04, 0.05, 0.06, 0.07, 0.08,
                              0.10, 0.12, 0.14, 0.16, 0.18])

    records = []

    # process players individually
    for player, grp in df.groupby("player"):
        scores = grp["Impact_Score"].values

        if len(scores) == 0:
            continue

        total_innings = len(scores)

        # take the last 10 innings (or fewer if player is new)
        window = scores[-10:]
        n = len(window)

        # normalize weights to match specific window size (ensures sum = 1.0)
        weights = base_weights[-n:].copy()
        weight_sum = weights.sum()
        if weight_sum <= 0:
            weights = np.ones(n) / n
        else:
            weights = weights / weight_sum

        # compute weighted average (dot product)
        rolling_score = float(np.dot(window, weights))

        # fallback for potential calculation artifacts
        if np.isnan(rolling_score):
            rolling_score = float(np.nanmean(window)) if len(window) > 0 else 50.0

        # apply out-of-form penalty: 10% reduction if last 3 games were all poor (<40)
        in_poor_form = False
        if n >= 3:
            last_three = window[-3:]
            if not np.any(np.isnan(last_three)) and np.all(last_three < 40):
                rolling_score *= 0.90
                in_poor_form = True

        # final score must stay within [0, 100]
        rolling_score = float(np.clip(rolling_score, 0, 100))

        records.append({
            "player":          player,
            "Rolling_Impact":  round(rolling_score, 2),
            "innings_count":   n,
            "total_innings":   total_innings,
            "in_poor_form":    in_poor_form
        })

    # return empty frame if no records generated
    if not records:
        logging.warning("No rolling impact records produced.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    # rank players by their final rolling IM score
    rolling_df = pd.DataFrame(records)
    rolling_df = (
        rolling_df
        .sort_values("Rolling_Impact", ascending=False)
        .reset_index(drop=True)
    )

    logging.info(
        f"Rolling Impact computed for {len(rolling_df)} players. "
        f"Range: [{rolling_df['Rolling_Impact'].min():.1f}, {rolling_df['Rolling_Impact'].max():.1f}]"
    )

    return rolling_df