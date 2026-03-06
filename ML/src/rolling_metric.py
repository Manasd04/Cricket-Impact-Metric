import logging
import numpy as np
import pandas as pd


def compute_rolling_impact(impact_df):
    """
    Calculates Rolling Impact (RI) using the last 10 innings of each player.

    Edge Cases Handled:
    1. Empty impact_df — returns empty DataFrame immediately.
    2. Impact_Score all NaN for a player — filled with neutral 50 before rolling.
    3. Player with only 1 inning — handled via weights[-n:] re-normalization.
    4. Player with 0 innings after dropna — skipped via len(scores)==0 guard.
    5. Weights don't sum to 1.0 for <10 innings — explicitly re-normalized.
    6. out-of-form penalty only when last 3 innings exist AND all < 40.
    7. Rolling score NaN after dot product (all-NaN window) — fallback to mean.
    8. Final Rolling_Impact always clipped strictly to [0, 100].
    9. innings_count reported correctly for players with fewer than 10 innings.
    10. Returns empty DataFrame (not crash) if no valid records produced.
    """
    logging.info("Calculating Recency-Weighted Rolling Impact (Last 10 Innings)...")

    # ── Guard: empty input ─────────────────────────────────────────────────────
    if impact_df is None or impact_df.empty:
        logging.warning("compute_rolling_impact received empty DataFrame.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    df = impact_df.copy()

    # ── Safety cleaning ────────────────────────────────────────────────────────
    df["Impact_Score"] = pd.to_numeric(df["Impact_Score"], errors="coerce")
    # FIX 2: fill NaN with neutral baseline (not drop — preserve innings count)
    df["Impact_Score"] = df["Impact_Score"].fillna(50)
    # Now drop any that are still NaN (shouldn't happen, but defensive)
    df = df.dropna(subset=["Impact_Score"])

    if df.empty:
        logging.warning("No valid Impact_Score rows after cleaning.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    # ── Sort chronologically ───────────────────────────────────────────────────
    if "start_date" in df.columns:
        df["start_date_dt"] = pd.to_datetime(df["start_date"], errors="coerce")
        df = df.sort_values(["player", "start_date_dt"])
    else:
        df = df.sort_values(["player", "match_id"])

    # ── Recency weights (most-recent last = highest weight) ───────────────────
    # [0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]
    # i=9 (most recent) gets 0.18, i=0 (oldest) gets 0.04
    base_weights = np.array([0.04, 0.05, 0.06, 0.07, 0.08,
                              0.10, 0.12, 0.14, 0.16, 0.18])

    records = []

    for player, grp in df.groupby("player"):
        scores = grp["Impact_Score"].values

        # FIX 4: skip players with no scores
        if len(scores) == 0:
            continue

        # FIX 9: track actual innings count
        total_innings = len(scores)

        # FIX 1: use last ≤ 10 innings
        window = scores[-10:]
        n = len(window)

        # FIX 3 & 5: align weights to window size and re-normalize so sum = 1
        weights = base_weights[-n:].copy()
        weight_sum = weights.sum()
        if weight_sum <= 0:
            weights = np.ones(n) / n
        else:
            weights = weights / weight_sum

        rolling_score = float(np.dot(window, weights))

        # FIX 7: NaN after dot product (e.g. all-NaN window despite fillna)
        if np.isnan(rolling_score):
            rolling_score = float(np.nanmean(window)) if len(window) > 0 else 50.0

        # ── Out-of-form penalty ────────────────────────────────────────────
        # FIX 6: only apply penalty if at least 3 innings AND all last 3 < 40
        in_poor_form = False
        if n >= 3:
            last_three = window[-3:]
            if not np.any(np.isnan(last_three)) and np.all(last_three < 40):
                rolling_score *= 0.90
                in_poor_form = True

        # FIX 8: clip to valid range
        rolling_score = float(np.clip(rolling_score, 0, 100))

        records.append({
            "player":          player,
            "Rolling_Impact":  round(rolling_score, 2),
            "innings_count":   n,
            "total_innings":   total_innings,
            "in_poor_form":    in_poor_form
        })

    # FIX 10: guard empty records list
    if not records:
        logging.warning("No rolling impact records produced.")
        return pd.DataFrame(columns=['player', 'Rolling_Impact', 'innings_count', 'in_poor_form'])

    rolling_df = pd.DataFrame(records)
    rolling_df = (
        rolling_df
        .sort_values("Rolling_Impact", ascending=False)
        .reset_index(drop=True)
    )

    logging.info(
        f"Rolling Impact computed for {len(rolling_df)} players. "
        f"Range: [{rolling_df['Rolling_Impact'].min():.1f}, {rolling_df['Rolling_Impact'].max():.1f}] | "
        f"Poor form: {rolling_df['in_poor_form'].sum()} players"
    )

    return rolling_df