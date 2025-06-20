#!/usr/bin/env python3
"""
Demonstration of VWRS (Variance-Weighted Representativeness Score) calculation.

This example shows how VWRS differs from traditional GRI by accounting for
sampling reliability and within-group variance.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from gri.calculator import calculate_gri
from gri.variance_weighted import calculate_vwrs_from_dataframes


def create_example_data():
    """Create example survey and benchmark data."""
    
    # Example survey data - notice the sample sizes vary greatly
    survey_data = []
    
    # USA: 50 respondents (well-sampled)
    for i in range(50):
        survey_data.append({
            'country': 'USA',
            'gender': 'Male' if i < 30 else 'Female',
            'participant_id': f'usa_{i}'
        })
    
    # China: 100 respondents (well-sampled)
    for i in range(100):
        survey_data.append({
            'country': 'China',
            'gender': 'Male' if i < 45 else 'Female',
            'participant_id': f'china_{i}'
        })
    
    # Denmark: 2 respondents (poorly sampled)
    survey_data.extend([
        {'country': 'Denmark', 'gender': 'Male', 'participant_id': 'den_1'},
        {'country': 'Denmark', 'gender': 'Female', 'participant_id': 'den_2'}
    ])
    
    # Luxembourg: 1 respondent (very poorly sampled)
    survey_data.append({
        'country': 'Luxembourg', 
        'gender': 'Female', 
        'participant_id': 'lux_1'
    })
    
    # Malta: 0 respondents (not sampled at all)
    
    survey_df = pd.DataFrame(survey_data)
    
    # Benchmark data (true population proportions)
    benchmark_data = [
        {'country': 'USA', 'population_proportion': 0.30},      # 30% of population
        {'country': 'China', 'population_proportion': 0.40},    # 40% of population
        {'country': 'Denmark', 'population_proportion': 0.02},  # 2% of population
        {'country': 'Luxembourg', 'population_proportion': 0.01}, # 1% of population
        {'country': 'Malta', 'population_proportion': 0.01},    # 1% of population
        {'country': 'Others', 'population_proportion': 0.26}    # 26% of population
    ]
    
    benchmark_df = pd.DataFrame(benchmark_data)
    
    # Example within-stratum variances (from historical data or agreement rates)
    # High variance = less internal consensus
    within_variances = {
        'USA': 0.15,        # Moderate internal variance
        'China': 0.08,      # Low internal variance (high consensus)
        'Denmark': 0.25,    # High internal variance (diverse opinions)
        'Luxembourg': 0.20, # High-moderate variance
        'Malta': 0.18,      # Moderate variance
        'Others': 0.12      # Moderate variance
    }
    
    return survey_df, benchmark_df, within_variances


def main():
    """Demonstrate VWRS calculation and compare with traditional GRI."""
    
    print("VWRS (Variance-Weighted Representativeness Score) Demo")
    print("=" * 60)
    
    # Create example data
    survey_df, benchmark_df, within_variances = create_example_data()
    
    # Show sample distribution
    print("\nSample Distribution:")
    sample_counts = survey_df['country'].value_counts()
    total_sample = len(survey_df)
    print(f"Total sample size: {total_sample}")
    for country, count in sample_counts.items():
        print(f"  {country}: {count} respondents ({count/total_sample*100:.1f}%)")
    print("  Malta: 0 respondents (0.0%)")
    
    # Calculate traditional GRI
    traditional_gri = calculate_gri(survey_df, benchmark_df, ['country'])
    print(f"\nTraditional GRI: {traditional_gri:.4f}")
    
    # Calculate VWRS without variance information
    vwrs_basic, details_basic = calculate_vwrs_from_dataframes(
        survey_df, benchmark_df, ['country']
    )
    print(f"VWRS (basic): {vwrs_basic:.4f}")
    
    # Calculate VWRS with variance information
    vwrs_full, details_full = calculate_vwrs_from_dataframes(
        survey_df, benchmark_df, ['country'], within_variances
    )
    print(f"VWRS (with variance): {vwrs_full:.4f}")
    
    # Show detailed breakdown
    print("\n" + "=" * 60)
    print("Detailed Breakdown (VWRS with variance):")
    print("=" * 60)
    
    print(details_full[[
        'stratum', 'population_prop', 'sample_prop', 'sample_count',
        'standard_error', 'reliability', 'normalized_weight', 'weighted_contribution'
    ]].round(4).to_string(index=False))
    
    # Explain the differences
    print("\n" + "=" * 60)
    print("Key Insights:")
    print("=" * 60)
    
    print(f"\n1. Score Comparison:")
    print(f"   - Traditional GRI: {traditional_gri:.4f}")
    print(f"   - Basic VWRS: {vwrs_basic:.4f} (improvement: {vwrs_basic - traditional_gri:+.4f})")
    print(f"   - Full VWRS: {vwrs_full:.4f} (improvement: {vwrs_full - traditional_gri:+.4f})")
    
    print(f"\n2. Why VWRS is higher:")
    print(f"   - Small countries (Denmark, Luxembourg) get less weight due to high standard error")
    print(f"   - Missing Malta (1% of population) is penalized less than in traditional GRI")
    print(f"   - China's low internal variance increases its reliability weight")
    
    print(f"\n3. Weighted Contributions to Error:")
    # Find biggest contributors
    top_errors = details_full.nlargest(3, 'weighted_contribution')
    for _, row in top_errors.iterrows():
        print(f"   - {row['stratum']}: {row['weighted_contribution']:.4f} " +
              f"(pop: {row['population_prop']*100:.1f}%, " +
              f"sample: {row['sample_prop']*100:.1f}%, " +
              f"n={int(row['sample_count'])})")
    
    # Multi-dimensional example
    print("\n" + "=" * 60)
    print("Multi-dimensional Example (Country × Gender):")
    print("=" * 60)
    
    # Create gender benchmark
    gender_benchmark = []
    for _, country_row in benchmark_df.iterrows():
        country = country_row['country']
        country_prop = country_row['population_proportion']
        # Assume 50/50 gender split globally
        gender_benchmark.append({
            'country': country,
            'gender': 'Male',
            'population_proportion': country_prop * 0.5
        })
        gender_benchmark.append({
            'country': country,
            'gender': 'Female',
            'population_proportion': country_prop * 0.5
        })
    
    gender_benchmark_df = pd.DataFrame(gender_benchmark)
    
    # Calculate for gender dimension
    gri_gender = calculate_gri(survey_df, gender_benchmark_df, ['country', 'gender'])
    vwrs_gender, _ = calculate_vwrs_from_dataframes(
        survey_df, gender_benchmark_df, ['country', 'gender']
    )
    
    print(f"Traditional GRI: {gri_gender:.4f}")
    print(f"VWRS: {vwrs_gender:.4f} (improvement: {vwrs_gender - gri_gender:+.4f})")
    
    print("\nConclusion:")
    print("-" * 60)
    print("VWRS provides a more nuanced measure of representativeness by:")
    print("1. Accounting for sampling reliability (standard error)")
    print("2. Incorporating within-group variance/consensus")
    print("3. Weighting errors by their statistical importance")
    print("\nThis prevents over-penalizing unavoidable variance in small demographics.")


if __name__ == "__main__":
    main()