"""
pipeline.py - central orchestrator for the Cricket Impact Metric calculation
"""
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
    Computes a robust, context-aware Impact Metric (IM) for T20 players.
    
    Formula logic:
    RawImpact = (Performance_bat × BatContext + Performance_bowl × BowlContext) × Situation
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def run_pipeline(self):
        """
        Execute the full end-to-end impact calculation pipeline.
        """
        
        # 1. DATA LOADING
        # pulls ball-by-ball CSVs and standardizes schemas
        df = load_data(self.data_dir)
        if df.empty:
            logging.error("No data found. Exiting pipeline.")
            return None, None

        # 2. FEATURE ENGINEERING
        # computes match-state features like required run rate and phase flags
        df = engineer_features(df)

        # 3. PERFORMANCE CALCULATION
        # derives core batting and bowling output (runs, wickets, efficiency)
        bat_df, bowl_df = compute_performance(df)

        # 4. CONTEXT & SITUATION
        # evaluates match-level pressure and tournament importance multipliers
        match_context_df = compute_context_and_situation(df)

        # 5. IMPACT SCORE
        # applies logistic normalization to map raw performance into a 0-100 scale
        impact_df = calculate_raw_and_final_impact(bat_df, bowl_df, match_context_df)

        # 6. ROLLING IMPACT
        # calculates recency-weighted moving average over the last 10 innings
        rolling_df = compute_rolling_impact(impact_df)

        # 7. VISUALIZATIONS
        # generates and saves static visual reports for stakeholder review
        generate_visualizations(impact_df, rolling_df)

        return impact_df, rolling_df