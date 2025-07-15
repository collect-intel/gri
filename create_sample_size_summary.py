#!/usr/bin/env python3
"""Create a focused summary of sample size effects on representativeness scores."""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_summary_visualization():
    """Create a focused 2x2 plot showing key patterns."""
    
    # Data from the analysis (Country dimension, mean values)
    sample_sizes = [50, 100, 200, 500, 971]
    
    # GRI scores
    gri_auto = [0.298, 0.389, 0.476, 0.526, 0.552]
    gri_legacy = [0.410, 0.465, 0.509, 0.531, 0.539]
    gri_none = [0.395, 0.464, 0.510, 0.545, 0.559]
    
    # Diversity scores
    div_auto = [0.556, 0.560, 0.583, 0.457, 0.451]
    div_legacy = [0.656, 0.676, 0.760, 0.821, 0.828]
    div_none = [0.625, 0.589, 0.600, 0.464, 0.455]
    
    # SRI scores
    sri_auto = [0.334, 0.393, 0.464, 0.465, 0.453]
    sri_legacy = [0.460, 0.510, 0.544, 0.557, 0.555]
    sri_none = [0.264, 0.340, 0.376, 0.409, 0.421]
    
    # VWRS scores
    vwrs_auto = [0.651, 0.804, 0.899, 0.968, 0.982]
    vwrs_legacy = [0.838, 0.815, 0.798, 0.786, 0.782]
    vwrs_none = [0.980, 0.982, 0.984, 0.984, 0.985]
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Sample Size Effects on Representativeness Scores (Country Dimension)', fontsize=16)
    
    # Plot 1: GRI
    ax1 = axes[0, 0]
    ax1.plot(sample_sizes, gri_auto, 'o-', label='Auto mode', linewidth=2, markersize=8)
    ax1.plot(sample_sizes, gri_legacy, 's-', label='Legacy mode', linewidth=2, markersize=8)
    ax1.plot(sample_sizes, gri_none, '^-', label='None mode', linewidth=2, markersize=8)
    ax1.set_xlabel('Sample Size')
    ax1.set_ylabel('GRI Score')
    ax1.set_title('GRI: Stable across modes')
    ax1.set_xscale('log')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.set_ylim(0.2, 0.6)
    
    # Plot 2: Diversity
    ax2 = axes[0, 1]
    ax2.plot(sample_sizes, div_auto, 'o-', label='Auto mode', linewidth=2, markersize=8)
    ax2.plot(sample_sizes, div_legacy, 's-', label='Legacy mode', linewidth=2, markersize=8)
    ax2.plot(sample_sizes, div_none, '^-', label='None mode', linewidth=2, markersize=8)
    ax2.set_xlabel('Sample Size')
    ax2.set_ylabel('Diversity Score')
    ax2.set_title('Diversity: Mode matters significantly')
    ax2.set_xscale('log')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_ylim(0.4, 0.9)
    
    # Plot 3: SRI
    ax3 = axes[1, 0]
    ax3.plot(sample_sizes, sri_auto, 'o-', label='Auto mode', linewidth=2, markersize=8)
    ax3.plot(sample_sizes, sri_legacy, 's-', label='Legacy mode', linewidth=2, markersize=8)
    ax3.plot(sample_sizes, sri_none, '^-', label='None mode', linewidth=2, markersize=8)
    ax3.set_xlabel('Sample Size')
    ax3.set_ylabel('SRI Score')
    ax3.set_title('SRI: Strategic allocation effects')
    ax3.set_xscale('log')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.set_ylim(0.2, 0.6)
    
    # Plot 4: VWRS
    ax4 = axes[1, 1]
    ax4.plot(sample_sizes, vwrs_auto, 'o-', label='Auto mode', linewidth=2, markersize=8)
    ax4.plot(sample_sizes, vwrs_legacy, 's-', label='Legacy mode', linewidth=2, markersize=8)
    ax4.plot(sample_sizes, vwrs_none, '^-', label='None mode', linewidth=2, markersize=8)
    ax4.set_xlabel('Sample Size')
    ax4.set_ylabel('VWRS Score')
    ax4.set_title('VWRS: Most affected by simplification')
    ax4.set_xscale('log')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.set_ylim(0.6, 1.0)
    
    # Add annotations
    ax4.annotate('Threshold changes\nwith sample size', 
                xy=(100, 0.804), xytext=(60, 0.72),
                arrowprops=dict(arrowstyle='->', color='gray'),
                ha='center')
    
    plt.tight_layout()
    plt.savefig('sample_size_summary.png', dpi=150, bbox_inches='tight')
    print("Summary visualization saved as: sample_size_summary.png")
    
    # Create comparison table
    print("\n" + "=" * 80)
    print("SCORE SENSITIVITY TO SAMPLE SIZE")
    print("=" * 80)
    print("\nRelative change from n=50 to n=971:")
    print("-" * 60)
    print(f"{'Metric':<15} {'Auto Mode':<20} {'Legacy Mode':<20} {'None Mode':<20}")
    print("-" * 60)
    
    # Calculate relative changes
    metrics = {
        'GRI': {
            'auto': (gri_auto[-1] - gri_auto[0]) / gri_auto[0] * 100,
            'legacy': (gri_legacy[-1] - gri_legacy[0]) / gri_legacy[0] * 100,
            'none': (gri_none[-1] - gri_none[0]) / gri_none[0] * 100
        },
        'Diversity': {
            'auto': (div_auto[-1] - div_auto[0]) / div_auto[0] * 100,
            'legacy': (div_legacy[-1] - div_legacy[0]) / div_legacy[0] * 100,
            'none': (div_none[-1] - div_none[0]) / div_none[0] * 100
        },
        'SRI': {
            'auto': (sri_auto[-1] - sri_auto[0]) / sri_auto[0] * 100,
            'legacy': (sri_legacy[-1] - sri_legacy[0]) / sri_legacy[0] * 100,
            'none': (sri_none[-1] - sri_none[0]) / sri_none[0] * 100
        },
        'VWRS': {
            'auto': (vwrs_auto[-1] - vwrs_auto[0]) / vwrs_auto[0] * 100,
            'legacy': (vwrs_legacy[-1] - vwrs_legacy[0]) / vwrs_legacy[0] * 100,
            'none': (vwrs_none[-1] - vwrs_none[0]) / vwrs_none[0] * 100
        }
    }
    
    for metric, changes in metrics.items():
        print(f"{metric:<15} {changes['auto']:>+18.1f}% {changes['legacy']:>+18.1f}% {changes['none']:>+18.1f}%")
    
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print("\n1. GRI increases ~30-85% with larger samples")
    print("   - Most stable metric across modes")
    print("   - Converges to similar values regardless of simplification")
    
    print("\n2. Diversity behavior varies by mode:")
    print("   - Auto/None: Decreases as harder to cover 100+ countries")
    print("   - Legacy: Increases as easier to cover 31 countries")
    
    print("\n3. SRI shows moderate increases (35-60%)")
    print("   - Legacy mode benefits most from strategic allocation")
    
    print("\n4. VWRS is highly mode-dependent:")
    print("   - Auto: +51% (threshold effect)")
    print("   - Legacy: -7% (more conservative with larger samples)")
    print("   - None: +0.5% (already near maximum)")

if __name__ == "__main__":
    create_summary_visualization()