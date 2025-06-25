"""
Utility to create simplified benchmarks for any dimension to avoid VWRS paradox.

This module provides a general approach to simplifying benchmarks by:
1. Keeping major strata that exceed a threshold
2. Grouping minor strata into an "Others" category
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Union


def simplify_benchmark(
    benchmark_df: pd.DataFrame,
    threshold: Optional[float] = None,
    top_n: Optional[int] = None,
    min_coverage: float = 0.8,
    others_label: str = "Others",
    proportion_col: str = "population_proportion"
) -> pd.DataFrame:
    """
    Create a simplified benchmark by grouping small strata.
    
    Args:
        benchmark_df: Original benchmark DataFrame
        threshold: Include strata with proportion >= threshold
        top_n: Include top N strata by proportion
        min_coverage: Minimum population coverage before grouping rest
        others_label: Label for grouped small strata
        proportion_col: Name of the proportion column
        
    Returns:
        Simplified benchmark DataFrame
    
    Examples:
        # Keep top 30 countries
        simplified = simplify_benchmark(country_benchmark, top_n=30)
        
        # Keep strata > 1% of population
        simplified = simplify_benchmark(religion_benchmark, threshold=0.01)
        
        # Keep enough strata to cover 80% of population
        simplified = simplify_benchmark(occupation_benchmark, min_coverage=0.8)
    """
    # Sort by proportion descending
    df = benchmark_df.copy()
    df = df.sort_values(proportion_col, ascending=False)
    
    # Determine which strata to keep
    if top_n is not None:
        # Keep top N
        keep_indices = min(top_n, len(df))
    elif threshold is not None:
        # Keep those above threshold
        keep_indices = sum(df[proportion_col] >= threshold)
    else:
        # Keep enough to reach min_coverage
        cumsum = df[proportion_col].cumsum()
        keep_indices = sum(cumsum < min_coverage) + 1
    
    # Split into kept and grouped
    kept_df = df.iloc[:keep_indices].copy()
    grouped_df = df.iloc[keep_indices:]
    
    # Calculate "Others" proportion
    others_proportion = grouped_df[proportion_col].sum()
    
    # Only add "Others" if there's something to group
    if others_proportion > 0:
        # Get the stratum column name (first non-proportion column)
        stratum_cols = [col for col in df.columns if col != proportion_col]
        
        # Create Others row
        others_row = {}
        for col in stratum_cols:
            others_row[col] = others_label
        others_row[proportion_col] = others_proportion
        
        # Append to kept data
        result_df = pd.concat([
            kept_df,
            pd.DataFrame([others_row])
        ], ignore_index=True)
    else:
        result_df = kept_df
    
    return result_df


def analyze_simplification_impact(
    original_df: pd.DataFrame,
    simplified_df: pd.DataFrame,
    proportion_col: str = "population_proportion"
) -> dict:
    """
    Analyze the impact of benchmark simplification.
    
    Returns:
        Dictionary with analysis metrics
    """
    original_strata = len(original_df)
    simplified_strata = len(simplified_df)
    
    # Find "Others" row
    others_rows = simplified_df[simplified_df.iloc[:, 0].str.contains("Other", case=False, na=False)]
    others_proportion = others_rows[proportion_col].sum() if not others_rows.empty else 0
    
    return {
        "original_strata": original_strata,
        "simplified_strata": simplified_strata,
        "reduction_ratio": (original_strata - simplified_strata) / original_strata,
        "others_proportion": others_proportion,
        "others_strata_count": original_strata - simplified_strata + (1 if others_proportion > 0 else 0),
        "major_strata_coverage": 1 - others_proportion
    }


def create_adaptive_simplification(
    benchmark_df: pd.DataFrame,
    sample_df: pd.DataFrame,
    stratum_cols: List[str],
    proportion_col: str = "population_proportion",
    coverage_target: float = 0.95
) -> pd.DataFrame:
    """
    Create a simplified benchmark adapted to actual sample coverage.
    
    Keeps all strata that appear in the sample, plus major strata
    needed to reach coverage_target.
    
    Args:
        benchmark_df: Original benchmark
        sample_df: Sample data
        stratum_cols: Columns defining strata
        proportion_col: Name of proportion column
        coverage_target: Target population coverage
        
    Returns:
        Adaptively simplified benchmark
    """
    # Get strata that appear in sample
    if len(stratum_cols) == 1:
        sample_strata = set(sample_df[stratum_cols[0]].unique())
    else:
        sample_strata = set(
            tuple(row) for row in sample_df[stratum_cols].drop_duplicates().values
        )
    
    # Mark which benchmark strata appear in sample
    benchmark_df = benchmark_df.copy()
    if len(stratum_cols) == 1:
        benchmark_df['in_sample'] = benchmark_df[stratum_cols[0]].isin(sample_strata)
    else:
        benchmark_df['in_sample'] = benchmark_df[stratum_cols].apply(
            lambda row: tuple(row) in sample_strata, axis=1
        )
    
    # Sort by: in_sample first, then by proportion
    benchmark_df = benchmark_df.sort_values(
        ['in_sample', proportion_col], 
        ascending=[False, False]
    )
    
    # Keep all sampled strata plus enough others to reach coverage
    cumsum = benchmark_df[proportion_col].cumsum()
    keep_mask = (benchmark_df['in_sample']) | (cumsum <= coverage_target)
    
    # Ensure we keep at least one more after reaching target
    keep_indices = keep_mask.sum()
    if keep_indices < len(benchmark_df) and cumsum.iloc[keep_indices-1] < coverage_target:
        keep_mask.iloc[keep_indices] = True
    
    # Split and create simplified version
    kept_df = benchmark_df[keep_mask].drop('in_sample', axis=1)
    grouped_df = benchmark_df[~keep_mask]
    
    # Add "Others" if needed
    others_proportion = grouped_df[proportion_col].sum()
    if others_proportion > 0:
        others_row = {col: "Others" for col in stratum_cols}
        others_row[proportion_col] = others_proportion
        result_df = pd.concat([kept_df, pd.DataFrame([others_row])], ignore_index=True)
    else:
        result_df = kept_df.copy()
    
    return result_df


# Example usage functions
def simplify_country_benchmark(benchmark_df: pd.DataFrame, top_n: int = 30) -> pd.DataFrame:
    """Simplify country benchmark to top N countries plus Others."""
    return simplify_benchmark(benchmark_df, top_n=top_n, others_label="Other Countries")


def simplify_religion_benchmark(benchmark_df: pd.DataFrame, threshold: float = 0.01) -> pd.DataFrame:
    """Simplify religion benchmark keeping religions > 1% of population."""
    return simplify_benchmark(benchmark_df, threshold=threshold, others_label="Other Religions")


def simplify_occupation_benchmark(benchmark_df: pd.DataFrame, min_coverage: float = 0.9) -> pd.DataFrame:
    """Simplify occupation benchmark to cover 90% of population."""
    return simplify_benchmark(benchmark_df, min_coverage=min_coverage, others_label="Other Occupations")