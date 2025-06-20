"""
Strategic Representativeness Index (SRI) implementation.

The SRI measures how well a sample matches the strategically optimal target
that minimizes total uncertainty across all demographic groups.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple


def calculate_strategic_targets(population_proportions: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate the strategic target proportions using the square root formula.
    
    The strategic target is: s*_i = sqrt(π_i) / Σ_j sqrt(π_j)
    
    This balances between proportional representation and equal representation,
    giving smaller groups more weight than proportional but less than equal.
    
    Args:
        population_proportions: Dict mapping stratum to population proportion
        
    Returns:
        Dict mapping stratum to strategic target proportion
    """
    # Calculate square roots
    sqrt_props = {k: np.sqrt(v) for k, v in population_proportions.items()}
    
    # Normalize to sum to 1
    total_sqrt = sum(sqrt_props.values())
    strategic_targets = {k: v / total_sqrt for k, v in sqrt_props.items()}
    
    return strategic_targets


def calculate_sri(
    sample_proportions: Dict[str, float],
    population_proportions: Dict[str, float]
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate the Strategic Representativeness Index (SRI).
    
    SRI = 1 - 0.5 * Σ|s_i - s*_i|
    
    Where s_i is actual sample proportion and s*_i is strategic target.
    
    Args:
        sample_proportions: Dict mapping stratum to sample proportion
        population_proportions: Dict mapping stratum to population proportion
        
    Returns:
        Tuple of (SRI score, strategic targets dict)
    """
    # Calculate strategic targets
    strategic_targets = calculate_strategic_targets(population_proportions)
    
    # Calculate total variation distance from strategic target
    tvd = 0.0
    for stratum in population_proportions:
        sample_prop = sample_proportions.get(stratum, 0.0)
        target_prop = strategic_targets[stratum]
        tvd += abs(sample_prop - target_prop)
    
    # Calculate SRI
    sri = 1 - 0.5 * tvd
    
    return sri, strategic_targets


def calculate_sri_from_dataframes(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    strata_cols: List[str]
) -> Tuple[float, pd.DataFrame]:
    """
    Calculate SRI using the same interface as calculate_gri.
    
    Args:
        survey_df: DataFrame with survey participant data
        benchmark_df: DataFrame with population proportions
        strata_cols: List of columns defining the strata
        
    Returns:
        Tuple of (SRI score, detailed breakdown DataFrame)
    """
    # Handle empty survey case
    if len(survey_df) == 0:
        return 0.0, pd.DataFrame()
    
    # Calculate sample proportions
    sample_counts = survey_df.groupby(strata_cols).size().reset_index(name='count')
    total_participants = len(survey_df)
    sample_counts['sample_proportion'] = sample_counts['count'] / total_participants
    
    # Prepare benchmark proportions
    benchmark_props = benchmark_df[strata_cols + ['population_proportion']].copy()
    
    # Merge sample and benchmark
    merged = pd.merge(benchmark_props, sample_counts[strata_cols + ['sample_proportion', 'count']], 
                     on=strata_cols, how='outer')
    
    # Fill NaN values
    merged['sample_proportion'] = merged['sample_proportion'].fillna(0)
    merged['population_proportion'] = merged['population_proportion'].fillna(0)
    merged['count'] = merged['count'].fillna(0).astype(int)
    
    # Create stratum identifier
    if len(strata_cols) == 1:
        merged['stratum'] = merged[strata_cols[0]]
    else:
        merged['stratum'] = merged[strata_cols].apply(
            lambda x: ' × '.join(x.astype(str)), axis=1
        )
    
    # Convert to dictionaries
    sample_props = dict(zip(merged['stratum'], merged['sample_proportion']))
    pop_props = dict(zip(merged['stratum'], merged['population_proportion']))
    
    # Calculate SRI and strategic targets
    sri, strategic_targets = calculate_sri(sample_props, pop_props)
    
    # Create detailed breakdown
    details = []
    for _, row in merged.iterrows():
        stratum = row['stratum']
        sample_prop = row['sample_proportion']
        pop_prop = row['population_proportion']
        strategic_target = strategic_targets.get(stratum, 0)
        
        # Calculate deviations
        deviation_from_population = abs(sample_prop - pop_prop)
        deviation_from_strategic = abs(sample_prop - strategic_target)
        
        details.append({
            'stratum': stratum,
            'population_prop': pop_prop,
            'strategic_target': strategic_target,
            'sample_prop': sample_prop,
            'sample_count': row['count'],
            'target_vs_population': strategic_target - pop_prop,
            'deviation_from_target': deviation_from_strategic,
            'deviation_from_population': deviation_from_population,
            'sri_contribution': 0.5 * deviation_from_strategic
        })
    
    details_df = pd.DataFrame(details).sort_values('population_prop', ascending=False)
    
    return sri, details_df


def compare_allocation_methods(
    population_proportions: Dict[str, float],
    total_n: int
) -> pd.DataFrame:
    """
    Compare proportional vs strategic allocation for a given sample size.
    
    Args:
        population_proportions: Population proportions by stratum
        total_n: Total sample size to allocate
        
    Returns:
        DataFrame comparing the two allocation methods
    """
    # Calculate strategic targets
    strategic_targets = calculate_strategic_targets(population_proportions)
    
    # Create comparison
    comparison_data = []
    for stratum, pop_prop in population_proportions.items():
        proportional_n = int(np.round(total_n * pop_prop))
        strategic_n = int(np.round(total_n * strategic_targets[stratum]))
        
        comparison_data.append({
            'stratum': stratum,
            'population_pct': pop_prop * 100,
            'proportional_n': proportional_n,
            'strategic_n': strategic_n,
            'difference': strategic_n - proportional_n,
            'strategic_boost': (strategic_targets[stratum] / pop_prop) if pop_prop > 0 else np.inf
        })
    
    return pd.DataFrame(comparison_data).sort_values('population_pct', ascending=False)