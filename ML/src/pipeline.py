import logging
from .data_loader import load_data
from .feature_engineering import engineer_features
from .performance import compute_performance
from .context_situation import compute_context_and_situation
from .impact_model import calculate_raw_and_final_impact
from .rolling_metric import compute_rolling_impact
from .visualization import generate_visualizations


class CricketImpactMetric:
    """
    Computes a robust, non-gameable Impact Metric (IM) for Cricket Players.

    Formula:
        IM = Performance × Match_Context × Game_Situation

    Where:
        - Performance    : Weighted batting + bowling output, dampened by workload
        - Match_Context  : Pressure-adjusted game state (phase, RRR, wickets fallen)
        - Game_Situation : Match importance × pressure intensity × recency-of-form penalty

    Final IM is:
        • Normalized to a 0–100 scale via logistic transformation
        • 50 = neutral baseline (average player, average conditions)
        • Aggregated over a recency-weighted rolling window of last 10 innings
        • Updated once per match (not real-time)

    Design decisions that prevent gaming:
        1. WorkloadFactor       – short cameos don't inflate scores
        2. Logistic ceiling     – superhuman raw scores compress near 99, not beyond
        3. Out-of-form penalty  – players in a cold streak get a situational haircut
        4. Context cap (0.8–1.4)– extreme pressure can boost but never dominate alone
        5. Rolling weights sum to 1 – reordering matches cannot game the aggregation
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def run_pipeline(self):
        """
        Execute the full end-to-end pipeline.

        Returns
        -------
        impact_df  : pd.DataFrame  – per-player, per-match Impact Scores
        rolling_df : pd.DataFrame  – recency-weighted rolling IM over last 10 innings
        """
        # ── 1. LOAD ────────────────────────────────────────────────────
        # Reads all ball-by-ball CSVs from data_dir.
        # Standardises column names (batter/striker → batsman, runs_off_bat → runs).
        # Derives: is_wicket, total_runs, extras breakdown.
        df = load_data(self.data_dir)
        if df.empty:
            logging.error("No data found. Exiting pipeline.")
            return None, None

        # ── 2. FEATURE ENGINEERING ─────────────────────────────────────
        # Adds per-ball contextual features:
        #   • phase          : Powerplay (ov 1–6) / Middle (7–15) / Death (16–20)
        #   • team_runs_cum  : cumulative runs in innings
        #   • wickets_fallen : cumulative wickets in innings
        #   • current_rr     : run rate at this ball
        #   • overs_remaining: balls left / 6
        #   • required_rr    : (target − runs_so_far) / overs_remaining
        #                      Uses innings-1 actual total as innings-2 target.
        df = engineer_features(df)

        # ── 3. PERFORMANCE SCORE ───────────────────────────────────────
        # Batting  (per player per match):
        #   runs_contribution = runs / match_total  (prevents padding reward)
        #   SR_Impact         = strike_rate / 130   (T20 par ~130)
        #   Boundary_Impact   = boundaries / 5
        #   Performance_bat   = 0.4×contrib + 0.3×SR + 0.3×boundary
        #   × BatWorkloadFactor(balls_faced) → dampens <10 ball cameos
        #
        # Bowling  (per bowler per match):
        #   Wicket_Impact  = wickets / 2
        #   Economy_Impact = 8.0 / economy_rate  (inverse: lower eco = higher score)
        #   Dot_Impact     = dot_ball% / 0.35
        #   Performance_bowl = 0.5×wicket + 0.3×economy + 0.2×dot
        #   × BowlWorkloadFactor(overs_bowled) → dampens < 1 over spells
        bat_df, bowl_df = compute_performance(df)

        # ── 4. CONTEXT & SITUATION ─────────────────────────────────────
        # Context (per match scalar, range 0.8–1.4):
        #   pressure_index  = (required_rr / current_rr) × (10 / wkts_rem) × (20 / ov_rem)
        #   Context         = clip(avg_pressure / 8.0 + 0.8,  0.8, 1.4)
        #
        # Situation (per match scalar, range 1.0–1.5):
        #   match_importance: playoff/final > league match (1.0–1.3 multiplier)
        #   pressure_tier   : derived from avg_pressure quintile
        #   out_of_form_penalty: if player's last 3 impact scores all < 40 → ×0.9
        #   Situation = clip(importance × pressure_tier × form_factor, 1.0, 1.5)
        match_context_df = compute_context_and_situation(df)

        # ── 5. RAW → FINAL IMPACT ──────────────────────────────────────
        # Merge bat + bowl performance, then multiply by Context & Situation:
        #   Total_Performance = Performance_bat + Performance_bowl
        #   RawImpact         = Total_Performance × Context × Situation
        #
        # Logistic normalisation → Impact_Score in [0, 99]:
        #   Impact_Score = 100 / (1 + exp(−5 × (RawImpact − 1.0)))
        #   • RawImpact = 1.0 maps to exactly 50 (neutral baseline) ✓
        #   • Scores below 0.5 → Impact < 27  (well below par)
        #   • Scores above 1.5 → Impact > 73  (clearly above par)
        impact_df = calculate_raw_and_final_impact(bat_df, bowl_df, match_context_df)

        # ── 6. ROLLING AGGREGATION (last 10 innings, recency-weighted) ─
        # Weights (most-recent first): [0.18, 0.16, 0.14, 0.12, 0.10,
        #                               0.08, 0.07, 0.06, 0.05, 0.04]
        # → sum = 1.0, so Rolling_Impact stays on the same 0–100 scale.
        # Players with < 10 innings use only their available matches,
        # re-normalised so weights still sum to 1.
        rolling_df = compute_rolling_impact(impact_df)

        # ── 7. VISUALIZATIONS ──────────────────────────────────────────
        # Outputs saved to visualizations/ directory:
        #   impact_distribution.png     – histogram of all match Impact Scores
        #   top_players_leaderboard.png – top-10 rolling IM bar chart
        #   impact_trend_<player>.png   – per-player rolling trend (top 5)
        #   impact_meter.png            – gauge meter for the #1 player
        generate_visualizations(impact_df, rolling_df)

        return impact_df, rolling_df