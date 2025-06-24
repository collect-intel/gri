"""
Monte Carlo simulation and maximum possible score calculations for GRI.

This module provides functions for calculating theoretical maximum GRI and 
Diversity scores using semi-stochastic sampling methodology.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import warnings
from pathlib import Path

from .calculator import calculate_gri


def generate_optimal_sample(
    true_proportions: np.ndarray, 
    sample_size: int, 
    random_seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate an optimal sample allocation using semi-stochastic sampling.
    
    This implements a hybrid approach where larger strata receive deterministic
    allocation while smaller strata are sampled probabilistically.
    
    Parameters
    ----------
    true_proportions : np.ndarray
        1D array of population proportions (must sum to 1.0)
    sample_size : int
        Total sample size
    random_seed : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    np.ndarray
        1D array of sample counts for each stratum
        
    Examples
    --------
    >>> proportions = np.array([0.5, 0.3, 0.15, 0.05])
    >>> sample = generate_optimal_sample(proportions, 100, seed=42)
    >>> print(sample.sum())  # Should equal 100
    100
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Validate proportions
    prop_sum = true_proportions.sum()
    if abs(prop_sum - 1.0) > 1e-6:
        warnings.warn(f"Proportions sum to {prop_sum:.6f}, normalizing to 1.0")
        true_proportions = true_proportions / prop_sum
    
    # Initialize sample counts
    sample_counts = np.zeros(len(true_proportions), dtype=int)
    
    # Calculate ideal sample for each stratum
    ideal_samples = true_proportions * sample_size
    
    # Apply semi-stochastic sampling logic
    for i, ideal in enumerate(ideal_samples):
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
    difference = sample_size - current_total
    
    if difference != 0:
        # Find strata that can be adjusted
        if difference < 0:
            # Need to reduce - only adjust strata with samples
            adjustable_strata = np.where(sample_counts > 0)[0]
        else:
            # Need to add - can adjust any stratum
            adjustable_strata = np.arange(len(sample_counts))
        
        # Randomly adjust samples to match target
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


def calculate_max_gri(
    true_proportions: np.ndarray, 
    sample_counts: np.ndarray
) -> float:
    """
    Calculate GRI score from sample allocation.
    
    Parameters
    ----------
    true_proportions : np.ndarray
        Population proportions
    sample_counts : np.ndarray
        Sample counts for each stratum
        
    Returns
    -------
    float
        GRI score (1 - Total Variation Distance)
    """
    # Convert sample counts to proportions
    total_samples = sample_counts.sum()
    if total_samples == 0:
        return 0.0
    
    sample_proportions = sample_counts / total_samples
    
    # Calculate Total Variation Distance
    tvd = 0.5 * np.sum(np.abs(sample_proportions - true_proportions))
    
    # GRI = 1 - TVD
    return 1 - tvd


def calculate_max_diversity_score(
    true_proportions: np.ndarray, 
    sample_counts: np.ndarray,
    threshold: Optional[float] = None,
    sample_size: Optional[int] = None
) -> float:
    """
    Calculate Diversity Score from sample allocation.
    
    Parameters
    ----------
    true_proportions : np.ndarray
        Population proportions
    sample_counts : np.ndarray
        Sample counts for each stratum
    threshold : float, optional
        Relevance threshold. If None, uses 1/N
    sample_size : int, optional
        Total sample size (required if threshold is None)
        
    Returns
    -------
    float
        Diversity Score (coverage rate of relevant strata)
    """
    if threshold is None:
        if sample_size is None:
            sample_size = sample_counts.sum()
        threshold = 1.0 / sample_size if sample_size > 0 else 0
    
    # Count relevant strata (above threshold)
    relevant_strata = np.sum(true_proportions > threshold)
    
    if relevant_strata == 0:
        return 0.0
    
    # Count represented strata (have samples AND are relevant)
    represented_strata = np.sum((sample_counts > 0) & (true_proportions > threshold))
    
    # Diversity score
    return represented_strata / relevant_strata


def monte_carlo_max_scores(
    benchmark_df: pd.DataFrame,
    sample_size: int,
    dimension_columns: Optional[List[str]] = None,
    n_simulations: int = 1000,
    random_seed: Optional[int] = 42,
    include_diversity: bool = True
) -> Dict[str, Union[float, Dict[str, float]]]:
    """
    Calculate expected maximum GRI and Diversity scores using Monte Carlo simulation.
    
    Parameters
    ----------
    benchmark_df : pd.DataFrame
        Benchmark data with population_proportion column
    sample_size : int
        Sample size to simulate
    dimension_columns : list of str, optional
        Columns defining the dimension (for reporting)
    n_simulations : int, default=1000
        Number of Monte Carlo simulations
    random_seed : int, optional
        Base random seed for reproducibility
    include_diversity : bool, default=True
        Whether to calculate diversity scores
        
    Returns
    -------
    dict
        Simulation results with statistics
        
    Examples
    --------
    >>> results = monte_carlo_max_scores(benchmark, 1000, n_simulations=100)
    >>> print(f"Max GRI: {results['max_gri']['mean']:.4f}")
    """
    # Extract population proportions
    true_proportions = benchmark_df['population_proportion'].values
    
    # Normalize if needed
    prop_sum = true_proportions.sum()
    if abs(prop_sum - 1.0) > 1e-6:
        true_proportions = true_proportions / prop_sum
    
    # Dynamic threshold for diversity
    threshold = 1.0 / sample_size if sample_size > 0 else 0
    
    # Run simulations
    gri_scores = []
    diversity_scores = [] if include_diversity else None
    
    for i in range(n_simulations):
        # Use different seed for each simulation
        sim_seed = random_seed + i if random_seed is not None else None
        
        # Generate optimal sample
        sample_counts = generate_optimal_sample(true_proportions, sample_size, sim_seed)
        
        # Calculate GRI
        gri = calculate_max_gri(true_proportions, sample_counts)
        gri_scores.append(gri)
        
        # Calculate diversity if requested
        if include_diversity:
            diversity = calculate_max_diversity_score(
                true_proportions, sample_counts, threshold
            )
            diversity_scores.append(diversity)
    
    # Convert to arrays for statistics
    gri_scores = np.array(gri_scores)
    
    # Build results
    results = {
        'sample_size': sample_size,
        'n_simulations': n_simulations,
        'total_strata': len(true_proportions),
        'relevant_strata': int(np.sum(true_proportions > threshold)),
        'threshold': threshold,
        'max_gri': {
            'mean': float(np.mean(gri_scores)),
            'std': float(np.std(gri_scores)),
            'min': float(np.min(gri_scores)),
            'max': float(np.max(gri_scores)),
            'median': float(np.median(gri_scores)),
            'q25': float(np.percentile(gri_scores, 25)),
            'q75': float(np.percentile(gri_scores, 75))
        }
    }
    
    if include_diversity:
        diversity_scores = np.array(diversity_scores)
        results['max_diversity'] = {
            'mean': float(np.mean(diversity_scores)),
            'std': float(np.std(diversity_scores)),
            'min': float(np.min(diversity_scores)),
            'max': float(np.max(diversity_scores)),
            'median': float(np.median(diversity_scores)),
            'q25': float(np.percentile(diversity_scores, 25)),
            'q75': float(np.percentile(diversity_scores, 75))
        }
    
    if dimension_columns:
        results['dimension_info'] = {
            'columns': dimension_columns,
            'name': ' × '.join(dimension_columns)
        }
    
    return results


def calculate_max_possible_gri(
    benchmark_df: pd.DataFrame,
    sample_size: int,
    dimension_columns: Optional[List[str]] = None,
    method: str = 'monte_carlo',
    n_simulations: int = 1000,
    random_seed: Optional[int] = 42
) -> float:
    """
    Calculate maximum possible GRI score for a given sample size.
    
    This is a convenience function that returns just the mean maximum GRI.
    
    Parameters
    ----------
    benchmark_df : pd.DataFrame
        Benchmark data
    sample_size : int
        Sample size
    dimension_columns : list of str, optional
        Dimension columns (for validation)
    method : str, default='monte_carlo'
        Calculation method (currently only 'monte_carlo' supported)
    n_simulations : int, default=1000
        Number of simulations for Monte Carlo
    random_seed : int, optional
        Random seed
        
    Returns
    -------
    float
        Expected maximum GRI score
        
    Examples
    --------
    >>> max_gri = calculate_max_possible_gri(benchmark, 1000)
    >>> print(f"Maximum possible GRI: {max_gri:.4f}")
    """
    if method != 'monte_carlo':
        raise ValueError(f"Unsupported method: {method}")
    
    results = monte_carlo_max_scores(
        benchmark_df,
        sample_size,
        dimension_columns,
        n_simulations,
        random_seed,
        include_diversity=False
    )
    
    return results['max_gri']['mean']


def calculate_efficiency_ratio(
    actual_score: float,
    max_possible_score: float
) -> float:
    """
    Calculate efficiency ratio (actual/max possible).
    
    Parameters
    ----------
    actual_score : float
        Actual achieved score
    max_possible_score : float
        Maximum possible score
        
    Returns
    -------
    float
        Efficiency ratio (0-1)
    """
    if max_possible_score <= 0:
        return 0.0
    
    return min(1.0, actual_score / max_possible_score)


def generate_sample_size_curve(
    benchmark_df: pd.DataFrame,
    sample_sizes: List[int],
    dimension_columns: Optional[List[str]] = None,
    n_simulations: int = 100,
    random_seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generate maximum possible scores across multiple sample sizes.
    
    Parameters
    ----------
    benchmark_df : pd.DataFrame
        Benchmark data
    sample_sizes : list of int
        Sample sizes to test
    dimension_columns : list of str, optional
        Dimension columns
    n_simulations : int, default=100
        Simulations per sample size
    random_seed : int, optional
        Random seed
        
    Returns
    -------
    pd.DataFrame
        Results with columns: sample_size, max_gri_mean, max_gri_std,
        max_diversity_mean, max_diversity_std
    """
    results = []
    
    for n in sample_sizes:
        scores = monte_carlo_max_scores(
            benchmark_df,
            n,
            dimension_columns,
            n_simulations,
            random_seed
        )
        
        results.append({
            'sample_size': n,
            'max_gri_mean': scores['max_gri']['mean'],
            'max_gri_std': scores['max_gri']['std'],
            'max_diversity_mean': scores['max_diversity']['mean'],
            'max_diversity_std': scores['max_diversity']['std'],
            'total_strata': scores['total_strata'],
            'relevant_strata': scores['relevant_strata']
        })
    
    return pd.DataFrame(results)