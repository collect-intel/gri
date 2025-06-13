"""
Configuration-aware GRI calculation functions.

This module provides enhanced GRI calculation functions that work with
the configuration system for flexible dimension and segment management.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from .calculator import calculate_gri, calculate_diversity_score
from .config import get_config, GRIConfig
from .simulation import monte_carlo_max_scores


def standardize_survey_data(
    survey_df: pd.DataFrame, 
    survey_source: str,
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """
    Standardize survey data using segment mappings from configuration.
    
    Args:
        survey_df: Raw survey data
        survey_source: Source identifier (e.g., 'global_dialogues', 'world_values_survey')
        config: Configuration instance (uses global if None)
        
    Returns:
        Standardized survey DataFrame with GRI standard segment names
    """
    if config is None:
        config = get_config()
    
    df = survey_df.copy()
    
    # Get survey mappings for this source
    survey_mappings = config.segments.get("survey_mappings", {}).get(survey_source, {})
    
    # Apply standardization for each segment type
    for segment_type, mapping in survey_mappings.items():
        if segment_type in df.columns:
            # Handle inheritance
            if isinstance(mapping, dict) and "inherit_from" in mapping:
                inherit_path = mapping["inherit_from"].split(".")
                base_mapping = config.segments
                for key in inherit_path:
                    base_mapping = base_mapping[key]
                mapping = base_mapping
            
            # Create reverse mapping (source_value -> standard_value)
            reverse_mapping = {}
            for standard_value, source_values in mapping.items():
                for source_value in source_values:
                    reverse_mapping[source_value] = standard_value
            
            # Apply mapping
            df[segment_type] = df[segment_type].map(reverse_mapping)
            
            # Remove rows where mapping failed (excluded segments)
            df = df.dropna(subset=[segment_type])
    
    return df


def add_regional_dimensions(
    df: pd.DataFrame,
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """
    Add regional and continental columns to a DataFrame with country data.
    
    Args:
        df: DataFrame with 'country' column
        config: Configuration instance (uses global if None)
        
    Returns:
        DataFrame with added 'region' and 'continent' columns
    """
    if config is None:
        config = get_config()
    
    if 'country' not in df.columns:
        return df
    
    df = df.copy()
    
    # Add region mapping
    country_to_region = config.get_country_to_region_mapping()
    df['region'] = df['country'].map(country_to_region)
    
    # Add continent mapping
    country_to_continent = config.get_country_to_continent_mapping()
    df['continent'] = df['country'].map(country_to_continent)
    
    return df


def aggregate_benchmark_for_dimension(
    benchmark_df: pd.DataFrame,
    dimension_columns: List[str],
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """
    Aggregate benchmark data for a specific dimension.
    
    This handles cases where we need coarser-grained dimensions by
    aggregating existing benchmark data.
    
    Args:
        benchmark_df: Original benchmark data
        dimension_columns: Columns defining the desired dimension
        config: Configuration instance (uses global if None)
        
    Returns:
        Aggregated benchmark DataFrame for the specified dimension
    """
    if config is None:
        config = get_config()
    
    df = benchmark_df.copy()
    
    # Add regional dimensions if needed
    if 'region' in dimension_columns or 'continent' in dimension_columns:
        df = add_regional_dimensions(df, config)
    
    # Check if we already have the exact columns
    if all(col in df.columns for col in dimension_columns):
        # Aggregate by the requested dimensions
        result = df.groupby(dimension_columns)['population_proportion'].sum().reset_index()
        return result
    
    # Handle special cases where we need to aggregate existing data
    available_cols = [col for col in dimension_columns if col in df.columns]
    
    if len(available_cols) < len(dimension_columns):
        missing_cols = [col for col in dimension_columns if col not in df.columns]
        raise ValueError(f"Cannot create dimension {dimension_columns}. Missing columns: {missing_cols}")
    
    # If we have more columns than needed, aggregate to the requested level
    result = df.groupby(dimension_columns)['population_proportion'].sum().reset_index()
    return result


def calculate_gri_for_dimension(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    dimension: Dict[str, Any],
    config: Optional[GRIConfig] = None
) -> Tuple[float, float]:
    """
    Calculate GRI and Diversity scores for a specific dimension configuration.
    
    Args:
        survey_df: Standardized survey data
        benchmark_df: Benchmark data
        dimension: Dimension configuration from config
        config: Configuration instance (uses global if None)
        
    Returns:
        Tuple of (gri_score, diversity_score)
    """
    if config is None:
        config = get_config()
    
    # Validate dimension requirements
    if not config.validate_dimension_requirements(dimension):
        raise ValueError(f"Dimension '{dimension['name']}' requirements not satisfied")
    
    # Get dimension columns
    columns = dimension["columns"]
    
    # Prepare benchmark data for this dimension
    agg_benchmark = aggregate_benchmark_for_dimension(benchmark_df, columns, config)
    
    # Add regional dimensions to survey if needed
    survey_with_regions = survey_df.copy()
    if 'region' in columns or 'continent' in columns:
        survey_with_regions = add_regional_dimensions(survey_with_regions, config)
    
    # Calculate GRI and Diversity scores
    gri_score = calculate_gri(survey_with_regions, agg_benchmark, columns)
    diversity_score = calculate_diversity_score(survey_with_regions, agg_benchmark, columns)
    
    return gri_score, diversity_score


def calculate_gri_scorecard(
    survey_df: pd.DataFrame,
    benchmark_data: Dict[str, pd.DataFrame],
    survey_source: str = "global_dialogues",
    use_extended_dimensions: bool = False,
    config: Optional[GRIConfig] = None,
    dimensions: Optional[Union[str, List[str]]] = None,
    include_max_possible: bool = False,
    n_simulations: int = 1000,
    random_seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Calculate a complete GRI scorecard using configuration-defined dimensions.
    
    Args:
        survey_df: Raw survey data
        benchmark_data: Dictionary of benchmark DataFrames keyed by type
                       (e.g., {'age_gender': df, 'religion': df, 'environment': df})
        survey_source: Survey source identifier for segment mapping
        use_extended_dimensions: Whether to include extended dimensions
        config: Configuration instance (uses global if None)
        dimensions: Specific dimensions to calculate. If 'all', calculates all available.
                   If None, uses standard scorecard.
        include_max_possible: Whether to include maximum possible scores
        n_simulations: Number of Monte Carlo simulations for max scores
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with GRI scorecard results
    """
    if config is None:
        config = get_config()
    
    # Standardize survey data
    standardized_survey = standardize_survey_data(survey_df, survey_source, config)
    
    # Get dimensions to calculate
    if dimensions == 'all':
        dimensions_list = config.get_all_dimensions()
    elif dimensions is not None:
        # Handle specific dimension names
        all_dims = config.get_all_dimensions()
        dim_map = {d['name']: d for d in all_dims}
        if isinstance(dimensions, str):
            dimensions = [dimensions]
        dimensions_list = [dim_map[name] for name in dimensions if name in dim_map]
    elif use_extended_dimensions:
        dimensions_list = config.get_all_dimensions()
    else:
        dimensions_list = config.get_standard_scorecard()
    
    # Calculate scores for each dimension
    results = []
    
    # Get sample size for max calculations
    sample_size = len(standardized_survey)
    
    for dimension in dimensions_list:
        try:
            # Determine which benchmark data to use
            columns = dimension["columns"]
            
            # Choose appropriate benchmark dataset
            if set(["country", "gender", "age_group"]).issubset(set(columns)):
                benchmark_df = benchmark_data.get("age_gender")
            elif set(["country", "religion"]).issubset(set(columns)):
                benchmark_df = benchmark_data.get("religion")
            elif set(["country", "environment"]).issubset(set(columns)):
                benchmark_df = benchmark_data.get("environment")
            else:
                # For single dimensions or regional, use the most comprehensive dataset
                benchmark_df = benchmark_data.get("age_gender")
            
            if benchmark_df is None:
                print(f"Warning: No suitable benchmark data for dimension '{dimension['name']}'")
                continue
            
            # Calculate scores
            gri_score, diversity_score = calculate_gri_for_dimension(
                standardized_survey, benchmark_df, dimension, config
            )
            
            result_row = {
                'dimension': dimension['name'],
                'gri_score': gri_score,
                'diversity_score': diversity_score,
                'dimension_columns': columns,
                'sample_size': sample_size,
                'description': dimension.get('description', '')
            }
            
            # Calculate max possible scores if requested
            if include_max_possible:
                # Prepare benchmark for this specific dimension
                agg_benchmark = aggregate_benchmark_for_dimension(benchmark_df, columns, config)
                
                # Run Monte Carlo simulation
                max_results = monte_carlo_max_scores(
                    agg_benchmark,
                    sample_size,
                    columns,
                    n_simulations,
                    random_seed
                )
                
                # Add max scores to results
                result_row['max_possible_score'] = max_results['max_gri']['mean']
                result_row['max_possible_diversity'] = max_results['max_diversity']['mean']
                result_row['efficiency_ratio'] = gri_score / max_results['max_gri']['mean'] if max_results['max_gri']['mean'] > 0 else 0
                result_row['diversity_efficiency'] = diversity_score / max_results['max_diversity']['mean'] if max_results['max_diversity']['mean'] > 0 else 0
            
            results.append(result_row)
            
        except Exception as e:
            print(f"Warning: Failed to calculate scores for dimension '{dimension['name']}': {str(e)}")
            continue
    
    scorecard_df = pd.DataFrame(results)
    
    # No need to add average row - let calling code handle that if needed
    return scorecard_df