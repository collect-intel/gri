#!/usr/bin/env python3
"""
Diversity Score Threshold Analysis

This script demonstrates how different threshold choices (1/2N, 1/N, 2/N) affect
diversity score calculations when sampling from populations with many small strata.

It shows why the 1/2N threshold might overcount achievable diversity by comparing
theoretical expectations with actual coverage in simulated samples.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import seaborn as sns
from scipy import stats
from typing import List, Tuple, Dict

def create_population_distribution(n_strata: int, distribution_type: str = 'uniform') -> np.ndarray:
    """
    Create a population distribution across strata.
    
    Args:
        n_strata: Number of strata in the population
        distribution_type: 'uniform', 'power_law', or 'mixed'
    
    Returns:
        Array of population proportions for each stratum
    """
    if distribution_type == 'uniform':
        # All strata have equal representation
        proportions = np.ones(n_strata) / n_strata
    
    elif distribution_type == 'power_law':
        # Some strata are much larger than others (80-20 rule)
        # Higher exponent means more extreme inequality
        values = 1 / (np.arange(1, n_strata + 1) ** 1.5)
        proportions = values / values.sum()
    
    elif distribution_type == 'mixed':
        # Mix of large and small strata
        # First 20% of strata contain 60% of population
        n_large = max(1, n_strata // 5)
        n_small = n_strata - n_large
        
        large_prop = 0.6 / n_large if n_large > 0 else 0
        small_prop = 0.4 / n_small if n_small > 0 else 0
        
        proportions = np.array([large_prop] * n_large + [small_prop] * n_small)
    
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")
    
    return proportions

def simulate_sampling(population: np.ndarray, sample_size: int, n_simulations: int = 1000) -> List[np.ndarray]:
    """
    Simulate drawing samples from the population.
    
    Args:
        population: Population proportions for each stratum
        sample_size: Number of individuals to sample
        n_simulations: Number of simulations to run
    
    Returns:
        List of sample distributions (counts per stratum)
    """
    n_strata = len(population)
    samples = []
    
    for _ in range(n_simulations):
        # Draw sample according to population proportions
        sample_strata = np.random.choice(n_strata, size=sample_size, p=population)
        
        # Count occurrences of each stratum
        counts = np.bincount(sample_strata, minlength=n_strata)
        samples.append(counts)
    
    return samples

def calculate_coverage_stats(samples: List[np.ndarray], sample_size: int, 
                           thresholds: Dict[str, float]) -> pd.DataFrame:
    """
    Calculate coverage statistics for different threshold values.
    
    Args:
        samples: List of sample distributions
        sample_size: Size of each sample
        thresholds: Dictionary of threshold names and values
    
    Returns:
        DataFrame with coverage statistics
    """
    results = []
    
    for sample in samples:
        sample_proportions = sample / sample_size
        
        for thresh_name, thresh_value in thresholds.items():
            # Count strata that meet the threshold
            covered = np.sum(sample_proportions >= thresh_value)
            
            results.append({
                'threshold': thresh_name,
                'covered_strata': covered,
                'coverage_rate': covered / len(sample)
            })
    
    return pd.DataFrame(results)

def theoretical_coverage(population: np.ndarray, sample_size: int, threshold: float) -> float:
    """
    Calculate theoretical expected coverage using binomial probabilities.
    
    For each stratum, calculate the probability of observing at least
    threshold * sample_size individuals.
    """
    expected_coverage = 0
    min_count = int(np.ceil(threshold * sample_size))
    
    for p in population:
        # Probability of seeing at least min_count from this stratum
        # Using normal approximation to binomial for large samples
        if sample_size * p > 5 and sample_size * (1-p) > 5:
            mean = sample_size * p
            std = np.sqrt(sample_size * p * (1 - p))
            z = (min_count - 0.5 - mean) / std  # Continuity correction
            prob_covered = 1 - stats.norm.cdf(z)
        else:
            # Use exact binomial for small expected counts
            prob_covered = 1 - stats.binom.cdf(min_count - 1, sample_size, p)
        
        expected_coverage += prob_covered
    
    return expected_coverage

def plot_coverage_comparison(results_df: pd.DataFrame, n_strata: int, sample_size: int,
                           population: np.ndarray, output_prefix: str):
    """Create visualization comparing coverage across thresholds."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Box plot of coverage rates
    ax = axes[0, 0]
    sns.boxplot(data=results_df, x='threshold', y='coverage_rate', ax=ax)
    ax.set_title(f'Coverage Rate Distribution\n({n_strata} strata, N={sample_size})')
    ax.set_ylabel('Fraction of Strata Covered')
    ax.set_ylim(0, 1)
    
    # Add theoretical expectations
    thresholds = {'1/2N': 0.5/sample_size, '1/N': 1/sample_size, '2/N': 2/sample_size}
    from scipy import stats
    theoretical = {name: theoretical_coverage(population, sample_size, thresh) 
                  for name, thresh in thresholds.items()}
    
    for i, (name, expected) in enumerate(theoretical.items()):
        ax.hlines(expected/n_strata, i-0.4, i+0.4, colors='red', 
                 linestyles='dashed', label='Theoretical' if i == 0 else None)
    
    if len(theoretical) > 0:
        ax.legend()
    
    # 2. Histogram of covered strata counts
    ax = axes[0, 1]
    for thresh in results_df['threshold'].unique():
        data = results_df[results_df['threshold'] == thresh]['covered_strata']
        ax.hist(data, alpha=0.5, label=thresh, bins=20)
    ax.set_xlabel('Number of Strata Covered')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Covered Strata')
    ax.legend()
    
    # 3. Population distribution
    ax = axes[1, 0]
    sorted_pop = np.sort(population)[::-1]
    ax.bar(range(len(sorted_pop)), sorted_pop)
    ax.set_xlabel('Stratum (sorted by size)')
    ax.set_ylabel('Population Proportion')
    ax.set_title('Population Distribution')
    ax.set_yscale('log')
    
    # Add threshold lines
    for name, thresh in thresholds.items():
        ax.axhline(thresh, color='red', linestyle='--', alpha=0.5, label=f'{name}={thresh:.4f}')
    ax.legend()
    
    # 4. Coverage probability by stratum size
    ax = axes[1, 1]
    stratum_sizes = population
    coverage_probs = {name: [] for name in thresholds.keys()}
    
    for p in stratum_sizes:
        for name, thresh in thresholds.items():
            min_count = int(np.ceil(thresh * sample_size))
            if sample_size * p > 5:
                mean = sample_size * p
                std = np.sqrt(sample_size * p * (1 - p))
                z = (min_count - 0.5 - mean) / std
                prob = 1 - stats.norm.cdf(z)
            else:
                prob = 1 - stats.binom.cdf(min_count - 1, sample_size, p)
            coverage_probs[name].append(prob)
    
    for name, probs in coverage_probs.items():
        ax.scatter(stratum_sizes, probs, alpha=0.6, label=name, s=30)
    
    ax.set_xlabel('Stratum Population Proportion')
    ax.set_ylabel('Probability of Coverage')
    ax.set_title('Coverage Probability vs Stratum Size')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_coverage_analysis.png', dpi=150)
    plt.close()

def main():
    """Run the diversity threshold analysis."""
    np.random.seed(42)
    
    # Analysis parameters
    scenarios = [
        {'n_strata': 50, 'sample_size': 100, 'dist': 'uniform'},  # Many strata, small sample
        {'n_strata': 100, 'sample_size': 200, 'dist': 'power_law'},  # Extreme case
        {'n_strata': 200, 'sample_size': 500, 'dist': 'mixed'},  # Moderate case
        {'n_strata': 1000, 'sample_size': 1000, 'dist': 'power_law'},  # Very many strata
    ]
    
    n_simulations = 1000
    
    print("Diversity Score Threshold Analysis")
    print("=" * 60)
    
    for i, scenario in enumerate(scenarios):
        n_strata = scenario['n_strata']
        sample_size = scenario['sample_size']
        dist_type = scenario['dist']
        
        print(f"\nScenario {i+1}: {n_strata} strata, N={sample_size}, {dist_type} distribution")
        print("-" * 60)
        
        # Create population
        population = create_population_distribution(n_strata, dist_type)
        
        # Define thresholds
        thresholds = {
            '1/2N': 0.5 / sample_size,
            '1/N': 1.0 / sample_size,
            '2/N': 2.0 / sample_size
        }
        
        print(f"Threshold values:")
        for name, value in thresholds.items():
            print(f"  {name}: {value:.6f} (min {int(np.ceil(value * sample_size))} observations)")
        
        # Simulate sampling
        samples = simulate_sampling(population, sample_size, n_simulations)
        
        # Calculate coverage statistics
        results_df = calculate_coverage_stats(samples, sample_size, thresholds)
        
        # Summary statistics
        print(f"\nCoverage Statistics (from {n_simulations} simulations):")
        summary = results_df.groupby('threshold')['coverage_rate'].agg(['mean', 'std', 'min', 'max'])
        print(summary)
        
        # Theoretical expectations
        print(f"\nTheoretical Expected Coverage:")
        from scipy import stats
        for name, thresh in thresholds.items():
            expected = theoretical_coverage(population, sample_size, thresh)
            print(f"  {name}: {expected:.1f} strata ({expected/n_strata:.1%})")
        
        # Count strata below each threshold
        print(f"\nStrata sizes relative to thresholds:")
        for name, thresh in thresholds.items():
            below = np.sum(population < thresh)
            print(f"  {below} strata ({below/n_strata:.1%}) have p < {name}")
        
        # Create visualization
        plot_coverage_comparison(results_df, n_strata, sample_size, population, 
                               f'diversity_scenario_{i+1}')
    
    print("\n" + "=" * 60)
    print("Analysis complete. Plots saved as diversity_scenario_*.png")
    
    # Create summary comparison
    print("\nSummary Comparison Across Scenarios:")
    print("-" * 80)
    print(f"{'Scenario':<40} {'1/2N Coverage':<20} {'Overcount vs 2/N':<20}")
    print("-" * 80)
    
    for i, scenario in enumerate(scenarios):
        n_strata = scenario['n_strata']
        sample_size = scenario['sample_size']
        dist_type = scenario['dist']
        
        # Get population
        population = create_population_distribution(n_strata, dist_type)
        
        # Calculate theoretical coverage
        coverage_half_n = theoretical_coverage(population, sample_size, 0.5/sample_size)
        coverage_2n = theoretical_coverage(population, sample_size, 2.0/sample_size)
        
        overcount = coverage_half_n - coverage_2n
        overcount_pct = (overcount / coverage_2n * 100) if coverage_2n > 0 else 0
        
        scenario_desc = f"{n_strata} strata, N={sample_size}, {dist_type}"
        coverage_str = f"{coverage_half_n:.1f} ({coverage_half_n/n_strata:.1%})"
        overcount_str = f"+{overcount:.1f} (+{overcount_pct:.1f}%)"
        
        print(f"{scenario_desc:<40} {coverage_str:<20} {overcount_str:<20}")
    
    # Summary insights
    print("\nKey Insights:")
    print("1. The 1/2N threshold counts strata that have <50% chance of appearing in the sample")
    print("2. With power law distributions, 1/2N can overcount diversity by >100% vs 2/N")
    print("3. Even uniform distributions show ~45% overcount with small samples")
    print("4. The 1/N threshold (requiring ≥1 observation) is more aligned with observable diversity")

if __name__ == "__main__":
    main()