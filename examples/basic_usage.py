#!/usr/bin/env python3
"""
Basic GRI Usage Examples

This script demonstrates the fundamental ways to use the GRI module.
"""

import pandas as pd
from pathlib import Path

# Add parent directory to path if running from examples folder
import sys
sys.path.append(str(Path(__file__).parent.parent))

from gri import calculate_gri, load_data, load_benchmark_suite


def example_1_simple_calculation():
    """Example 1: Basic GRI calculation with minimal code."""
    print("=" * 60)
    print("Example 1: Simple GRI Calculation")
    print("=" * 60)
    
    # Load data (you would use your own file paths)
    survey_data = load_data('data/processed/gd3_survey_data_processed.csv')
    benchmark_data = load_data('data/processed/benchmark_country_gender_age.csv')
    
    # Calculate GRI for Country × Gender × Age
    gri_score = calculate_gri(
        survey_data, 
        benchmark_data, 
        ['country', 'gender', 'age_group']
    )
    
    print(f"GRI Score: {gri_score:.4f}")
    print(f"Interpretation: ", end="")
    if gri_score >= 0.9:
        print("Excellent representation")
    elif gri_score >= 0.8:
        print("Good representation")
    elif gri_score >= 0.7:
        print("Fair representation")
    else:
        print("Poor representation")
    print()


def example_2_multiple_dimensions():
    """Example 2: Calculate GRI for multiple dimensions."""
    print("=" * 60)
    print("Example 2: Multiple Dimension Calculation")
    print("=" * 60)
    
    # Load survey data once
    survey = load_data('data/processed/gd3_survey_data_processed.csv')
    
    # Load all benchmarks
    benchmarks = load_benchmark_suite()
    
    # Define dimensions to analyze
    dimensions_to_check = [
        ('Country', ['country']),
        ('Gender', ['gender']),
        ('Age Group', ['age_group']),
        ('Country × Gender', ['country', 'gender']),
        ('Country × Gender × Age', ['country', 'gender', 'age_group'])
    ]
    
    results = []
    for dim_name, dim_cols in dimensions_to_check:
        # Get appropriate benchmark
        if dim_name in benchmarks:
            benchmark = benchmarks[dim_name]
        else:
            # For combinations not pre-computed, use the most detailed
            benchmark = benchmarks['Country × Gender × Age']
        
        score = calculate_gri(survey, benchmark, dim_cols)
        results.append({
            'Dimension': dim_name,
            'GRI Score': score,
            'Columns': ', '.join(dim_cols)
        })
        print(f"{dim_name}: {score:.4f}")
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(results)
    print("\nSummary DataFrame:")
    print(summary_df)
    print()


def example_3_with_diversity_score():
    """Example 3: Calculate both GRI and Diversity scores."""
    print("=" * 60)
    print("Example 3: GRI and Diversity Scores")
    print("=" * 60)
    
    from gri import calculate_diversity_score
    
    # Load data
    survey = load_data('data/processed/gd3_survey_data_processed.csv')
    benchmark = load_data('data/processed/benchmark_country_gender_age.csv')
    dimension_cols = ['country', 'gender', 'age_group']
    
    # Calculate both scores
    gri_score = calculate_gri(survey, benchmark, dimension_cols)
    diversity_score = calculate_diversity_score(survey, benchmark, dimension_cols)
    
    print(f"GRI Score: {gri_score:.4f}")
    print(f"Diversity Score: {diversity_score:.4f}")
    print()
    print("Interpretation:")
    print(f"- GRI measures how well proportions match the benchmark")
    print(f"- Diversity measures coverage of demographic categories")
    print(f"- Both scores range from 0 (worst) to 1 (best)")
    print()


def example_4_data_validation():
    """Example 4: Validate survey data before analysis."""
    print("=" * 60)
    print("Example 4: Data Validation")
    print("=" * 60)
    
    from gri import validate_survey_data, check_category_alignment
    
    # Load data
    survey = load_data('data/processed/gd3_survey_data_processed.csv')
    benchmark = load_data('data/processed/benchmark_country_gender_age.csv')
    
    # Validate survey data structure
    is_valid, issues = validate_survey_data(survey)
    print(f"Survey data valid: {is_valid}")
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    # Check category alignment
    alignment = check_category_alignment(
        survey, 
        benchmark, 
        ['country', 'gender', 'age_group']
    )
    
    print("\nCategory Alignment:")
    for col, stats in alignment.items():
        coverage = stats['coverage'] * 100
        print(f"  {col}: {coverage:.1f}% matched ({stats['matched']}/{stats['total_survey']} categories)")
        if stats['unmatched']:
            print(f"    Unmatched: {list(stats['unmatched'])[:5]}...")
    print()


if __name__ == "__main__":
    # Run all examples
    try:
        example_1_simple_calculation()
    except Exception as e:
        print(f"Example 1 failed: {e}\n")
    
    try:
        example_2_multiple_dimensions()
    except Exception as e:
        print(f"Example 2 failed: {e}\n")
    
    try:
        example_3_with_diversity_score()
    except Exception as e:
        print(f"Example 3 failed: {e}\n")
    
    try:
        example_4_data_validation()
    except Exception as e:
        print(f"Example 4 failed: {e}\n")
    
    print("Note: Some examples may fail if data files are not in expected locations.")
    print("Adjust file paths as needed for your setup.")