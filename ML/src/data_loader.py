import pandas as pd
import glob
import os
import logging
import numpy as np


# Wicket types that are NOT credited to the bowler
# run out    → fielding team's effort, not the bowler
# retired hurt / retired out → medical/voluntary, not a wicket at all
# obstructing the field → rare, batsman's fault not bowler's
_NON_BOWLER_WICKETS = {'run out', 'retired hurt', 'retired out', 'obstructing the field'}


def load_data(data_dir):
    logging.info(f"Loading CSV files from {data_dir}...")

    # ── FIX 1: Filter out _info.csv files ──────────────────────────────────
    # The ipl_male_csv2 folder contains 2 files per match:
    #   123456.csv       ← ball-by-ball data (what we want)
    #   123456_info.csv  ← match metadata in different structure (crashes concat)
    # Original code loaded ALL *.csv which logged 1,169 parse errors silently.
    all_files = [
        f for f in glob.glob(os.path.join(data_dir, "*.csv"))
        if "_info" not in os.path.basename(f)
    ]

    if not all_files:
        logging.warning("No CSV files found. Please ensure the path is correct.")
        return pd.DataFrame()

    df_list = []
    skipped = 0

    for f in all_files:
        try:
            temp_df = pd.read_csv(f)

            # Assign match_id from filename if column missing
            if 'match_id' not in temp_df.columns:
                match_id = os.path.basename(f).split('.')[0]
                temp_df['match_id'] = match_id

            df_list.append(temp_df)

        except Exception as e:
            logging.error(f"Skipping {f}: {e}")
            skipped += 1

    # ── FIX 2: Guard empty list before concat ───────────────────────────────
    # pd.concat([]) raises ValueError. This happens if every file failed to parse.
    if not df_list:
        logging.error("All files failed to load. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.concat(df_list, ignore_index=True)
    logging.info(
        f"Loaded {len(df_list)} matches ({skipped} skipped). "
        f"Total ball-by-ball records: {len(df)}"
    )

    # ── FIX 3: Column renaming — keep 'striker' alive ───────────────────────
    # Original rename_map renamed 'striker' → 'batsman', removing 'striker'.
    # BUT context_situation.py groups on df['striker'] to compute per-player
    # pressure. After the rename it crashes with KeyError: 'striker'.
    #
    # Fix: rename ONLY if the column is literally named 'batter' (older Cricsheet
    # format). The current IPL dataset already uses 'striker', so we keep it and
    # add 'batsman' as an alias column so performance.py still works.
    if 'batter' in df.columns and 'striker' not in df.columns:
        df.rename(columns={'batter': 'striker'}, inplace=True)

    # performance.py groups on 'batsman' — create alias without destroying 'striker'
    if 'striker' in df.columns:
        df['batsman'] = df['striker']

    # runs_off_bat → keep original name; add 'runs' alias for performance.py
    if 'runs_off_bat' in df.columns:
        df['runs'] = df['runs_off_bat']
    elif 'runs' not in df.columns:
        df['runs'] = 0

    # ── FIX 4: Fill ALL extra-type columns with 0, not just 3 ───────────────
    # Original only filled ['extras', 'wides', 'noballs'].
    # byes, legbyes, penalty are 99-100% NaN in most match files (no event = NaN).
    # feature_engineering and performance.py reference these directly.
    for col in ['extras', 'wides', 'noballs', 'byes', 'legbyes', 'penalty']:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0)

    # runs_off_bat also needs fillna (defensive)
    if 'runs_off_bat' in df.columns:
        df['runs_off_bat'] = df['runs_off_bat'].fillna(0)
    df['runs'] = df['runs'].fillna(0)

    # ── FIX 5: Correct is_wicket logic ─────────────────────────────────────
    # Original: is_wicket = player_dismissed.notna() & player_dismissed != ''
    # Problems:
    #   a) 'retired hurt' (17 cases) is in wicket_type but player_dismissed
    #      is filled → incorrectly counted as a wicket affecting bowler.
    #   b) 'run out' (1,153 cases = 8.3% of all wickets) is a fielding team
    #      event — should not be credited to bowler in performance.py.
    #   c) Wicket on a no-ball (10 cases, all run outs) — already excluded
    #      by (b) but explicitly handled here for clarity.
    #
    # is_wicket = True for ALL dismissals (affects batting stats — duck detection)
    # is_bowler_wicket = True ONLY for wickets the bowler caused

    # Handle duplicate player_dismissed column edge case (original code preserved)
    if isinstance(df.get('player_dismissed'), pd.DataFrame):
        dismissed_col = df['player_dismissed'].iloc[:, 0]
    else:
        dismissed_col = df.get('player_dismissed', pd.Series(dtype=str))

    # General wicket flag (used for cumulative wickets_fallen in feature_engineering)
    # Retired hurt = player left field, but innings wickets count still ticks
    # so we keep it as True for wickets_fallen tracking, but exclude from bowler credit
    df['is_wicket'] = dismissed_col.notna() & (dismissed_col.astype(str).str.strip() != '')

    # Bowler wicket flag (used in performance.py Wicket_Impact)
    wicket_type_col = df.get('wicket_type', pd.Series(dtype=str))
    df['is_bowler_wicket'] = (
        df['is_wicket']
        & ~wicket_type_col.isin(_NON_BOWLER_WICKETS)   # exclude run out, retired hurt
        & (df['noballs'] == 0)                          # wicket on no-ball is void
    )

    # ── total_runs: runs scored off bat + all extras ─────────────────────────
    # extras column already equals wides+noballs+byes+legbyes+penalty (verified)
    df['total_runs'] = df['runs'].fillna(0) + df['extras'].fillna(0)

    # ── bowler_runs: runs the BOWLER is responsible for ──────────────────────
    # Byes and legbyes are not the bowler's fault (wicketkeeper/fielder error).
    # Used by performance.py to compute accurate economy rate.
    df['bowler_runs'] = (
        df['runs'].fillna(0)
        + df['wides'].fillna(0)
        + df['noballs'].fillna(0)
    )

    # ── season: ensure always string for consistent filtering ────────────────
    # Season is int64 for numeric years (2017, 2018) but object for cross-year
    # seasons like '2007/08', '2020/21'. Casting to str makes it uniform.
    df['season'] = df['season'].astype(str)

    logging.info(
        f"Data ready. Columns: {list(df.columns)}\n"
        f"  Seasons: {sorted(df['season'].unique())}\n"
        f"  Players (striker): {df['striker'].nunique() if 'striker' in df.columns else 'N/A'}\n"
        f"  Total wickets: {df['is_wicket'].sum()} "
        f"(bowler credited: {df['is_bowler_wicket'].sum()})"
    )

    return df