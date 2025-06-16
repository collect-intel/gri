"""
Variance-Weighted Representativeness Score (VWRS) and Optimal Sample Allocation

This module implements:
1. VWRS: A modified GRI that accounts for sampling variance in each stratum
2. Optimal allocation: Neyman allocation to minimize overall sampling error
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional


def calculate_vwrs(
    sample_proportions: Dict[str, float],
    population_proportions: Dict[str, float],
    sample_sizes: Dict[str, int]
) -> float:
    """
    Calculate Variance-Weighted Representativeness Score (VWRS).
    
    VWRS = 1 - Σ(w_i × |p_i - π_i|)
    
    Where weights w_i account for the sampling variance in each stratum.
    
    Args:
        sample_proportions: Dict mapping stratum name to sample proportion
        population_proportions: Dict mapping stratum name to population proportion
        sample_sizes: Dict mapping stratum name to number of samples
        
    Returns:
        VWRS score between 0 and 1 (1 = perfect representation)
    """
    total_weighted_error = 0.0
    total_weight = 0.0
    
    for stratum in population_proportions:
        if stratum not in sample_proportions:
            sample_proportions[stratum] = 0.0
            sample_sizes[stratum] = 0
            
        p_i = sample_proportions[stratum]
        pi_i = population_proportions[stratum]
        n_i = sample_sizes[stratum]
        
        # Calculate standard error for this stratum
        if n_i > 0:
            se_i = np.sqrt(p_i * (1 - p_i) / n_i)
        else:
            se_i = 1.0  # Maximum uncertainty
            
        # Weight by population size × standard error
        weight = pi_i * se_i
        
        total_weighted_error += weight * abs(p_i - pi_i)
        total_weight += weight
    
    if total_weight > 0:
        normalized_error = total_weighted_error / total_weight
    else:
        normalized_error = 1.0
        
    return 1 - normalized_error


def optimal_allocation(
    population_proportions: Dict[str, float],
    total_sample_size: int,
    within_stratum_variances: Optional[Dict[str, float]] = None
) -> Dict[str, int]:
    """
    Calculate optimal sample allocation using Neyman allocation.
    
    n_i = N × (π_i × σ_i) / Σ(π_j × σ_j)
    
    Args:
        population_proportions: Dict mapping stratum name to population proportion
        total_sample_size: Total number of samples to allocate
        within_stratum_variances: Optional dict of known within-stratum variances
                                 If None, assumes maximum variance (0.25)
        
    Returns:
        Dict mapping stratum name to optimal number of samples
    """
    allocations = {}
    
    # Calculate allocation proportions
    total_allocation_weight = 0.0
    allocation_weights = {}
    
    for stratum, pi_i in population_proportions.items():
        # Use provided variance or assume maximum variance for binary outcome
        if within_stratum_variances and stratum in within_stratum_variances:
            var_i = within_stratum_variances[stratum]
        else:
            # For binary outcomes, variance = p(1-p), maximum at p=0.5
            var_i = 0.25
            
        sigma_i = np.sqrt(var_i)
        
        # Neyman allocation weight
        weight = pi_i * sigma_i
        allocation_weights[stratum] = weight
        total_allocation_weight += weight
    
    # Allocate samples
    allocated = 0
    for stratum, weight in allocation_weights.items():
        if total_allocation_weight > 0:
            proportion = weight / total_allocation_weight
            n_i = int(np.round(total_sample_size * proportion))
        else:
            n_i = 0
            
        allocations[stratum] = n_i
        allocated += n_i
    
    # Adjust for rounding errors
    if allocated != total_sample_size:
        # Add/subtract from largest stratum
        largest_stratum = max(allocations.keys(), key=lambda k: allocations[k])
        allocations[largest_stratum] += (total_sample_size - allocated)
    
    return allocations


def compare_gri_vwrs(
    sample_df: pd.DataFrame,
    population_df: pd.DataFrame,
    stratum_column: str
) -> Tuple[float, float, pd.DataFrame]:
    """
    Compare traditional GRI with VWRS for a given demographic dimension.
    
    Args:
        sample_df: DataFrame with sample data
        population_df: DataFrame with population proportions
        stratum_column: Column name defining the strata
        
    Returns:
        Tuple of (GRI score, VWRS score, detailed comparison DataFrame)
    """
    # Calculate sample proportions and sizes
    sample_counts = sample_df[stratum_column].value_counts()
    total_sample = len(sample_df)
    
    sample_proportions = (sample_counts / total_sample).to_dict()
    sample_sizes = sample_counts.to_dict()
    
    # Get population proportions (assumed to be pre-calculated)
    population_proportions = population_df.set_index(stratum_column)['proportion'].to_dict()
    
    # Calculate traditional GRI
    gri = 0.0
    for stratum in population_proportions:
        p_i = sample_proportions.get(stratum, 0.0)
        pi_i = population_proportions[stratum]
        gri += 0.5 * abs(p_i - pi_i)
    gri = 1 - gri
    
    # Calculate VWRS
    vwrs = calculate_vwrs(sample_proportions, population_proportions, sample_sizes)
    
    # Create detailed comparison
    comparison_data = []
    for stratum in population_proportions:
        p_i = sample_proportions.get(stratum, 0.0)
        pi_i = population_proportions[stratum]
        n_i = sample_sizes.get(stratum, 0)
        
        se_i = np.sqrt(p_i * (1 - p_i) / n_i) if n_i > 0 else 1.0
        
        comparison_data.append({
            'stratum': stratum,
            'population_prop': pi_i,
            'sample_prop': p_i,
            'sample_size': n_i,
            'standard_error': se_i,
            'absolute_deviation': abs(p_i - pi_i),
            'gri_contribution': 0.5 * abs(p_i - pi_i),
            'vwrs_weight': pi_i * se_i
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    return gri, vwrs, comparison_df