#!/usr/bin/env python3
"""Generate GD vs WVS comparison figure for the GRI website."""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path

matplotlib.use('Agg')

# Paths
base = Path(__file__).parent.parent.parent
gd_csv = base / 'analysis_output/scorecards/GD_combined_scorecards.csv'
wvs_csv = base / 'analysis_output/scorecards/WVS_combined_scorecards.csv'
output_dir = Path(__file__).parent.parent / 'images'
output_dir.mkdir(exist_ok=True)

# Load data
gd = pd.read_csv(gd_csv)
wvs = pd.read_csv(wvs_csv)

# Filter: GD1-6 only, exclude "Overall (Average)" rows
gd = gd[gd['survey'].isin([f'GD{i}' for i in range(1, 7)])]
wvs = wvs[wvs['dimension'] != 'Overall (Average)']

# Dimensions to compare (shared between both datasets)
dims = [
    'Country × Gender × Age',
    'Country × Religion',
    'Country × Environment',
    'Religion',
    'Gender',
]
dim_labels = [
    'Country ×\nGender × Age',
    'Country ×\nReligion',
    'Country ×\nEnvironment',
    'Religion',
    'Gender',
]

# Compute per-dimension averages across waves
gd_means = gd.groupby('dimension').agg(
    gri=('gri', 'mean'),
    design_effect=('design_effect', 'mean'),
    effective_n=('effective_n', 'mean'),
    precision_retention=('precision_retention', 'mean'),
    n_samples=('n_samples', 'mean'),
).loc[dims]

wvs_means = wvs.groupby('dimension').agg(
    gri=('gri', 'mean'),
    design_effect=('design_effect', 'mean'),
    effective_n=('effective_n', 'mean'),
    precision_retention=('precision_retention', 'mean'),
    n_samples=('n_samples', 'mean'),
).loc[dims]

# --- Figure: Two-panel comparison ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), gridspec_kw={'width_ratios': [1, 1]})

x = np.arange(len(dims))
width = 0.35

# Colors
gd_color = '#2563eb'  # Blue
wvs_color = '#dc2626'  # Red

# Panel A: GRI scores
bars1 = ax1.bar(x - width/2, gd_means['gri'], width, label='Global Dialogues (N ≈ 1,000)',
                color=gd_color, alpha=0.85, edgecolor='white', linewidth=0.5)
bars2 = ax1.bar(x + width/2, wvs_means['gri'], width, label='World Values Survey (N ≈ 58,000)',
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

# Add value labels on bars
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
             f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=gd_color)
for bar in bars2:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
             f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=8, color=wvs_color)

# Panel B: Precision Retention
bars3 = ax2.bar(x - width/2, gd_means['precision_retention'] * 100, width,
                label='Global Dialogues', color=gd_color, alpha=0.85, edgecolor='white', linewidth=0.5)
bars4 = ax2.bar(x + width/2, wvs_means['precision_retention'] * 100, width,
                label='World Values Survey', color=wvs_color, alpha=0.85, edgecolor='white', linewidth=0.5)

ax2.set_ylabel('Precision Retained (%)', fontsize=12, fontweight='bold')
ax2.set_title('Statistical Precision Retained', fontsize=13, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(dim_labels, fontsize=9)
ax2.set_ylim(0, 110)
ax2.legend(fontsize=9, loc='upper left')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.axhline(y=0, color='grey', linewidth=0.5)

# Add value labels on bars
for bar in bars3:
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5,
             f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=gd_color)
for bar in bars4:
    ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1.5,
             f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=wvs_color)

fig.suptitle('Global Dialogues vs. World Values Survey', fontsize=15, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig(output_dir / 'gd_vs_wvs_comparison.png', dpi=200, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.savefig(output_dir / 'gd_vs_wvs_comparison.svg', bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"Saved to {output_dir / 'gd_vs_wvs_comparison.png'}")
print(f"Saved to {output_dir / 'gd_vs_wvs_comparison.svg'}")
