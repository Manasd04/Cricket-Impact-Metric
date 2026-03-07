"""
visualization.py - generates charts and visual analytics for the impact model
"""
import logging
import os
import numpy as np
import matplotlib
matplotlib.use('Agg') # use non-interactive background for server stability
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns


def generate_visualizations(impact_df, rolling_df):
    """
    Generates and saves visual reports to the visualizations/ directory.
    """
    logging.info("Generating Visualizations...")
    os.makedirs("visualizations", exist_ok=True)

    # 1. IMPACT SCORE DISTRIBUTION
    # visualizes the spread of all per-match impacts across the dataset
    plt.figure(figsize=(10, 6))
    sns.histplot(impact_df['Impact_Score'], bins=40, kde=True, color='mediumpurple')
    plt.axvline(50, color='crimson', linestyle='dashed', linewidth=2, label='Neutral baseline (50)')
    plt.title('Distribution of Per-Match Impact Scores', fontsize=14, fontweight='bold')
    plt.xlabel('Impact Score (0-100)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.savefig("visualizations/impact_distribution.png", dpi=150)
    plt.close()

    # 2. TOP-10 PLAYER LEADERBOARD
    # ranks players by their recency-weighted rolling impact score
    top_players = rolling_df.head(10).copy()
    colors = ['gold' if i == 0 else 'steelblue' for i in range(len(top_players))]
    plt.figure(figsize=(12, 6))
    bars = plt.barh(top_players['player'][::-1], top_players['Rolling_Impact'][::-1], color=colors[::-1])
    plt.axvline(50, color='crimson', linestyle='dashed', linewidth=1.5, label='Neutral (50)')
    plt.title('Top 10 Players — Rolling Impact (Last 10 Innings)', fontsize=13, fontweight='bold')
    plt.xlabel('Rolling Impact Score (0-100)')
    plt.ylabel('Player')
    for bar, val in zip(bars, top_players['Rolling_Impact'][::-1]):
        plt.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                 f'{val:.1f}', va='center', fontsize=9)
    plt.legend()
    plt.tight_layout()
    plt.savefig("visualizations/top_players_leaderboard.png", dpi=150)
    plt.close()

    # 3. INDIVIDUAL PLAYER TRENDS (Top 5 only)
    # line charts showing performance volatility for the top-ranked players
    top5 = rolling_df.head(5)['player'].tolist()
    df_sorted = impact_df.sort_values(['player', 'match_id'])
    for player in top5:
        pdata = df_sorted[df_sorted['player'] == player].tail(10).reset_index(drop=True)
        if pdata.empty:
            continue
        plt.figure(figsize=(9, 4))
        plt.plot(range(1, len(pdata) + 1), pdata['Impact_Score'],
                 marker='o', linewidth=2, color='steelblue', markersize=7)
        plt.fill_between(range(1, len(pdata) + 1), pdata['Impact_Score'],
                         50, alpha=0.15, color='steelblue')
        plt.axhline(50, color='crimson', linestyle='dashed', linewidth=1.5, label='Neutral (50)')
        plt.ylim(0, 100)
        plt.title(f'Performance Trend — {player}', fontsize=12, fontweight='bold')
        plt.xlabel('Match (oldest → newest)')
        plt.ylabel('Impact Score (0-100)')
        plt.legend()
        plt.tight_layout()
        safe_name = player.replace(' ', '_').replace('.', '')
        plt.savefig(f"visualizations/impact_trend_{safe_name}.png", dpi=150)
        plt.close()

    # 4. IMPACT METER GAUGE
    # premium gauge chart for the #1 ranked player
    top_player = rolling_df.iloc[0]
    score = float(top_player['Rolling_Impact'])
    _draw_gauge(score, top_player['player'])
    plt.savefig("visualizations/impact_meter.png", dpi=150, bbox_inches='tight')
    plt.close()

    logging.info("Visualizations saved to 'visualizations/' directory.")


def _draw_gauge(score: float, player_name: str):
    """
    Draws a semicircular impact meter for a given score (0-100).
    """
    fig, ax = plt.subplots(figsize=(7, 4), subplot_kw=dict(aspect='equal'))
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.3, 1.3)
    ax.axis('off')

    # gauge zones by impact intensity
    zones = [
        (0,  30,  'crimson',        'Low'),
        (30, 50,  'darkorange',     'Below Par'),
        (50, 70,  'mediumseagreen', 'Above Par'),
        (70, 100, 'royalblue',      'Elite'),
    ]
    for lo, hi, color, label in zones:
        theta1 = 180 - lo * 1.8
        theta2 = 180 - hi * 1.8
        arc = mpatches.Arc((0, 0), 2.0, 2.0, angle=0,
                           theta1=theta2, theta2=theta1,
                           color=color, lw=20, zorder=2)
        ax.add_patch(arc)

    # indicator needle points to the player's score
    angle_rad = np.radians(180 - score * 1.8)
    nx, ny = 0.85 * np.cos(angle_rad), 0.85 * np.sin(angle_rad)
    ax.annotate('', xy=(nx, ny), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='black', lw=2.5))
    ax.plot(0, 0, 'ko', markersize=8, zorder=5)

    ax.text(0, -0.15, f'{score:.1f}', ha='center', va='center',
            fontsize=22, fontweight='bold', color='black')
    ax.text(0, 1.18, f'Impact Meter — {player_name}', ha='center',
            fontsize=11, fontweight='bold')
    ax.text(-1.1, -0.12, '0',   ha='center', fontsize=9, color='grey')
    ax.text(0,   -0.22, '50',  ha='center', fontsize=9, color='grey')
    ax.text(1.1,  -0.12, '100', ha='center', fontsize=9, color='grey')

    return fig