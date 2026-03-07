import pandas as pd
import os
import logging
import sys

# Suppress debug logs for cleaner output
logging.getLogger().setLevel(logging.ERROR)

from ML.src.data_loader import load_data
from ML.src.feature_engineering import engineer_features
from ML.src.performance import compute_performance
from ML.src.context_situation import compute_context_and_situation
from ML.src.impact_model import calculate_raw_and_final_impact
from ML.src.rolling_metric import compute_rolling_impact

# Setup paths
base_dir = r"c:\Users\DELL\OneDrive\Desktop\Cricket-Impact-Metric-main"
data_dir = os.path.join(base_dir, "ipl_male_csv2")
output_dir = os.path.join(base_dir, "demo_excel_files")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("Starting pipeline to generate step-by-step samples...")

# 1. Load Data
print("1/6: Loading raw data...")
df = load_data(data_dir)
# Save a single match's raw data for better context (e.g., first 240 balls)
df.head(250).to_csv(os.path.join(output_dir, "01_raw_data_sample.csv"), index=False)

# 2. Feature Engineering
print("2/6: Engineering contextual features...")
df_fe = engineer_features(df)
df_fe.head(250).to_csv(os.path.join(output_dir, "02_feature_engineered_sample.csv"), index=False)

# 3. Performance Scores (Batting and Bowling)
print("3/6: Computing batting and bowling performance...")
bat_df, bowl_df = compute_performance(df_fe)
bat_df.head(100).to_csv(os.path.join(output_dir, "03a_batting_performance_sample.csv"), index=False)
bowl_df.head(100).to_csv(os.path.join(output_dir, "03b_bowling_performance_sample.csv"), index=False)

# 4. Context and Situation
print("4/6: Computing match context and pressure situations...")
match_context_df = compute_context_and_situation(df_fe)
match_context_df.head(100).to_csv(os.path.join(output_dir, "04_context_and_situation_sample.csv"), index=False)

# 5. Raw and Final Impact Score
print("5/6: Calculating final impact metric (logistic normalization)...")
impact_df = calculate_raw_and_final_impact(bat_df, bowl_df, match_context_df)
impact_df.head(100).to_csv(os.path.join(output_dir, "05_final_impact_scores_sample.csv"), index=False)

# 6. Rolling Impact 
print("6/6: Calculating recency-weighted rolling impact...")
rolling_df = compute_rolling_impact(impact_df)
rolling_df.head(100).to_csv(os.path.join(output_dir, "06_rolling_impact_sample.csv"), index=False)

print(f"\n✅ Success! All 7 demo files have been generated in the '{output_dir}' folder.")
