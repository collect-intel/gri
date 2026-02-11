#!/usr/bin/env python3
"""Generate multi-survey comparison figures for the GRI website."""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

matplotlib.use('Agg')

# Paths
base = Path(__file__).parent.parent.parent
output_dir = Path(__file__).parent.parent / 'images'
output_dir.mkdir(exist_ok=True)

# Load all scorecards
gd = pd.read_csv(base / 'analysis_output/scorecards/GD_combined_scorecards.csv')
wvs = pd.read_csv(base / 'analysis_output/scorecards/WVS_combined_scorecards.csv')
afro = pd.read_csv(base / 'analysis_output/scorecards/Afrobarometer_R9_scorecard.csv')
lb23 = pd.read_csv(base / 'analysis_output/scorecards/Latinobarometro_2023_scorecard.csv')
lb24 = pd.read_csv(base / 'analysis_output/scorecards/Latinobarometro_2024_scorecard.csv')
pew = pd.read_csv(base / 'analysis_output/scorecards/Pew_Spring2024_scorecard.csv')

# Filter GD to GD1-GD8, exclude Overall rows for averaging
gd = gd[gd['dimension'] != 'Overall (Average)']
wvs = wvs[wvs['dimension'] != 'Overall (Average)']

# Compute per-dimension averages for multi-wave surveys
gd_means = gd.groupby('dimension').agg(
    gri=('gri', 'mean'),
    precision_retention=('precision_retention', 'mean'),
    design_effect=('design_effect', 'mean'),
).reset_index()

wvs_means = wvs.groupby('dimension').agg(
    gri=('gri', 'mean'),
    precision_retention=('precision_retention', 'mean'),
    design_effect=('design_effect', 'mean'),
).reset_index()

# Average LB 2023+2024
lb_avg = pd.concat([lb23, lb24]).groupby('dimension').agg(
    gri=('gri', 'mean'),
    precision_retention=('precision_retention', 'mean'),
    design_effect=('design_effect', 'mean'),
).reset_index()


def get_val(df, dim, col='gri'):
    row = df[df['dimension'] == dim]
    if len(row) > 0:
        return row[col].values[0]
    return np.nan


# ============================================================================
# Figure 1: Multi-survey GRI comparison (key dimensions)
# ============================================================================

dims = [
    'Country × Gender × Age',
    'Country × Religion',
    'Country × Environment',
    'Country',
    'Religion',
    'Gender',
]
dim_labels = [
    'Country ×\nGender × Age',
    'Country ×\nReligion',
    'Country ×\nEnvironment',
    'Country',
    'Religion',
    'Gender',
]

surveys = [
    ('Global Dialogues\n(N≈1K, global)', gd_means, '#2563eb'),
    ('WVS\n(N≈58K, global)', wvs_means, '#dc2626'),
    ('Pew Spring 2024\n(N=41K, 35 countries)', pew, '#16a34a'),
    ('Afrobarometer R9\n(N=53K, 39 African)', afro, '#f59e0b'),
    ('Latinobarómetro\n(N≈19K, 17 LatAm)', lb_avg, '#8b5cf6'),
]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5), gridspec_kw={'width_ratios': [1, 1]})

x = np.arange(len(dims))
n_surveys = len(surveys)
total_width = 0.78
bar_width = total_width / n_surveys

# Panel A: GRI scores
for i, (label, df, color) in enumerate(surveys):
    vals = [get_val(df, d, 'gri') for d in dims]
    offset = (i - n_surveys/2 + 0.5) * bar_width
    bars = ax1.bar(x + offset, vals, bar_width, label=label,
                   color=color, alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar in bars:
        h = bar.get_height()
        if not np.isnan(h):
            ax1.text(bar.get_x() + bar.get_width()/2., h + 0.012,
                     f'{h:.2f}', ha='center', va='bottom', fontsize=6.5,
                     color=color, fontweight='bold')

ax1.set_ylabel('GRI Score', fontsize=12, fontweight='bold')
ax1.set_title('Representativeness (GRI)', fontsize=13, fontweight='bold', pad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(dim_labels, fontsize=8.5)
ax1.set_ylim(0, 1.15)
ax1.legend(fontsize=7.5, loc='upper left', ncol=1)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.axhline(y=0, color='grey', linewidth=0.5)

# Panel B: Precision Retention
for i, (label, df, color) in enumerate(surveys):
    vals = [get_val(df, d, 'precision_retention') * 100 for d in dims]
    offset = (i - n_surveys/2 + 0.5) * bar_width
    bars = ax2.bar(x + offset, vals, bar_width, label=label,
                   color=color, alpha=0.85, edgecolor='white', linewidth=0.5)
    for bar in bars:
        h = bar.get_height()
        if not np.isnan(h):
            ax2.text(bar.get_x() + bar.get_width()/2., h + 1.0,
                     f'{h:.0f}%', ha='center', va='bottom', fontsize=6.5,
                     color=color, fontweight='bold')

ax2.set_ylabel('Precision Retained (%)', fontsize=12, fontweight='bold')
ax2.set_title('Statistical Precision Retained', fontsize=13, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(dim_labels, fontsize=8.5)
ax2.set_ylim(0, 115)
ax2.legend(fontsize=7.5, loc='upper left', ncol=1)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.axhline(y=0, color='grey', linewidth=0.5)

fig.suptitle('Survey Representativeness Comparison', fontsize=15, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig(output_dir / 'survey_comparison.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.savefig(output_dir / 'survey_comparison.svg', bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Saved survey_comparison to {output_dir}")

# Also save the old GD vs WVS for backwards compat
fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), gridspec_kw={'width_ratios': [1, 1]})

width = 0.35
gd_color = '#2563eb'
wvs_color = '#dc2626'

gd_gri = [get_val(gd_means, d, 'gri') for d in dims]
wvs_gri = [get_val(wvs_means, d, 'gri') for d in dims]

bars1 = ax1.bar(x - width/2, gd_gri, width, label='Global Dialogues (N ≈ 1,000)',
                color=gd_color, alpha=0.85, edgecolor='white', linewidth=0.5)
bars2 = ax1.bar(x + width/2, wvs_gri, width, label='World Values Survey (N ≈ 58,000)',
                color=wvs_color, alpha=0.85, edgecolor='white', linewidth=0.5)

ax1.set_ylabel('GRI Score', fontsize=12, fontweight='bold')
ax1.set_title('Representativeness (GRI)', fontsize=13, fontweight='bold', pad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(dim_labels, fontsize=9)
ax1.set_ylim(0, 1.05)
ax1.legend(fontsize=9, loc='upper left')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.axhline(y=0, color='grey', linewidth=0.5)

for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
             f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=gd_color)
for bar in bars2:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
             f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=wvs_color)

gd_prec = [get_val(gd_means, d, 'precision_retention') * 100 for d in dims]
wvs_prec = [get_val(wvs_means, d, 'precision_retention') * 100 for d in dims]

bars3 = ax2.bar(x - width/2, gd_prec, width, label='Global Dialogues',
                color=gd_color, alpha=0.85, edgecolor='white', linewidth=0.5)
bars4 = ax2.bar(x + width/2, wvs_prec, width, label='World Values Survey',
                color=wvs_color, alpha=0.85, edgecolor='white', linewidth=0.5)

ax2.set_ylabel('Precision Retained (%)', fontsize=12, fontweight='bold')
ax2.set_title('Statistical Precision Retained', fontsize=13, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(dim_labels, fontsize=9)
ax2.set_ylim(0, 110)
ax2.legend(fontsize=9, loc='upper left')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.axhline(y=0, color='grey', linewidth=0.5)

for bar in bars3:
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5,
             f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=gd_color)
for bar in bars4:
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5,
             f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=wvs_color)

fig2.suptitle('Global Dialogues vs. World Values Survey', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(output_dir / 'gd_vs_wvs_comparison.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.savefig(output_dir / 'gd_vs_wvs_comparison.svg', bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Saved gd_vs_wvs_comparison to {output_dir}")
