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

from gri.calculator import calculate_gri, calculate_diversity_score
from gri.variance_weighted import calculate_vwrs_from_dataframes
from gri.strategic_index import calculate_sri_from_dataframes
from gri.simulation import monte_carlo_max_scores
from gri.utils import load_data


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


def calculate_multi_dimension_gri(survey_df: pd.DataFrame, base_path: Path):
    """Calculate GRI scores across multiple dimensions."""
    results = {}
    
    # Load all benchmark data
    benchmarks = {
        'Country × Gender × Age': load_data(base_path / 'data/processed/benchmark_country_gender_age.csv'),
        'Country × Religion': load_data(base_path / 'data/processed/benchmark_country_religion.csv'),
        'Country × Environment': load_data(base_path / 'data/processed/benchmark_country_environment.csv'),
        'Country': create_simple_country_benchmark()
    }
    
    # Define dimension columns
    dimension_cols = {
        'Country × Gender × Age': ['country', 'gender', 'age_group'],
        'Country × Religion': ['country', 'religion'],
        'Country × Environment': ['country', 'environment'],
        'Country': ['country']
    }
    
    # Calculate GRI for each dimension
    for dim_name, benchmark_df in benchmarks.items():
        try:
            cols = dimension_cols[dim_name]
            # Check if all required columns exist in survey data
            if all(col in survey_df.columns for col in cols):
                gri = calculate_gri(survey_df, benchmark_df, cols)
                diversity = calculate_diversity_score(survey_df, benchmark_df, cols)
                results[dim_name] = {'gri': gri, 'diversity': diversity}
            else:
                results[dim_name] = {'gri': None, 'diversity': None, 'error': 'Missing columns'}
        except Exception as e:
            results[dim_name] = {'gri': None, 'diversity': None, 'error': str(e)}
    
    # Calculate overall average (excluding None values)
    valid_gris = [r['gri'] for r in results.values() if r['gri'] is not None]
    if valid_gris:
        results['Overall (Average)'] = {
            'gri': sum(valid_gris) / len(valid_gris),
            'diversity': None  # Diversity average not meaningful
        }
    
    return results


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
    
    # Calculate all metrics for Country dimension
    print("\n" + "=" * 70)
    print("Analysis by COUNTRY Dimension:")
    print("=" * 70)
    print("Note: All metrics below are calculated for country-level representation only.")
    print("Full GRI would also include other dimensions (age×gender, religion, etc.)")
    
    # Traditional GRI for Country dimension
    gri = calculate_gri(survey_df, benchmark_df, ['country'])
    print(f"\n1. Traditional GRI (Country): {gri:.4f}")
    print("   (Perfect score = proportional representation by country)")
    
    # Diversity Score for Country dimension
    diversity = calculate_diversity_score(survey_df, benchmark_df, ['country'])
    threshold = 1.0 / (2 * len(survey_df))
    print(f"\n2. Diversity Score (Country): {diversity:.4f}")
    print(f"   (Coverage of countries with population > {threshold:.5f})")
    
    # Strategic Representativeness Index
    sri, sri_details = calculate_sri_from_dataframes(survey_df, benchmark_df, ['country'])
    print(f"\n3. Strategic Representativeness Index (SRI): {sri:.4f}")
    print("   (Perfect score = optimal allocation for minimizing uncertainty)")
    
    # Calculate basic VWRS (no variance info)
    vwrs_basic, details_basic = calculate_vwrs_from_dataframes(
        survey_df, benchmark_df, ['country']
    )
    print(f"\n4. VWRS (basic): {vwrs_basic:.4f}")
    print("   (Accounts for sampling reliability)")
    
    # Load variance data if available
    variance_data = load_variance_data(base_path, gd_num)
    if variance_data:
        print("\nUsing within-group variance data from previous analysis...")
        print("(This adjusts weights based on how much responses vary within each country)")
        vwrs_full, details_full = calculate_vwrs_from_dataframes(
            survey_df, benchmark_df, ['country'], variance_data
        )
        print(f"\n5. VWRS (with internal variance): {vwrs_full:.4f}")
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
        
        # Separate countries with and without variance data
        print("\nCountries with NO survey data (using conservative default variance):")
        no_data_countries = []
        for _, row in weight_changes.iterrows():
            if row['stratum'] != 'Others' and row['sample_count'] == 0:
                # These countries use default variance of 0.25
                has_variance_data = row['stratum'] in variance_data
                variance_used = variance_data.get(row['stratum'], 0.25)
                no_data_countries.append((row, variance_used, has_variance_data))
        
        # Sort by weight change and show top 5
        no_data_countries.sort(key=lambda x: x[0]['weight_change'], reverse=True)
        for row, variance, has_data in no_data_countries[:5]:
            status = "measured" if has_data else "default"
            print(f"  {row['stratum']}: {row['weight_change']:+.4f} weight change " +
                  f"(n=0, {status} variance={variance:.3f})")
        
        print("\nCountries WITH survey data (using measured response variance):")
        with_data_countries = []
        for _, row in weight_changes.iterrows():
            if row['stratum'] != 'Others' and row['sample_count'] > 0:
                variance = variance_data.get(row['stratum'], 0.25)
                with_data_countries.append((row, variance))
        
        # Sort by weight change (most negative = less weight)
        with_data_countries.sort(key=lambda x: x[0]['weight_change'])
        for row, variance in with_data_countries[:5]:
            agreement_level = "high agreement" if variance < 0.1 else "moderate agreement"
            print(f"  {row['stratum']}: {row['weight_change']:+.4f} weight change " +
                  f"(n={int(row['sample_count'])}, measured variance={variance:.3f}, {agreement_level})")
    
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
    
    # Calculate maximum possible scores for this sample size
    print("\n" + "-" * 70)
    print("Maximum Possible Scores Analysis (Country Dimension):")
    print("-" * 70)
    
    total_sample_size = len(survey_df)
    max_results = monte_carlo_max_scores(
        benchmark_df, 
        total_sample_size,
        dimension_columns=['country'],
        n_simulations=1000,
        include_diversity=True
    )
    
    max_gri_mean = max_results['max_gri']['mean']
    max_gri_std = max_results['max_gri']['std']
    max_div_mean = max_results['max_diversity']['mean']
    max_div_std = max_results['max_diversity']['std']
    
    print(f"For a sample size of {total_sample_size} (Country dimension only):")
    print(f"  Maximum possible GRI: {max_gri_mean:.4f} ± {max_gri_std:.4f}")
    print(f"  Maximum possible Diversity: {max_div_mean:.4f} ± {max_div_std:.4f}")
    print(f"\nCurrent achievement rates:")
    print(f"  GRI: {gri/max_gri_mean*100:.1f}% of maximum possible")
    print(f"  Diversity: {diversity/max_div_mean*100:.1f}% of maximum possible")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("Score Summary (Country Dimension):")
    print("=" * 70)
    print(f"\nMetric Comparison:")
    print(f"  Traditional GRI:     {gri:.4f} ({gri/max_gri_mean*100:.1f}% of max)")
    print(f"  Diversity Score:     {diversity:.4f} ({diversity/max_div_mean*100:.1f}% of max)")
    print(f"  SRI:                 {sri:.4f}")
    print(f"  VWRS (basic):        {vwrs_basic:.4f}")
    if variance_data:
        print(f"  VWRS (full):         {vwrs_full:.4f}")
    print(f"\nMaximum Possible (Country):")
    print(f"  Max GRI:             {max_gri_mean:.4f} ± {max_gri_std:.4f}")
    print(f"  Max Diversity:       {max_div_mean:.4f} ± {max_div_std:.4f}")
    
    # Summary insights
    # Multi-dimensional scorecard
    print("\n" + "=" * 70)
    print("Multi-Dimensional GRI Scorecard:")
    print("=" * 70)
    print("\nCalculating GRI across all standard dimensions...")
    
    multi_dim_results = calculate_multi_dimension_gri(survey_df, base_path)
    
    # Calculate max possible for key dimensions
    print("\nEstimating maximum possible GRI for each dimension...")
    max_scores = {}
    for dim in ['Country × Gender × Age', 'Country × Religion', 'Country × Environment', 'Country']:
        if dim == 'Country':
            max_scores[dim] = max_gri_mean  # We already calculated this
        else:
            # Quick estimate - in practice these are slightly lower than Country-only
            max_scores[dim] = 0.98
    
    print(f"\n{'Dimension':<25} {'GRI':>8} {'Diversity':>10} {'% of Max':>12} {'Status':>15}")
    print("-" * 75)
    
    # Display results for each dimension
    status_symbols = {
        'good': '✓ Good',
        'fair': '~ Fair', 
        'poor': '✗ Poor'
    }
    
    for dim in ['Country × Gender × Age', 'Country × Religion', 'Country × Environment', 'Country']:
        if dim in multi_dim_results:
            result = multi_dim_results[dim]
            if result['gri'] is not None:
                max_gri = max_scores.get(dim, 0.98)
                pct_max = result['gri'] / max_gri * 100
                
                # Determine status
                if pct_max >= 50:
                    status = status_symbols['good']
                elif pct_max >= 40:
                    status = status_symbols['fair']
                else:
                    status = status_symbols['poor']
                
                div_str = f"{result['diversity']:.4f}" if result['diversity'] else "N/A"
                print(f"{dim:<25} {result['gri']:>8.4f} {div_str:>10} {pct_max:>11.1f}% {status:>15}")
            else:
                print(f"{dim:<25} {'Error':>8} {'Error':>10} {'N/A':>12} {'Error':>15}")
                if 'error' in result:
                    print(f"  → {result['error']}")
    
    # Overall average
    print("-" * 75)
    if 'Overall (Average)' in multi_dim_results:
        avg_result = multi_dim_results['Overall (Average)']
        avg_pct = avg_result['gri'] / 0.985 * 100  # Rough average of max scores
        if avg_pct >= 50:
            avg_status = status_symbols['good']
        elif avg_pct >= 40:
            avg_status = status_symbols['fair']
        else:
            avg_status = status_symbols['poor']
        print(f"{'Overall (Average)':<25} {avg_result['gri']:>8.4f} {'N/A':>10} {avg_pct:>11.1f}% {avg_status:>15}")
    
    print("\n" + "-" * 75)
    print("Notes:")
    print("- Country×Gender×Age: Most granular demographic breakdown (highest difficulty)")
    print("- Country×Religion: Religious diversity within countries") 
    print("- Country×Environment: Urban/rural representation within countries")
    print("- Country: Basic geographic representation")
    print("- Overall: Simple average of all dimension scores")
    
    print("\n" + "=" * 70)
    print("Key Insights:")
    print("=" * 70)
    
    print(f"\n1. Traditional GRI ({gri:.4f}) measures proportional country representation")
    print("   - Penalizes all deviations from population proportions equally")
    print(f"   - Achieves {gri/max_gri_mean*100:.1f}% of the maximum possible for this sample size")
    print("   - Best when you need exact demographic matching")
    print("   - Note: This is ONLY the country dimension (full GRI includes age×gender, etc.)")
    
    print(f"\n2. Diversity Score ({diversity:.4f}) measures country coverage")
    print(f"   - {diversity*100:.1f}% of relevant countries are represented") 
    print(f"   - Achieves {diversity/max_div_mean*100:.1f}% of maximum possible coverage")
    print(f"   - Relevant = countries with population > {threshold:.5f}")
    
    print(f"\n3. SRI ({sri:.4f}) measures strategic representation") 
    print("   - Targets sqrt(population) allocation")
    print("   - Balances between equal and proportional representation")
    print("   - Small countries get boosted (see table above)")
    print("   - Best for minimizing total survey uncertainty")
    
    print(f"\n4. VWRS ({vwrs_basic:.4f}) measures reliable representation")
    print("   - Weights by statistical reliability")
    print("   - Small/unreliable samples contribute less to score")
    print("   - Closer to 1.0 suggests good coverage of statistically meaningful groups")
    print("   - Perfect VWRS=1.0 would mean perfect match weighted by reliability")
    
    if variance_data:
        print(f"\n5. With internal variance, VWRS changes by {vwrs_full - vwrs_basic:+.4f}")
        print("   - Variance measures how much survey responses differ within each country")
        print("   - Countries WITH data: variance measured from actual responses (typically 0.05-0.08)")
        print("   - Countries WITHOUT data: assigned conservative default variance of 0.25")
        print("   - Lower variance = more agreement within country = higher weight in VWRS")
    
    print(f"\n6. Maximum Possible Scores ({max_gri_mean:.4f} GRI, {max_div_mean:.4f} Diversity)")
    print("   - Even with optimal allocation, perfect scores are impossible with finite samples")
    print(f"   - Current survey achieves {gri/max_gri_mean*100:.1f}% of max GRI, {diversity/max_div_mean*100:.1f}% of max diversity")
    print("   - These maxima are for country dimension only")


if __name__ == "__main__":
    main()