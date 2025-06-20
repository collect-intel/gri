#!/usr/bin/env python3
"""
Calculate VWRS for any GD survey using actual variance data.

Usage: python vwrs_gd_analysis.py <N>
where N is the GD survey number (1, 2, or 3)

This demonstrates how VWRS compares to traditional GRI on real survey data.
"""

import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from gri.calculator import calculate_gri
from gri.variance_weighted import calculate_vwrs_from_dataframes
from gri.strategic_index import calculate_sri_from_dataframes
from gri.simulation import monte_carlo_max_scores


def load_gd_data(base_path: Path, gd_num: int):
    """Load GD survey data and standardize columns."""
    df = pd.read_csv(
        base_path / f'data/raw/survey_data/global-dialogues/Data/GD{gd_num}/GD{gd_num}_participants.csv'
    )
    
    # Standardize column names
    column_mapping = {
        'What country or region do you most identify with?': 'country',
        'What is your gender?': 'gender',
        'How old are you?': 'age_group',
        'What best describes where you live?': 'environment',
        'What religious group or faith do you most identify with?': 'religion'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Standardize environment
    if 'environment' in df.columns:
        df['environment'] = df['environment'].replace({'Suburban': 'Urban'})
    
    return df


def create_simple_country_benchmark():
    """Create simplified country benchmark for demonstration."""
    # Major countries by population (simplified)
    benchmark_data = [
        {'country': 'China', 'population_proportion': 0.180},
        {'country': 'India', 'population_proportion': 0.175},
        {'country': 'United States', 'population_proportion': 0.042},
        {'country': 'Indonesia', 'population_proportion': 0.035},
        {'country': 'Pakistan', 'population_proportion': 0.028},
        {'country': 'Brazil', 'population_proportion': 0.027},
        {'country': 'Nigeria', 'population_proportion': 0.026},
        {'country': 'Bangladesh', 'population_proportion': 0.021},
        {'country': 'Russian Federation', 'population_proportion': 0.018},
        {'country': 'Mexico', 'population_proportion': 0.016},
        {'country': 'Japan', 'population_proportion': 0.016},
        {'country': 'Ethiopia', 'population_proportion': 0.015},
        {'country': 'Philippines', 'population_proportion': 0.014},
        {'country': 'Egypt', 'population_proportion': 0.013},
        {'country': 'Viet Nam', 'population_proportion': 0.012},
        {'country': 'Türkiye', 'population_proportion': 0.011},
        {'country': 'Germany', 'population_proportion': 0.010},
        {'country': 'United Kingdom', 'population_proportion': 0.008},
        {'country': 'France', 'population_proportion': 0.008},
        {'country': 'Italy', 'population_proportion': 0.007},
        {'country': 'South Africa', 'population_proportion': 0.007},
        {'country': 'Kenya', 'population_proportion': 0.007},
        {'country': 'South Korea', 'population_proportion': 0.006},
        {'country': 'Spain', 'population_proportion': 0.006},
        {'country': 'Canada', 'population_proportion': 0.005},
        {'country': 'Poland', 'population_proportion': 0.005},
        {'country': 'Australia', 'population_proportion': 0.003},
        {'country': 'Netherlands', 'population_proportion': 0.002},
        {'country': 'Belgium', 'population_proportion': 0.001},
        {'country': 'Sweden', 'population_proportion': 0.001},
        {'country': 'Denmark', 'population_proportion': 0.001},
    ]
    
    # Add all other countries as "Others"
    total_listed = sum(item['population_proportion'] for item in benchmark_data)
    benchmark_data.append({
        'country': 'Others',
        'population_proportion': 1.0 - total_listed
    })
    
    return pd.DataFrame(benchmark_data)


def load_variance_data(base_path: Path, gd_num: int):
    """Load variance data from previous analysis."""
    variance_file = base_path / f'analysis_output/demographic_variance/GD{gd_num}_variance_lookup.json'
    
    if variance_file.exists():
        with open(variance_file, 'r') as f:
            variance_data = json.load(f)
        
        # Extract country variances
        if 'Country' in variance_data:
            return variance_data['Country']
    
    return None


def main():
    """Analyze GD survey with VWRS."""
    # Parse command line arguments
    if len(sys.argv) != 2:
        print("Usage: python vwrs_gd_analysis.py <N>")
        print("where N is the GD survey number (1, 2, or 3)")
        sys.exit(1)
    
    try:
        gd_num = int(sys.argv[1])
        if gd_num not in [1, 2, 3]:
            raise ValueError("GD number must be 1, 2, or 3")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    base_path = Path(__file__).parent.parent
    
    print(f"Representativeness Analysis of GD{gd_num} Survey Data")
    print("=" * 70)
    print("\nComparing three approaches to measuring representativeness:")
    print("1. GRI - Traditional proportional representation")
    print("2. SRI - Strategic allocation (balances large and small groups)")
    print("3. VWRS - Variance-weighted (accounts for reliability and consensus)")
    
    # Load survey data
    print(f"\nLoading GD{gd_num} data...")
    survey_df = load_gd_data(base_path, gd_num)
    print(f"Total participants: {len(survey_df)}")
    
    # Show sample distribution
    print("\nTop 20 Countries by Sample Size:")
    country_counts = survey_df['country'].value_counts()
    for country, count in country_counts.head(20).items():
        print(f"  {country}: {count} ({count/len(survey_df)*100:.1f}%)")
    
    # Create benchmark
    benchmark_df = create_simple_country_benchmark()
    
    # Calculate all three metrics
    print("\n" + "=" * 70)
    print("Country-Level Analysis:")
    print("=" * 70)
    
    # Traditional GRI
    gri = calculate_gri(survey_df, benchmark_df, ['country'])
    print(f"\n1. Traditional GRI: {gri:.4f}")
    print("   (Perfect score = proportional representation)")
    
    # Strategic Representativeness Index
    sri, sri_details = calculate_sri_from_dataframes(survey_df, benchmark_df, ['country'])
    print(f"\n2. Strategic Representativeness Index (SRI): {sri:.4f}")
    print("   (Perfect score = optimal allocation for minimizing uncertainty)")
    
    # Calculate basic VWRS (no variance info)
    vwrs_basic, details_basic = calculate_vwrs_from_dataframes(
        survey_df, benchmark_df, ['country']
    )
    print(f"\n3. VWRS (basic): {vwrs_basic:.4f}")
    print("   (Accounts for sampling reliability)")
    
    # Load variance data if available
    variance_data = load_variance_data(base_path, gd_num)
    if variance_data:
        print("\nUsing within-group variance data from previous analysis...")
        print("(This adjusts weights based on how much responses vary within each country)")
        vwrs_full, details_full = calculate_vwrs_from_dataframes(
            survey_df, benchmark_df, ['country'], variance_data
        )
        print(f"\n4. VWRS (with internal variance): {vwrs_full:.4f}")
        print("   (Also accounts for within-group consensus)")
        
        # Show which countries benefit most from VWRS
        print("\n" + "-" * 70)
        print("How Internal Variance Affects Country Weights:")
        print("-" * 70)
        print("(Comparing VWRS basic vs. VWRS with internal variance)")
        
        # Compare weights
        details_basic['weight_change'] = details_full['normalized_weight'] - details_basic['normalized_weight']
        weight_changes = details_full.copy()
        weight_changes['weight_change'] = details_basic['weight_change']
        
        print("\nCountries given MORE weight (high internal consensus):")
        for _, row in weight_changes.nlargest(5, 'weight_change').iterrows():
            if row['stratum'] != 'Others':
                # Default variance of 0.25 (maximum for binary outcomes) when no data
                variance = variance_data.get(row['stratum'], 0.25)
                consensus = 1 - variance
                print(f"  {row['stratum']}: {row['weight_change']:+.4f} weight change " +
                      f"(n={int(row['sample_count'])}, variance={variance:.3f}, consensus={consensus:.0%})")
        
        print("\nCountries given LESS weight (high internal disagreement):")
        for _, row in weight_changes.nsmallest(5, 'weight_change').iterrows():
            if row['stratum'] != 'Others':
                # Countries with actual data have lower variance (more consensus)
                # Countries without data get default variance of 0.25
                variance = variance_data.get(row['stratum'], 0.25)
                consensus = 1 - variance
                print(f"  {row['stratum']}: {row['weight_change']:+.4f} weight change " +
                      f"(n={int(row['sample_count'])}, variance={variance:.3f}, consensus={consensus:.0%})")
    
    # Show error contributions
    print("\n" + "-" * 70)
    print("Top Contributors to Representation Error:")
    print("-" * 70)
    
    details_to_show = details_full if variance_data else details_basic
    
    # Calculate total error for percentage calculation
    total_error = details_to_show['weighted_contribution'].sum()
    vwrs_score = vwrs_full if variance_data else vwrs_basic
    
    # Add percentage column
    details_to_show['error_percent'] = (details_to_show['weighted_contribution'] / total_error * 100)
    
    top_errors = details_to_show.nlargest(10, 'weighted_contribution')
    
    print(f"{'Country':<20} {'Pop %':>8} {'Sample %':>10} {'n':>5} {'Error':>10} {'% of Total':>11}")
    print("-" * 70)
    for _, row in top_errors.iterrows():
        print(f"{row['stratum']:<20} {row['population_prop']*100:>7.1f}% " +
              f"{row['sample_prop']*100:>9.1f}% {int(row['sample_count']):>5} " +
              f"{row['weighted_contribution']:>10.4f} {row['error_percent']:>10.1f}%")
    
    # Show SRI strategic targets
    print("\n" + "-" * 70)
    print("Strategic Allocation Targets (SRI):")
    print("-" * 70)
    print("Showing how SRI targets differ from proportional representation:")
    print("Top 10 most-boosted countries (smallest countries get biggest boost):")
    print(f"\n{'Country':<20} {'Pop %':>8} {'Target %':>10} {'Boost':>8}")
    print("-" * 50)
    
    # Calculate boost factor and filter out 'Others' and countries with zero population
    sri_details = sri_details[sri_details['stratum'] != 'Others'].copy()
    sri_details = sri_details[sri_details['population_prop'] > 0].copy()
    sri_details['boost_factor'] = sri_details['strategic_target'] / sri_details['population_prop']
    
    # Show top boosted countries (sorted by boost factor)
    for _, row in sri_details.nlargest(10, 'boost_factor').iterrows():
        print(f"{row['stratum']:<20} {row['population_prop']*100:>7.1f}% " +
              f"{row['strategic_target']*100:>9.1f}% {row['boost_factor']:>7.1f}x")
    
    # Calculate maximum possible GRI for this sample size
    print("\n" + "-" * 70)
    print("Maximum Possible GRI Analysis:")
    print("-" * 70)
    
    total_sample_size = len(survey_df)
    max_gri_results = monte_carlo_max_scores(
        benchmark_df, 
        total_sample_size,
        dimension_columns=['country'],
        n_simulations=1000,
        include_diversity=False
    )
    
    max_gri_mean = max_gri_results['max_gri']['mean']
    max_gri_std = max_gri_results['max_gri']['std']
    
    print(f"For a sample size of {total_sample_size}:")
    print(f"  Maximum possible GRI: {max_gri_mean:.4f} ± {max_gri_std:.4f}")
    print(f"  Current GRI achievement: {gri/max_gri_mean*100:.1f}% of maximum")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("Score Summary:")
    print("=" * 70)
    print(f"\nMetric Comparison:")
    print(f"  Traditional GRI:  {gri:.4f} ({gri/max_gri_mean*100:.1f}% of max possible)")
    print(f"  SRI:             {sri:.4f}")
    print(f"  VWRS (basic):    {vwrs_basic:.4f}")
    if variance_data:
        print(f"  VWRS (full):     {vwrs_full:.4f}")
    print(f"  Max Possible GRI: {max_gri_mean:.4f} ± {max_gri_std:.4f}")
    
    # Summary insights
    print("\n" + "=" * 70)
    print("Key Insights:")
    print("=" * 70)
    
    print(f"\n1. Traditional GRI ({gri:.4f}) measures proportional representation")
    print("   - Penalizes all deviations equally")
    print(f"   - Achieves {gri/max_gri_mean*100:.1f}% of the maximum possible GRI for this sample size")
    print("   - Best when you need exact demographic matching")
    
    print(f"\n2. SRI ({sri:.4f}) measures strategic representation") 
    print("   - Targets sqrt(population) allocation")
    print("   - Balances between equal and proportional representation")
    print("   - Small countries get boosted (see table above)")
    print("   - Best for minimizing total survey uncertainty")
    
    print(f"\n3. VWRS ({vwrs_basic:.4f}) measures reliable representation")
    print("   - Weights by statistical reliability")
    print("   - Small/unreliable samples contribute less to score")
    print("   - Closer to 1.0 suggests good coverage of statistically meaningful groups")
    print("   - Perfect VWRS=1.0 would mean perfect match weighted by reliability")
    
    if variance_data:
        print(f"\n4. With internal variance, VWRS changes by {vwrs_full - vwrs_basic:+.4f}")
        print("   - Countries WITHOUT survey data get default variance of 0.25 (75% consensus)")
        print("   - Countries WITH survey data have measured variance (typically lower = higher consensus)")
        print("   - This explains the counterintuitive consensus labels above")
    
    print(f"\n5. Maximum Possible GRI ({max_gri_mean:.4f}) represents perfect sampling")
    print("   - Even with optimal allocation, perfect GRI=1.0 is impossible with finite samples")
    print(f"   - Current survey achieves {gri/max_gri_mean*100:.1f}% of the theoretical maximum")


if __name__ == "__main__":
    main()