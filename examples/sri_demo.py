#!/usr/bin/env python3
"""
Demonstration of Strategic Representativeness Index (SRI).

Shows how SRI's square-root allocation balances between proportional
and equal representation to minimize total survey uncertainty.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from gri.calculator import calculate_gri
from gri.strategic_index import calculate_sri_from_dataframes, compare_allocation_methods


def create_example_scenario():
    """Create an example with very different population sizes."""
    
    # Population data - mix of large and small countries
    population_data = [
        {'country': 'China', 'population_proportion': 0.40},      # 40% - very large
        {'country': 'USA', 'population_proportion': 0.20},        # 20% - large
        {'country': 'Germany', 'population_proportion': 0.10},    # 10% - medium
        {'country': 'Kenya', 'population_proportion': 0.05},      # 5% - small
        {'country': 'Denmark', 'population_proportion': 0.01},    # 1% - very small
        {'country': 'Luxembourg', 'population_proportion': 0.001}, # 0.1% - tiny
        {'country': 'Others', 'population_proportion': 0.239}     # Rest
    ]
    
    benchmark_df = pd.DataFrame(population_data)
    
    # Three different sample scenarios
    scenarios = {
        'Proportional': {
            'China': 400, 'USA': 200, 'Germany': 100, 'Kenya': 50,
            'Denmark': 10, 'Luxembourg': 1, 'Others': 239
        },
        'Strategic': {
            'China': 290, 'USA': 190, 'Germany': 140, 'Kenya': 100,
            'Denmark': 45, 'Luxembourg': 15, 'Others': 220
        },
        'Equal': {
            'China': 143, 'USA': 143, 'Germany': 143, 'Kenya': 143,
            'Denmark': 143, 'Luxembourg': 142, 'Others': 143
        }
    }
    
    return benchmark_df, scenarios


def main():
    """Demonstrate SRI calculation and strategic allocation benefits."""
    
    print("Strategic Representativeness Index (SRI) Demonstration")
    print("=" * 60)
    
    # Create example
    benchmark_df, scenarios = create_example_scenario()
    
    # Show allocation comparison
    print("\nComparing Allocation Strategies (n=1000):")
    print("-" * 60)
    
    # Extract population proportions
    pop_props = dict(zip(benchmark_df['country'], benchmark_df['population_proportion']))
    comparison = compare_allocation_methods(pop_props, 1000)
    
    print(comparison[['stratum', 'population_pct', 'proportional_n', 'strategic_n', 'strategic_boost']].to_string(index=False))
    
    # Calculate scores for each scenario
    print("\n" + "=" * 60)
    print("Scoring Different Sample Distributions:")
    print("=" * 60)
    
    results = []
    
    for scenario_name, sample_counts in scenarios.items():
        # Create survey data
        survey_data = []
        for country, count in sample_counts.items():
            for _ in range(count):
                survey_data.append({'country': country})
        
        survey_df = pd.DataFrame(survey_data)
        
        # Calculate scores
        gri = calculate_gri(survey_df, benchmark_df, ['country'])
        sri, _ = calculate_sri_from_dataframes(survey_df, benchmark_df, ['country'])
        
        results.append({
            'Scenario': scenario_name,
            'GRI': gri,
            'SRI': sri,
            'Total n': len(survey_df)
        })
        
        print(f"\n{scenario_name} Sample:")
        print(f"  GRI: {gri:.4f}")
        print(f"  SRI: {sri:.4f}")
    
    # Show results comparison
    results_df = pd.DataFrame(results)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(results_df.to_string(index=False))
    
    print("\nKey Insights:")
    print("-" * 60)
    print("1. Proportional sampling maximizes GRI but may give poor SRI")
    print("   - Perfect for demographic representation")
    print("   - But tiny countries have huge uncertainty")
    
    print("\n2. Strategic sampling maximizes SRI")
    print("   - Balances representation with reliability")
    print("   - Small countries get boosted (but not to equality)")
    
    print("\n3. Equal sampling is poor for both metrics")
    print("   - Over-represents small countries")
    print("   - Under-represents large countries")
    
    print("\n4. SRI rewards smart allocation:")
    print("   - Large countries: sqrt(40%) = 63% of proportional")
    print("   - Small countries: sqrt(1%) = 316% of proportional")
    print("   - This minimizes total survey uncertainty")


if __name__ == "__main__":
    main()