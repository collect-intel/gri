#!/usr/bin/env python3
"""
Maximum Possible GRI and Diversity Score Calculator

This script calculates the theoretical maximum GRI and Diversity scores achievable
for a given sample size using semi-stochastic sampling methodology.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Tuple, Dict
import argparse

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.utils import load_data


def generate_optimal_sample(true_proportions: np.ndarray, N: int, random_seed: int = None) -> np.ndarray:
    """
    Generate an optimal sample allocation using semi-stochastic sampling.
    
    Args:
        true_proportions: 1D array of population proportions (must sum to 1.0)
        N: Total sample size
        random_seed: Random seed for reproducibility
        
    Returns:
        1D array of sample counts for each stratum
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Initialize sample counts
    sample_counts = np.zeros(len(true_proportions), dtype=int)
    
    # Calculate ideal sample for each stratum
    ideal_samples = true_proportions * N
    
    # Apply semi-stochastic sampling logic
    for i, (q_i, ideal) in enumerate(zip(true_proportions, ideal_samples)):
        if round(ideal) > 0:
            # Deterministic allocation for larger strata
            sample_counts[i] = round(ideal)
        else:
            # Probabilistic allocation for smaller strata
            if np.random.random() < ideal:
                sample_counts[i] = 1
            else:
                sample_counts[i] = 0
    
    # Adjust to ensure total sample size is exactly N
    current_total = sample_counts.sum()
    difference = N - current_total
    
    if difference != 0:
        # Find strata that can be adjusted (have sample_counts > 0 or could receive samples)
        adjustable_strata = np.where(sample_counts > 0)[0] if difference < 0 else np.arange(len(sample_counts))
        
        # Randomly adjust samples to match target N
        for _ in range(abs(difference)):
            if len(adjustable_strata) == 0:
                break
            
            idx = np.random.choice(adjustable_strata)
            
            if difference > 0:
                sample_counts[idx] += 1
            else:
                if sample_counts[idx] > 0:
                    sample_counts[idx] -= 1
                    if sample_counts[idx] == 0:
                        # Remove from adjustable if it goes to zero
                        adjustable_strata = adjustable_strata[adjustable_strata != idx]
    
    return sample_counts


def calculate_max_gri(true_proportions: np.ndarray, sample_counts: np.ndarray, N: int) -> float:
    """
    Calculate GRI score from optimal sample allocation.
    
    Args:
        true_proportions: Population proportions
        sample_counts: Sample counts for each stratum
        N: Total sample size
        
    Returns:
        GRI score (1 - Total Variation Distance)
    """
    # Convert sample counts to proportions
    sample_proportions = sample_counts / N
    
    # Calculate Total Variation Distance
    tvd = 0.5 * np.sum(np.abs(sample_proportions - true_proportions))
    
    # GRI = 1 - TVD
    gri = 1 - tvd
    
    return gri


def calculate_max_diversity_score(true_proportions: np.ndarray, sample_counts: np.ndarray, 
                                 threshold: float = None, N: int = None) -> float:
    """
    Calculate Diversity Score from optimal sample allocation.
    
    Args:
        true_proportions: Population proportions
        sample_counts: Sample counts for each stratum
        threshold: Relevance threshold (default: 1/(2*N))
        N: Total sample size (required if threshold is None)
        
    Returns:
        Diversity Score (coverage rate of relevant strata)
    """
    if threshold is None:
        if N is None:
            raise ValueError("Must provide either threshold or N")
        threshold = 1.0 / (2 * N)
    
    # Count relevant strata (above threshold)
    relevant_strata = np.sum(true_proportions > threshold)
    
    # Count represented strata (have samples AND are relevant)
    represented_strata = np.sum((sample_counts > 0) & (true_proportions > threshold))
    
    # Diversity score
    diversity_score = represented_strata / relevant_strata if relevant_strata > 0 else 0.0
    
    return diversity_score


def monte_carlo_max_scores(benchmark_df: pd.DataFrame, N: int, strata_cols: list,
                          n_simulations: int = 1000, random_seed: int = 42) -> Dict:
    """
    Calculate expected maximum GRI and Diversity scores using Monte Carlo simulation.
    
    Args:
        benchmark_df: Benchmark data with population proportions
        N: Sample size to simulate
        strata_cols: Columns defining the strata
        n_simulations: Number of Monte Carlo simulations
        random_seed: Base random seed
        
    Returns:
        Dictionary with simulation results
    """
    # Extract population proportions
    true_proportions = benchmark_df['population_proportion'].values
    
    # Verify proportions sum to 1
    total_prop = true_proportions.sum()
    if abs(total_prop - 1.0) > 1e-6:
        print(f"Warning: Population proportions sum to {total_prop:.6f}, not 1.0")
        true_proportions = true_proportions / total_prop  # Normalize
    
    # Dynamic threshold
    threshold = 1.0 / (2 * N)
    
    # Run simulations
    gri_scores = []
    diversity_scores = []
    
    print(f"Running {n_simulations} Monte Carlo simulations...")
    
    for i in range(n_simulations):
        # Use different seed for each simulation
        sim_seed = random_seed + i if random_seed is not None else None
        
        # Generate optimal sample
        sample_counts = generate_optimal_sample(true_proportions, N, sim_seed)
        
        # Calculate scores
        gri = calculate_max_gri(true_proportions, sample_counts, N)
        diversity = calculate_max_diversity_score(true_proportions, sample_counts, threshold, N)
        
        gri_scores.append(gri)
        diversity_scores.append(diversity)
        
        if (i + 1) % 100 == 0:
            print(f"  Completed {i + 1}/{n_simulations} simulations")
    
    # Calculate statistics
    gri_scores = np.array(gri_scores)
    diversity_scores = np.array(diversity_scores)
    
    results = {
        'sample_size': int(N),
        'threshold': float(threshold),
        'n_simulations': int(n_simulations),
        'total_strata': int(len(true_proportions)),
        'relevant_strata': int(np.sum(true_proportions > threshold)),
        'max_gri': {
            'mean': float(np.mean(gri_scores)),
            'std': float(np.std(gri_scores)),
            'min': float(np.min(gri_scores)),
            'max': float(np.max(gri_scores)),
            'median': float(np.median(gri_scores)),
            'q25': float(np.percentile(gri_scores, 25)),
            'q75': float(np.percentile(gri_scores, 75))
        },
        'max_diversity': {
            'mean': float(np.mean(diversity_scores)),
            'std': float(np.std(diversity_scores)),
            'min': float(np.min(diversity_scores)),
            'max': float(np.max(diversity_scores)),
            'median': float(np.median(diversity_scores)),
            'q25': float(np.percentile(diversity_scores, 25)),
            'q75': float(np.percentile(diversity_scores, 75))
        },
        'dimension_info': {
            'strata_columns': strata_cols,
            'sample_size': N,
            'threshold_percentage': threshold * 100
        }
    }
    
    return results


def calculate_all_max_scores(sample_sizes: list, output_dir: str = "analysis_output",
                           n_simulations: int = 1000) -> Dict:
    """
    Calculate maximum scores for all dimensions and sample sizes.
    
    Args:
        sample_sizes: List of sample sizes to test
        output_dir: Output directory for results
        n_simulations: Number of Monte Carlo simulations per calculation
        
    Returns:
        Complete results dictionary
    """
    # Load benchmark data
    benchmark_age_gender = load_data('data/processed/benchmark_country_gender_age.csv')
    benchmark_religion = load_data('data/processed/benchmark_country_religion.csv')
    benchmark_environment = load_data('data/processed/benchmark_country_environment.csv')
    
    # Define dimensions
    dimensions = {
        'Country × Gender × Age': {
            'benchmark': benchmark_age_gender,
            'strata_cols': ['country', 'gender', 'age_group']
        },
        'Country × Religion': {
            'benchmark': benchmark_religion,
            'strata_cols': ['country', 'religion']
        },
        'Country × Environment': {
            'benchmark': benchmark_environment,
            'strata_cols': ['country', 'environment']
        }
    }
    
    results = {}
    
    for dim_name, dim_config in dimensions.items():
        print(f"\n{'='*60}")
        print(f"DIMENSION: {dim_name}")
        print(f"{'='*60}")
        
        results[dim_name] = {}
        
        for N in sample_sizes:
            print(f"\nCalculating max scores for N = {N:,}...")
            
            max_scores = monte_carlo_max_scores(
                dim_config['benchmark'], 
                N, 
                dim_config['strata_cols'],
                n_simulations
            )
            
            results[dim_name][f'N_{N}'] = max_scores
            
            # Print summary
            print(f"  Max GRI: {max_scores['max_gri']['mean']:.4f} ± {max_scores['max_gri']['std']:.4f}")
            print(f"  Max Diversity: {max_scores['max_diversity']['mean']:.4f} ± {max_scores['max_diversity']['std']:.4f}")
            print(f"  Relevant strata: {max_scores['relevant_strata']:,} / {max_scores['total_strata']:,}")
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save complete results as JSON
    import json
    results_file = output_path / "max_possible_scores.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create summary CSV
    summary_data = []
    for dim_name, dim_results in results.items():
        for size_key, size_results in dim_results.items():
            N = size_results['sample_size']
            summary_data.append({
                'dimension': dim_name,
                'sample_size': N,
                'max_gri_mean': size_results['max_gri']['mean'],
                'max_gri_std': size_results['max_gri']['std'],
                'max_diversity_mean': size_results['max_diversity']['mean'],
                'max_diversity_std': size_results['max_diversity']['std'],
                'total_strata': size_results['total_strata'],
                'relevant_strata': size_results['relevant_strata'],
                'threshold': size_results['threshold']
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = output_path / "max_possible_scores_summary.csv"
    summary_df.to_csv(summary_file, index=False)
    
    # Create detailed report
    report_file = output_path / "max_possible_scores_report.txt"
    with open(report_file, 'w') as f:
        f.write("MAXIMUM POSSIBLE GRI AND DIVERSITY SCORES ANALYSIS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Analysis completed with {n_simulations:,} Monte Carlo simulations per calculation\n")
        f.write("Methodology: Semi-stochastic sampling with hybrid deterministic/probabilistic allocation\n\n")
        
        for dim_name, dim_results in results.items():
            f.write(f"{dim_name}:\n")
            f.write("-" * len(dim_name) + "\n")
            
            for size_key, size_results in dim_results.items():
                N = size_results['sample_size']
                threshold_pct = size_results['threshold'] * 100
                
                f.write(f"\\nSample Size: {N:,}\n")
                f.write(f"Dynamic Threshold: {threshold_pct:.4f}% population\n")
                f.write(f"Total Strata: {size_results['total_strata']:,}\n")
                f.write(f"Relevant Strata: {size_results['relevant_strata']:,}\n")
                
                gri = size_results['max_gri']
                div = size_results['max_diversity']
                
                f.write(f"\\nMaximum GRI Score:\n")
                f.write(f"  Mean: {gri['mean']:.6f} ± {gri['std']:.6f}\n")
                f.write(f"  Range: [{gri['min']:.6f}, {gri['max']:.6f}]\n")
                f.write(f"  Median: {gri['median']:.6f}\n")
                
                f.write(f"\\nMaximum Diversity Score:\n")
                f.write(f"  Mean: {div['mean']:.6f} ± {div['std']:.6f}\n")
                f.write(f"  Range: [{div['min']:.6f}, {div['max']:.6f}]\n")
                f.write(f"  Median: {div['median']:.6f}\n")
                
            f.write("\\n" + "="*40 + "\\n")
    
    print(f"\\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved:")
    print(f"  - {results_file}")
    print(f"  - {summary_file}")
    print(f"  - {report_file}")
    
    return results


def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(description='Calculate maximum possible GRI and Diversity scores')
    parser.add_argument('--sample-sizes', nargs='+', type=int, 
                       default=[100, 250, 500, 1000, 2000], 
                       help='Sample sizes to analyze')
    parser.add_argument('--simulations', type=int, default=1000,
                       help='Number of Monte Carlo simulations')
    parser.add_argument('--output-dir', default='analysis_output',
                       help='Output directory')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print("Maximum Possible GRI and Diversity Scores Calculator")
    print("=" * 60)
    print(f"Sample sizes: {args.sample_sizes}")
    print(f"Simulations per calculation: {args.simulations:,}")
    print(f"Output directory: {args.output_dir}")
    print(f"Random seed: {args.seed}")
    
    # Set global random seed
    np.random.seed(args.seed)
    
    results = calculate_all_max_scores(
        sample_sizes=args.sample_sizes,
        output_dir=args.output_dir,
        n_simulations=args.simulations
    )
    
    # Print quick summary
    print(f"\\nQUICK SUMMARY:")
    print(f"Sample sizes analyzed: {len(args.sample_sizes)}")
    print(f"Dimensions analyzed: {len(results)}")
    print(f"Total calculations: {len(args.sample_sizes) * len(results)}")


if __name__ == "__main__":
    main()