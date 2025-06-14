"""
Analysis functions for Global Representativeness Index calculations.

This module provides functions for segment analysis, deviation calculations,
and identifying top contributing segments to representativeness gaps.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Literal
import warnings

from .utils import aggregate_data


def check_category_alignment(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    columns: List[str]
) -> Dict[str, Dict[str, Union[int, set, float]]]:
    """
    Check alignment between survey and benchmark categories.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data with demographic columns
    benchmark_df : pd.DataFrame
        Benchmark data with same columns
    columns : list of str
        Columns to check for alignment
        
    Returns
    -------
    dict
        Alignment results for each column with statistics
        
    Examples
    --------
    >>> alignment = check_category_alignment(survey, benchmark, ['country', 'gender'])
    >>> print(alignment['country']['coverage'])
    0.95  # 95% of survey countries found in benchmark
    """
    alignment_results = {}
    
    for col in columns:
        if col in survey_df.columns and col in benchmark_df.columns:
            survey_categories = set(survey_df[col].dropna().unique())
            benchmark_categories = set(benchmark_df[col].dropna().unique())
            
            matched = survey_categories.intersection(benchmark_categories)
            unmatched = survey_categories - benchmark_categories
            
            alignment_results[col] = {
                'total_survey': len(survey_categories),
                'total_benchmark': len(benchmark_categories),
                'matched': len(matched),
                'unmatched': unmatched,
                'coverage': len(matched) / len(survey_categories) if survey_categories else 0
            }
        else:
            missing_in = []
            if col not in survey_df.columns:
                missing_in.append('survey')
            if col not in benchmark_df.columns:
                missing_in.append('benchmark')
                
            alignment_results[col] = {
                'total_survey': 0,
                'total_benchmark': 0,
                'matched': 0,
                'unmatched': set(),
                'coverage': 0,
                'missing_in': missing_in
            }
    
    return alignment_results


def calculate_segment_deviations(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    dimension_columns: List[str],
    normalize: bool = True
) -> pd.DataFrame:
    """
    Calculate deviation between survey and benchmark for each segment.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data
    benchmark_df : pd.DataFrame
        Benchmark data with population_proportion column
    dimension_columns : list of str
        Columns defining the dimension (e.g., ['country', 'gender', 'age_group'])
    normalize : bool, default=True
        Whether to normalize deviations by benchmark proportion
        
    Returns
    -------
    pd.DataFrame
        DataFrame with segments and their deviation metrics
        
    Examples
    --------
    >>> deviations = calculate_segment_deviations(
    ...     survey, benchmark, ['country', 'gender', 'age_group']
    ... )
    >>> print(deviations.head())
       country gender age_group  sample_prop  benchmark_prop  deviation  abs_deviation
    0  India   Male   18-25     0.045        0.023          0.022      0.022
    """
    # Aggregate survey data
    survey_agg = aggregate_data(survey_df, dimension_columns)
    
    # Calculate proportions from counts
    total_count = survey_agg['count'].sum()
    survey_agg['proportion'] = survey_agg['count'] / total_count
    
    # Merge with benchmark
    merged = pd.merge(
        survey_agg,
        benchmark_df,
        on=dimension_columns,
        how='outer',
        suffixes=('_sample', '_benchmark')
    )
    
    # Handle column names - benchmark might have 'population_proportion' instead of 'proportion'
    if 'proportion' in merged.columns and 'population_proportion' in merged.columns:
        merged['sample_proportion'] = merged['proportion'].fillna(0)
        merged['benchmark_proportion'] = merged['population_proportion'].fillna(0)
    else:
        # If suffixes were applied
        merged['sample_proportion'] = merged.get('proportion_sample', 0).fillna(0)
        merged['benchmark_proportion'] = merged.get('proportion_benchmark', 0).fillna(0)
    
    # Calculate deviations
    merged['deviation'] = merged['sample_proportion'] - merged['benchmark_proportion']
    merged['abs_deviation'] = merged['deviation'].abs()
    
    if normalize:
        # Normalized deviation (percentage of benchmark)
        merged['normalized_deviation'] = np.where(
            merged['benchmark_proportion'] > 0,
            merged['deviation'] / merged['benchmark_proportion'],
            np.inf if merged['sample_proportion'].sum() > 0 else 0
        )
    
    # Calculate contribution to total variation distance
    merged['tvd_contribution'] = merged['abs_deviation'] / 2
    
    # Sort by absolute deviation
    merged = merged.sort_values('abs_deviation', ascending=False)
    
    # Columns are already named correctly, no rename needed
    
    return merged


def identify_top_contributors(
    deviations: pd.DataFrame,
    n: int = 10,
    contribution_type: Literal['over', 'under', 'both'] = 'both',
    min_benchmark_prop: float = 0.0001
) -> pd.DataFrame:
    """
    Identify segments that contribute most to representativeness gaps.
    
    Parameters
    ----------
    deviations : pd.DataFrame
        Output from calculate_segment_deviations
    n : int, default=10
        Number of top segments to return
    contribution_type : {'over', 'under', 'both'}, default='both'
        Whether to show over-represented, under-represented, or both
    min_benchmark_prop : float, default=0.0001
        Minimum benchmark proportion to consider (filters out very small segments)
        
    Returns
    -------
    pd.DataFrame
        Top contributing segments with their metrics
        
    Examples
    --------
    >>> top_over = identify_top_contributors(deviations, n=5, contribution_type='over')
    >>> print(f"Top 5 over-represented: {top_over['segment_name'].tolist()}")
    """
    # Filter by minimum benchmark proportion
    filtered = deviations[deviations['benchmark_proportion'] >= min_benchmark_prop].copy()
    
    # Add representation category
    filtered['representation'] = pd.cut(
        filtered['deviation'],
        bins=[-np.inf, -0.001, 0.001, np.inf],
        labels=['under', 'balanced', 'over']
    )
    
    # Filter by contribution type
    if contribution_type == 'over':
        filtered = filtered[filtered['deviation'] > 0]
    elif contribution_type == 'under':
        filtered = filtered[filtered['deviation'] < 0]
    # else 'both' - no filtering
    
    # Get top n by absolute deviation
    top_segments = filtered.nlargest(n, 'abs_deviation')
    
    # Add cumulative impact
    top_segments['cumulative_tvd'] = top_segments['tvd_contribution'].cumsum()
    
    # Create readable segment names
    dimension_cols = [col for col in top_segments.columns 
                     if col not in ['sample_proportion', 'benchmark_proportion', 
                                   'deviation', 'abs_deviation', 'normalized_deviation',
                                   'tvd_contribution', 'representation', 'cumulative_tvd']]
    
    if dimension_cols:
        top_segments['segment_name'] = top_segments[dimension_cols].apply(
            lambda row: ' - '.join(str(row[col]) for col in dimension_cols), axis=1
        )
    
    return top_segments


def generate_alignment_report(
    survey_df: pd.DataFrame,
    benchmarks: Dict[str, pd.DataFrame],
    dimensions_to_check: Optional[List[str]] = None
) -> Dict[str, Dict]:
    """
    Generate comprehensive alignment report for all dimensions.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data
    benchmarks : dict
        Dictionary of benchmark DataFrames by dimension name
    dimensions_to_check : list of str, optional
        Specific dimensions to check. If None, checks all available.
        
    Returns
    -------
    dict
        Comprehensive alignment report with statistics and recommendations
        
    Examples
    --------
    >>> report = generate_alignment_report(survey, benchmarks)
    >>> print(report['Country × Gender × Age']['overall_alignment'])
    0.95  # 95% overall alignment
    """
    if dimensions_to_check is None:
        dimensions_to_check = list(benchmarks.keys())
    
    report = {}
    
    # Define dimension columns
    dimension_columns_map = {
        'Country × Gender × Age': ['country', 'gender', 'age_group'],
        'Country × Religion': ['country', 'religion'],
        'Country × Environment': ['country', 'environment'],
        'Country': ['country'],
        'Gender': ['gender'],
        'Age Group': ['age_group'],
        'Religion': ['religion'],
        'Environment': ['environment'],
        'Region × Gender × Age': ['region', 'gender', 'age_group'],
        'Region × Religion': ['region', 'religion'],
        'Region × Environment': ['region', 'environment'],
        'Region': ['region'],
        'Continent': ['continent']
    }
    
    for dimension in dimensions_to_check:
        if dimension not in benchmarks:
            continue
            
        benchmark_df = benchmarks[dimension]
        columns = dimension_columns_map.get(dimension, [])
        
        if not all(col in survey_df.columns for col in columns):
            report[dimension] = {
                'status': 'skipped',
                'reason': f'Missing columns in survey data: {columns}'
            }
            continue
        
        # Check alignment
        alignment = check_category_alignment(survey_df, benchmark_df, columns)
        
        # Calculate overall metrics
        total_coverage = np.mean([stats['coverage'] for stats in alignment.values()])
        
        # Identify issues
        issues = []
        for col, stats in alignment.items():
            if stats['coverage'] < 1.0:
                issues.append({
                    'column': col,
                    'coverage': stats['coverage'],
                    'unmatched_count': len(stats['unmatched']),
                    'unmatched_sample': list(stats['unmatched'])[:5]  # First 5
                })
        
        report[dimension] = {
            'status': 'complete',
            'overall_alignment': total_coverage,
            'column_alignment': alignment,
            'issues': issues,
            'recommendation': _generate_recommendation(total_coverage, issues)
        }
    
    return report


def _generate_recommendation(coverage: float, issues: List[Dict]) -> str:
    """Generate recommendation based on alignment coverage."""
    if coverage >= 0.95:
        return "Excellent alignment. Ready for analysis."
    elif coverage >= 0.80:
        return "Good alignment. Consider mapping unmapped categories or excluding them."
    elif coverage >= 0.60:
        return "Moderate alignment. Review unmapped categories and update segment mappings."
    else:
        return "Poor alignment. Significant mapping work needed before analysis."


def calculate_dimension_impact(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    dimension_columns: List[str],
    target_segments: Optional[pd.DataFrame] = None,
    n_targets: int = 10
) -> Dict[str, float]:
    """
    Calculate the impact on GRI score of fixing top deviation segments.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data
    benchmark_df : pd.DataFrame
        Benchmark data
    dimension_columns : list of str
        Columns defining the dimension
    target_segments : pd.DataFrame, optional
        Specific segments to analyze. If None, uses top deviations.
    n_targets : int, default=10
        Number of top segments to analyze if target_segments not provided
        
    Returns
    -------
    dict
        Impact metrics including current GRI, potential GRI, and improvement
        
    Examples
    --------
    >>> impact = calculate_dimension_impact(survey, benchmark, ['country', 'gender'])
    >>> print(f"Fixing top 10 segments would improve GRI by {impact['improvement']:.3f}")
    """
    from .calculator import calculate_gri
    
    # Calculate current GRI
    current_gri = calculate_gri(survey_df, benchmark_df, dimension_columns)
    
    # Get deviations if target segments not provided
    if target_segments is None:
        deviations = calculate_segment_deviations(
            survey_df, benchmark_df, dimension_columns
        )
        target_segments = identify_top_contributors(
            deviations, n=n_targets, contribution_type='both'
        )
    
    # Calculate GRI improvement if we fixed these segments
    total_tvd_reduction = target_segments['tvd_contribution'].sum()
    potential_gri = min(1.0, current_gri + total_tvd_reduction)
    
    # Calculate segment-by-segment impact
    segment_impacts = []
    cumulative_gri = current_gri
    
    for _, segment in target_segments.iterrows():
        cumulative_gri = min(1.0, cumulative_gri + segment['tvd_contribution'])
        segment_impacts.append({
            'segment': segment.get('segment_name', 'Unknown'),
            'individual_impact': segment['tvd_contribution'],
            'cumulative_gri': cumulative_gri
        })
    
    return {
        'current_gri': current_gri,
        'potential_gri': potential_gri,
        'improvement': potential_gri - current_gri,
        'improvement_pct': (potential_gri - current_gri) / current_gri * 100,
        'segment_impacts': segment_impacts
    }