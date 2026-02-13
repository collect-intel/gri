#!/usr/bin/env python3
"""
Generate publication-quality figures for the GRI whitepaper.

Reads actual data from the repository and produces PDF figures for LaTeX.

Usage:
    python generate_figures.py

Outputs:
    figures/gri_scores_by_wave.pdf
    figures/efficiency_ratios.pdf
    figures/scorecard_heatmap.pdf
    figures/gri_pipeline.pdf
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
OUTPUT_DIR = SCRIPT_DIR

# Style configuration
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
})


def load_scorecard_data():
    """Load the combined scorecards CSV."""
    csv_path = os.path.join(
        REPO_ROOT, 'analysis_output', 'scorecards', 'GD_combined_scorecards.csv'
    )
    if not os.path.exists(csv_path):
        print(f"ERROR: Cannot find {csv_path}")
        sys.exit(1)
    return pd.read_csv(csv_path)


def load_max_scores():
    """Load maximum possible scores summary."""
    csv_path = os.path.join(
        REPO_ROOT, 'analysis_output', 'max_possible_scores_summary.csv'
    )
    if not os.path.exists(csv_path):
        print(f"WARNING: Cannot find {csv_path}, skipping max scores")
        return None
    return pd.read_csv(csv_path)


def figure1_gri_scores_by_wave(df):
    """
    Multi-panel figure showing GRI scores across GD waves by dimension.
    """
    primary_dims = [
        'Country × Gender × Age',
        'Country × Religion',
        'Country × Environment',
    ]
    auxiliary_dims = [
        'Country',
        'Region',
        'Continent',
        'Religion',
        'Gender',
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    waves = sorted(df['gd'].unique())
    wave_nums_all = sorted([int(w.replace('GD', '')) for w in waves])
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(primary_dims)))

    # Panel A: Primary dimensions
    ax = axes[0]
    for i, dim in enumerate(primary_dims):
        dim_data = df[df['dimension'] == dim].sort_values('gd')
        wave_nums = [int(w.replace('GD', '')) for w in dim_data['gd']]
        ax.plot(wave_nums, dim_data['gri'], 'o-', color=colors[i],
                label=dim, linewidth=1.5, markersize=5)
    ax.set_xlabel('Global Dialogues Wave')
    ax.set_ylabel('GRI Score')
    ax.set_title('(a) Primary Dimensions')
    ax.set_xticks(wave_nums_all)
    ax.set_xticklabels([f'GD{i}' for i in wave_nums_all])
    ax.legend(fontsize=8, loc='upper left')
    ax.set_ylim(0, 1.05)
    ax.axhline(y=0.4, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.axhline(y=0.6, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.axhline(y=0.8, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.grid(axis='y', alpha=0.2)

    # Panel B: Auxiliary dimensions
    ax = axes[1]
    colors2 = plt.cm.plasma(np.linspace(0.2, 0.8, len(auxiliary_dims)))
    for i, dim in enumerate(auxiliary_dims):
        dim_data = df[df['dimension'] == dim].sort_values('gd')
        if len(dim_data) == 0:
            continue
        wave_nums = [int(w.replace('GD', '')) for w in dim_data['gd']]
        ax.plot(wave_nums, dim_data['gri'], 'o-', color=colors2[i],
                label=dim, linewidth=1.5, markersize=5)
    ax.set_xlabel('Global Dialogues Wave')
    ax.set_title('(b) Auxiliary Dimensions')
    ax.set_xticks(wave_nums_all)
    ax.set_xticklabels([f'GD{i}' for i in wave_nums_all])
    ax.legend(fontsize=8, loc='lower left')
    ax.axhline(y=0.4, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.axhline(y=0.6, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.axhline(y=0.8, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.grid(axis='y', alpha=0.2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'gri_scores_by_wave.pdf')
    plt.savefig(out_path)
    out_png = os.path.join(REPO_ROOT, 'site', 'images', 'gri_scores_by_wave.png')
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"  Saved: {out_path}")
    print(f"  Saved: {out_png}")


def figure2_efficiency_ratios(df):
    """
    Bar chart comparing actual GRI vs max-possible GRI (efficiency ratios).
    """
    primary_dims = [
        'Country × Gender × Age',
        'Country × Religion',
        'Country × Environment',
    ]
    max_gri_values = {
        'Country × Gender × Age': 0.792,
        'Country × Religion': 0.938,
        'Country × Environment': 0.950,
    }

    fig, ax = plt.subplots(figsize=(10, 5))

    waves = sorted(df['gd'].unique())
    x = np.arange(len(waves))
    width = 0.25
    colors = ['#2196F3', '#4CAF50', '#FF9800']

    for i, dim in enumerate(primary_dims):
        dim_data = df[df['dimension'] == dim].sort_values('gd')
        actual = dim_data['gri'].values
        max_val = max_gri_values[dim]
        efficiency = actual / max_val * 100

        bars = ax.bar(x + i * width, efficiency, width, label=dim,
                      color=colors[i], alpha=0.85)

        for bar, eff in zip(bars, efficiency):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.5,
                    f'{eff:.0f}%', ha='center', va='bottom', fontsize=6)

    ax.set_xlabel('Global Dialogues Wave')
    ax.set_ylabel('Efficiency Ratio (%)')
    ax.set_title('Sampling Efficiency: Actual GRI as Percentage of Maximum Achievable')
    ax.set_xticks(x + width)
    ax.set_xticklabels(waves)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 70)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.grid(axis='y', alpha=0.2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'efficiency_ratios.pdf')
    plt.savefig(out_path)
    out_png = os.path.join(REPO_ROOT, 'site', 'images', 'efficiency_ratios.png')
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"  Saved: {out_path}")
    print(f"  Saved: {out_png}")


def figure3_scorecard_heatmap(df):
    """
    Heatmap of the full scorecard data across all dimensions and waves.
    """
    dimensions_order = [
        'Gender',
        'Continent',
        'Religion',
        'Age Group',
        'Environment',
        'Region',
        'Region × Religion',
        'Region × Gender × Age',
        'Region × Environment',
        'Country',
        'Country × Religion',
        'Country × Environment',
        'Country × Gender × Age',
    ]

    pivot = df.pivot_table(index='dimension', columns='gd', values='gri')

    # Reorder
    available_dims = [d for d in dimensions_order if d in pivot.index]
    pivot = pivot.loc[available_dims]

    # Sort columns
    pivot = pivot[sorted(pivot.columns)]

    fig, ax = plt.subplots(figsize=(8, 7))

    cmap = LinearSegmentedColormap.from_list('gri',
        ['#d32f2f', '#ff9800', '#ffc107', '#8bc34a', '#4caf50'], N=256)

    im = ax.imshow(pivot.values, cmap=cmap, aspect='auto', vmin=0, vmax=1)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=0)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    # Annotate cells
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = 'white' if val < 0.5 else 'black'
                ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                        fontsize=7, color=text_color)

    cbar = plt.colorbar(im, ax=ax, label='GRI Score', shrink=0.8)
    ax.set_title('GRI Scorecard Heatmap: All Dimensions × All Waves')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'scorecard_heatmap.pdf')
    plt.savefig(out_path)
    out_png = os.path.join(REPO_ROOT, 'site', 'images', 'scorecard_heatmap.png')
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"  Saved: {out_path}")
    print(f"  Saved: {out_png}")


def figure4_pipeline_diagram():
    """
    Diagram illustrating the GRI calculation pipeline.
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')

    box_style = dict(boxstyle='round,pad=0.4', facecolor='#e3f2fd',
                     edgecolor='#1565c0', linewidth=1.5)
    result_style = dict(boxstyle='round,pad=0.4', facecolor='#e8f5e9',
                        edgecolor='#2e7d32', linewidth=1.5)
    arrow_props = dict(arrowstyle='->', color='#455a64', lw=1.5)

    # Input boxes
    ax.text(0.8, 3.2, 'Survey\nData', ha='center', va='center',
            fontsize=9, fontweight='bold', bbox=box_style)
    ax.text(0.8, 0.8, 'Population\nBenchmarks', ha='center', va='center',
            fontsize=9, fontweight='bold', bbox=box_style)

    # Processing
    ax.text(3.2, 2.0, 'Compute\nProportions\n$p_i$, $q_i$', ha='center', va='center',
            fontsize=9, bbox=box_style)

    # Core calculation
    ax.text(5.5, 2.0, 'Calculate\nTVD\n$\\frac{1}{2}\\sum|p_i - q_i|$',
            ha='center', va='center', fontsize=9, bbox=box_style)

    # Outputs
    ax.text(8.0, 3.2, 'GRI Score\n$1 - \\mathrm{TVD}$', ha='center', va='center',
            fontsize=9, fontweight='bold', bbox=result_style)
    ax.text(8.0, 2.0, 'Diversity\nScore', ha='center', va='center',
            fontsize=9, fontweight='bold', bbox=result_style)
    ax.text(8.0, 0.8, 'Segment\nDeviations', ha='center', va='center',
            fontsize=9, fontweight='bold', bbox=result_style)

    # Arrows
    ax.annotate('', xy=(2.2, 2.4), xytext=(1.5, 3.0), arrowprops=arrow_props)
    ax.annotate('', xy=(2.2, 1.6), xytext=(1.5, 1.0), arrowprops=arrow_props)
    ax.annotate('', xy=(4.5, 2.0), xytext=(4.0, 2.0), arrowprops=arrow_props)
    ax.annotate('', xy=(7.0, 3.0), xytext=(6.5, 2.4), arrowprops=arrow_props)
    ax.annotate('', xy=(7.0, 2.0), xytext=(6.5, 2.0), arrowprops=arrow_props)
    ax.annotate('', xy=(7.0, 1.0), xytext=(6.5, 1.6), arrowprops=arrow_props)

    ax.set_title('GRI Calculation Pipeline', fontsize=12, fontweight='bold', pad=10)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'gri_pipeline.pdf')
    plt.savefig(out_path)
    out_png = os.path.join(REPO_ROOT, 'site', 'images', 'gri_pipeline.png')
    plt.savefig(out_png, dpi=200)
    plt.close()
    print(f"  Saved: {out_path}")
    print(f"  Saved: {out_png}")


def main():
    print("Generating figures for GRI Whitepaper...")
    print(f"  Repository root: {REPO_ROOT}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print()

    # Ensure site images directory exists
    site_images = os.path.join(REPO_ROOT, 'site', 'images')
    os.makedirs(site_images, exist_ok=True)

    df = load_scorecard_data()
    print(f"  Loaded scorecard data: {len(df)} rows")

    print("\n--- Figure 1: GRI Scores by Wave ---")
    figure1_gri_scores_by_wave(df)

    print("\n--- Figure 2: Efficiency Ratios ---")
    figure2_efficiency_ratios(df)

    print("\n--- Figure 3: Scorecard Heatmap ---")
    figure3_scorecard_heatmap(df)

    print("\n--- Figure 4: Pipeline Diagram ---")
    figure4_pipeline_diagram()

    print("\nDone! All figures saved to:", OUTPUT_DIR)


if __name__ == '__main__':
    main()
