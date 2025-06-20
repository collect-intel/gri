#!/usr/bin/env python3
"""
Calculate optimal sample allocation using variance data from GD surveys.

This script uses the variance analysis from analyze_demographic_variance.py
to determine optimal sample sizes for each demographic stratum.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Tuple
import sys
sys.path.append(str(Path(__file__).parent.parent))

from gri.variance_weighted import optimal_allocation, calculate_vwrs


def load_variance_data(variance_file: Path) -> Dict[str, Dict[str, float]]:
    """Load variance lookup table from JSON file."""
    with open(variance_file, 'r') as f:
        return json.load(f)


def load_population_proportions(
    benchmark_path: Path,
    dimension: str
) -> Dict[str, float]:
    """
    Load population proportions for a specific dimension.
    
    This is a simplified example - in practice, you'd calculate these
    from the actual benchmark data files.
    """
    # Example proportions for demonstration
    example_proportions = {
        'Country': {
            'China': 0.180, 'India': 0.175, 'United States of America': 0.042,
            'Indonesia': 0.035, 'Pakistan': 0.028, 'Brazil': 0.027,
            'Nigeria': 0.026, 'Bangladesh': 0.021, 'Russian Federation': 0.018,
            'Mexico': 0.016, 'Japan': 0.016, 'Ethiopia': 0.015,
            'Philippines': 0.014, 'Egypt': 0.013, 'Viet Nam': 0.012,
            'Other': 0.362  # Aggregate smaller countries
        },
        'Gender': {
            'Male': 0.505,
            'Female': 0.495
        },
        'Age Group': {
            '18-25': 0.18,
            '26-35': 0.22,
            '36-45': 0.20,
            '46-55': 0.17,
            '56-65': 0.13,
            '65+': 0.10
        },
        'Religion': {
            'Christianity': 0.31,
            'Islam': 0.24,
            'Hinduism': 0.15,
            'Buddhism': 0.07,
            'I do not identify with any religious group or faith': 0.16,
            'Other religious group': 0.06,
            'Judaism': 0.002
        },
        'Environment': {
            'Urban': 0.56,
            'Rural': 0.44
        }
    }
    
    # For composite dimensions, we'd need to calculate joint distributions
    # This is simplified for demonstration
    return example_proportions.get(dimension.split(' × ')[0], {})


def compare_allocation_strategies(
    population_props: Dict[str, float],
    variances: Dict[str, float],
    total_n: int
) -> pd.DataFrame:
    """Compare proportional vs optimal allocation strategies."""
    
    # Proportional allocation
    proportional = {k: int(total_n * v) for k, v in population_props.items()}
    
    # Optimal allocation using variance data
    optimal = optimal_allocation(population_props, total_n, variances)
    
    # Create comparison DataFrame
    comparison_data = []
    for stratum in population_props:
        prop_n = proportional.get(stratum, 0)
        opt_n = optimal.get(stratum, 0)
        variance = variances.get(stratum, 0.25)
        
        comparison_data.append({
            'stratum': stratum,
            'population_pct': population_props[stratum] * 100,
            'variance': variance,
            'proportional_n': prop_n,
            'optimal_n': opt_n,
            'difference': opt_n - prop_n,
            'pct_change': ((opt_n - prop_n) / prop_n * 100) if prop_n > 0 else 0
        })
    
    df = pd.DataFrame(comparison_data)
    df = df.sort_values('population_pct', ascending=False)
    return df


def calculate_efficiency_gain(
    population_props: Dict[str, float],
    variances: Dict[str, float],
    proportional_n: Dict[str, int],
    optimal_n: Dict[str, int]
) -> float:
    """
    Calculate the efficiency gain from optimal allocation.
    
    Efficiency measured as reduction in overall sampling variance.
    """
    def total_variance(allocations):
        total_var = 0
        for stratum, pop_prop in population_props.items():
            n = allocations.get(stratum, 0)
            var = variances.get(stratum, 0.25)
            if n > 0:
                # Variance of mean estimator
                total_var += (pop_prop ** 2) * var / n
        return total_var
    
    var_proportional = total_variance(proportional_n)
    var_optimal = total_variance(optimal_n)
    
    efficiency_gain = (var_proportional - var_optimal) / var_proportional
    return efficiency_gain


def main():
    """Main analysis function."""
    base_path = Path(__file__).parent.parent
    variance_path = base_path / 'analysis_output' / 'demographic_variance'
    output_path = base_path / 'analysis_output' / 'optimal_allocation'
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Sample sizes to test
    sample_sizes = [1000, 2500, 5000, 10000]
    
    # Analyze each GD survey
    for gd_num in [1, 2, 3]:
        variance_file = variance_path / f'GD{gd_num}_variance_lookup.json'
        
        if not variance_file.exists():
            print(f"Variance data not found for GD{gd_num}, skipping...")
            continue
            
        print(f"\nAnalyzing optimal allocation for GD{gd_num}...")
        variance_data = load_variance_data(variance_file)
        
        # Analyze key dimensions
        for dimension in ['Country', 'Gender', 'Age Group', 'Religion', 'Environment']:
            print(f"\n  Dimension: {dimension}")
            
            # Get variances for this dimension
            if dimension not in variance_data:
                print(f"    No variance data for {dimension}")
                continue
                
            stratum_variances = variance_data[dimension]
            
            # Get population proportions (simplified for demo)
            pop_props = load_population_proportions(base_path / 'data' / 'raw' / 'benchmark_data', dimension)
            
            if not pop_props:
                continue
            
            # Compare allocations for different sample sizes
            for n in sample_sizes:
                print(f"\n    Sample size N = {n:,}")
                
                comparison = compare_allocation_strategies(pop_props, stratum_variances, n)
                
                # Save detailed comparison
                comparison.to_csv(
                    output_path / f'GD{gd_num}_{dimension.replace(" ", "_")}_n{n}_comparison.csv',
                    index=False
                )
                
                # Calculate efficiency gain
                prop_dict = dict(zip(comparison['stratum'], comparison['proportional_n']))
                opt_dict = dict(zip(comparison['stratum'], comparison['optimal_n']))
                
                efficiency = calculate_efficiency_gain(pop_props, stratum_variances, prop_dict, opt_dict)
                
                print(f"      Efficiency gain: {efficiency:.1%}")
                print(f"      Largest increases: ")
                top_increases = comparison.nlargest(3, 'pct_change')[['stratum', 'pct_change']]
                for _, row in top_increases.iterrows():
                    print(f"        {row['stratum']}: +{row['pct_change']:.1f}%")
                
                print(f"      Largest decreases: ")
                top_decreases = comparison.nsmallest(3, 'pct_change')[['stratum', 'pct_change']]
                for _, row in top_decreases.iterrows():
                    print(f"        {row['stratum']}: {row['pct_change']:.1f}%")
    
    print("\n\nCreating summary visualization data...")
    
    # Create a summary showing how consensus affects allocation
    summary_data = []
    
    for gd_num in [1, 2, 3]:
        variance_file = variance_path / f'GD{gd_num}_variance_lookup.json'
        if not variance_file.exists():
            continue
            
        variance_data = load_variance_data(variance_file)
        
        for dimension, variances in variance_data.items():
            if not variances:
                continue
                
            # Group by consensus level
            for stratum, var in variances.items():
                consensus = 1 - var  # Convert variance to consensus
                summary_data.append({
                    'survey': f'GD{gd_num}',
                    'dimension': dimension,
                    'stratum': stratum,
                    'variance': var,
                    'consensus_score': consensus,
                    'consensus_category': (
                        'High' if consensus > 0.8 else
                        'Medium' if consensus > 0.6 else
                        'Low'
                    )
                })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_path / 'consensus_allocation_summary.csv', index=False)
    
    # Print key insights
    print("\n\nKey Insights:")
    print("=" * 60)
    
    if not summary_df.empty:
        print("\nConsensus Categories:")
        consensus_stats = summary_df.groupby('consensus_category')['variance'].agg(['count', 'mean'])
        print(consensus_stats)
        
        print("\nRecommendations:")
        print("- High consensus groups (>0.8): Can use smaller samples")
        print("- Medium consensus groups (0.6-0.8): Use proportional allocation")
        print("- Low consensus groups (<0.6): Oversample for better estimates")
        
        print("\nDimensions with highest variance (need oversampling):")
        high_var = summary_df.nlargest(10, 'variance')[['dimension', 'stratum', 'variance']]
        print(high_var.to_string(index=False))


if __name__ == "__main__":
    main()