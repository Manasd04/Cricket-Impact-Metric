import logging
import numpy as np
import pandas as pd


def compute_rolling_impact(impact_df):
    """
    Calculates Rolling Impact (RI) using the last 10 innings of each player.

    Features:
    • Recency-weighted average
    • Works with fewer than 10 innings
    • Handles missing values safely
    • Applies out-of-form penalty
    • Keeps scores strictly in the 0–100 scale
    """

    logging.info("Calculating Recency-Weighted Rolling Impact (Last 10 Innings)...")

    df = impact_df.copy()

    # --------------------------------------------------
    # 1. SAFETY CLEANING
    # --------------------------------------------------

    # Remove rows with missing impact score
    df = df.dropna(subset=["Impact_Score"])

    # Ensure numeric
    df["Impact_Score"] = pd.to_numeric(df["Impact_Score"], errors="coerce")

    # Fill remaining NaN with neutral baseline
    df["Impact_Score"] = df["Impact_Score"].fillna(50)

    # --------------------------------------------------
    # 2. SORT CHRONOLOGICALLY
    # --------------------------------------------------

    if "start_date" in df.columns:
        df["start_date_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
        df = df.sort_values(["player", "start_date_dt"])
    else:
        df = df.sort_values(["player", "match_id"])

    # --------------------------------------------------
    # 3. RECENCY WEIGHTS
    # --------------------------------------------------

    base_weights = np.array([
        0.04, 0.05, 0.06, 0.07, 0.08,
        0.10, 0.12, 0.14, 0.16, 0.18
    ])

    records = []

    # --------------------------------------------------
    # 4. PER PLAYER ROLLING IMPACT
    # --------------------------------------------------

    for player, grp in df.groupby("player"):

        scores = grp["Impact_Score"].values

        if len(scores) == 0:
            continue

        # Last ≤ 10 innings
        window = scores[-10:]
        n = len(window)

        # Align weights to window size
        weights = base_weights[-n:]
        weights = weights / weights.sum()

        rolling_score = float(np.dot(window, weights))

        # --------------------------------------------------
        # 5. OUT OF FORM PENALTY
        # --------------------------------------------------

        in_poor_form = False

        if n >= 3:
            last_three = window[-3:]

            if np.all(last_three < 40):
                rolling_score *= 0.90
                in_poor_form = True

        # --------------------------------------------------
        # 6. CLIP TO SAFE RANGE
        # --------------------------------------------------

        rolling_score = float(np.clip(rolling_score, 0, 100))

        records.append({
            "player": player,
            "Rolling_Impact": round(rolling_score, 2),
            "innings_count": n,
            "in_poor_form": in_poor_form
        })

    rolling_df = pd.DataFrame(records)

    if rolling_df.empty:
        return rolling_df

    rolling_df = (
        rolling_df
        .sort_values("Rolling_Impact", ascending=False)
        .reset_index(drop=True)
    )

    logging.info(f"Rolling Impact computed for {len(rolling_df)} players")

    return rolling_df