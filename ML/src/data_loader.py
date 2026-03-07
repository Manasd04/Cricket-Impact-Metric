"""
data_loader.py - handles loading and cleaning of ball-by-ball raw CSV data
"""
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
    """
    Load and clean all IPL ball-by-ball CSV files from directory.
    """
    logging.info(f"Loading CSV files from {data_dir}...")

    # Filter out metadata files (_info.csv) to avoid structure conflicts
    all_files = [
        f for f in glob.glob(os.path.join(data_dir, "*.csv"))
        if "_info" not in os.path.basename(f)
    ]

    # error if no csv found
    if not all_files:
        logging.warning("No CSV files found. Please ensure the path is correct.")
        return pd.DataFrame()

    df_list = []
    skipped = 0

    # process files individually
    for f in all_files:
        try:
            temp_df = pd.read_csv(f)

            # assign match_id from filename if column missing
            if 'match_id' not in temp_df.columns:
                match_id = os.path.basename(f).split('.')[0]
                temp_df['match_id'] = match_id

            df_list.append(temp_df)

        except Exception as e:
            # log failure but keep going
            logging.error(f"Skipping {f}: {e}")
            skipped += 1

    # guard against empty list before concat
    if not df_list:
        logging.error("All files failed to load. Returning empty DataFrame.")
        return pd.DataFrame()

    # combine all matches into one big dataframe
    df = pd.concat(df_list, ignore_index=True)
    logging.info(
        f"Loaded {len(df_list)} matches ({skipped} skipped). "
        f"Total ball-by-ball records: {len(df)}"
    )

    # standardize column names: handle both 'batter' and 'striker' variants
    if 'batter' in df.columns and 'striker' not in df.columns:
        df.rename(columns={'batter': 'striker'}, inplace=True)

    # alias 'striker' to 'batsman' for performance logic compatibility
    if 'striker' in df.columns:
        df['batsman'] = df['striker']

    # alias 'runs_off_bat' to 'runs' for simplicity
    if 'runs_off_bat' in df.columns:
        df['runs'] = df['runs_off_bat']
    elif 'runs' not in df.columns:
        df['runs'] = 0

    # initialize all possible extra types to 0 if missing
    for col in ['extras', 'wides', 'noballs', 'byes', 'legbyes', 'penalty']:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0)

    # fill na runs with 0
    if 'runs_off_bat' in df.columns:
        df['runs_off_bat'] = df['runs_off_bat'].fillna(0)
    df['runs'] = df['runs'].fillna(0)

    # handle edge case where player_dismissed is a dataframe instead of series
    if isinstance(df.get('player_dismissed'), pd.DataFrame):
        dismissed_col = df['player_dismissed'].iloc[:, 0]
    else:
        dismissed_col = df.get('player_dismissed', pd.Series(dtype=str))

    # is_wicket: identifies any dismissal (used for chase pressure/duck detection)
    df['is_wicket'] = dismissed_col.notna() & (dismissed_col.astype(str).str.strip() != '')

    # is_bowler_wicket: credits the bowler only for non-fielding dismissals on legal balls
    wicket_type_col = df.get('wicket_type', pd.Series(dtype=str))
    df['is_bowler_wicket'] = (
        df['is_wicket']
        & ~wicket_type_col.isin(_NON_BOWLER_WICKETS)   # remove run outs/retired hurt
        & (df['noballs'] == 0)                          # wickets on no-balls don't count
    )

    # total_runs: base runs + all extras
    df['total_runs'] = df['runs'].fillna(0) + df['extras'].fillna(0)

    # bowler_runs: runs specifically charged to the bowler (ignores byes/legbyes)
    df['bowler_runs'] = (
        df['runs'].fillna(0)
        + df['wides'].fillna(0)
        + df['noballs'].fillna(0)
    )

    # ensure season is always a string for consistent filtering
    df['season'] = df['season'].astype(str)
    
    # normalize cross-year seasons (e.g., '2009/10') to single year labels
    season_map = {
        '2007/08': '2008',
        '2009/10': '2010',
        '2020/21': '2020'
    }
    df['season'] = df['season'].replace(season_map)

    logging.info(
        f"Data ready. Columns: {list(df.columns)}\n"
        f"  Seasons: {sorted(df['season'].unique())}\n"
        f"  Players (striker): {df['striker'].nunique() if 'striker' in df.columns else 'N/A'}\n"
        f"  Total wickets: {df['is_wicket'].sum()} "
        f"(bowler credited: {df['is_bowler_wicket'].sum()})"
    )

    return df