#!/usr/bin/env python3
"""
Configuration-Driven Data Processing Script for GRI

This script processes raw benchmark data according to the dimensions defined in 
config/dimensions.yaml, creating all necessary benchmark files for the complete
GRI scorecard.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.config import GRIConfig
from gri.utils import aggregate_data

# Import the original processing functions
from scripts.process_data import (
    load_raw_data,
    process_country_gender_age,
    process_country_religion,
    process_country_environment
)


def create_regional_benchmark(country_benchmark: pd.DataFrame, config: GRIConfig,
                            columns: list, target_geo_level: str) -> pd.DataFrame:
    """
    Create regional or continental benchmark by aggregating country data.
    
    Args:
        country_benchmark: Country-level benchmark data
        config: GRI configuration
        columns: Target columns for the benchmark
        target_geo_level: 'region' or 'continent'
        
    Returns:
        Aggregated benchmark DataFrame
    """
    if target_geo_level not in ['region', 'continent']:
        raise ValueError("target_geo_level must be 'region' or 'continent'")
    
    # Get geographic mappings
    if target_geo_level == 'region':
        geo_mapping = config.get_country_to_region_mapping()
    else:  # continent
        geo_mapping = config.get_country_to_continent_mapping()
    
    # Add geographic column to benchmark data
    country_benchmark_with_geo = country_benchmark.copy()
    country_benchmark_with_geo[target_geo_level] = country_benchmark_with_geo['country'].map(geo_mapping)
    
    # Filter out countries not in mapping
    country_benchmark_with_geo = country_benchmark_with_geo.dropna(subset=[target_geo_level])
    
    # Create grouping columns (replace 'country' with target geographic level)
    group_columns = [col if col != 'country' else target_geo_level for col in columns]
    
    # Aggregate by the new geographic level
    aggregated = country_benchmark_with_geo.groupby(group_columns)['population_proportion'].sum().reset_index()
    
    return aggregated


def create_single_dimension_benchmark(base_benchmark: pd.DataFrame, 
                                    target_column: str) -> pd.DataFrame:
    """
    Create single-dimension benchmark by aggregating across other dimensions.
    
    Args:
        base_benchmark: Multi-dimensional benchmark data
        target_column: The single column to keep
        
    Returns:
        Single-dimension benchmark DataFrame
    """
    if target_column not in base_benchmark.columns:
        raise ValueError(f"Column '{target_column}' not found in benchmark data")
    
    # Aggregate by the target column only
    single_dim = base_benchmark.groupby(target_column)['population_proportion'].sum().reset_index()
    
    return single_dim


def process_all_configured_benchmarks(config: GRIConfig) -> dict:
    """
    Process all benchmark files according to the dimensions configuration.
    
    Args:
        config: GRI configuration object
        
    Returns:
        Dictionary mapping dimension names to processed benchmark DataFrames
    """
    print("Loading raw benchmark data...")
    raw_data = load_raw_data()
    
    print("Processing base benchmark data...")
    
    # Create the three foundational benchmarks (these are always needed)
    base_benchmarks = {
        'country_gender_age': process_country_gender_age(raw_data['male_pop'], raw_data['female_pop']),
        'country_religion': process_country_religion(raw_data['religion']),
        'country_environment': process_country_environment(raw_data['urban_rural'])
    }
    
    print(f"  ✓ Country × Gender × Age: {len(base_benchmarks['country_gender_age'])} strata")
    print(f"  ✓ Country × Religion: {len(base_benchmarks['country_religion'])} strata")
    print(f"  ✓ Country × Environment: {len(base_benchmarks['country_environment'])} strata")
    
    # Get all dimensions from configuration
    all_dimensions = config.get_all_dimensions()
    processed_benchmarks = {}
    
    print("\\nProcessing configured dimensions...")
    
    for dimension in all_dimensions:
        dim_name = dimension['name']
        dim_columns = dimension['columns']
        
        print(f"  Processing: {dim_name}")
        
        try:
            benchmark_df = None
            
            # Determine processing approach based on dimension structure
            if 'region' in dim_columns:
                # Choose appropriate base data for regional dimensions
                if 'religion' in dim_columns:
                    base_data = base_benchmarks['country_religion']
                elif 'environment' in dim_columns:
                    base_data = base_benchmarks['country_environment']
                else:
                    base_data = base_benchmarks['country_gender_age']
                    
                # Create regional benchmark
                benchmark_df = create_regional_benchmark(base_data, config, dim_columns, 'region')
                
            elif 'continent' in dim_columns:
                # Use country_gender_age as base for continental aggregation
                base_data = base_benchmarks['country_gender_age']
                benchmark_df = create_regional_benchmark(base_data, config, dim_columns, 'continent')
                
            elif len(dim_columns) == 1:
                # Single dimension - need to choose appropriate base and aggregate
                single_col = dim_columns[0]
                if single_col == 'religion':
                    base_data = base_benchmarks['country_religion']
                elif single_col == 'environment':
                    base_data = base_benchmarks['country_environment']
                else:
                    base_data = base_benchmarks['country_gender_age']
                
                benchmark_df = create_single_dimension_benchmark(base_data, single_col)
                
            elif set(dim_columns) == {'country', 'gender', 'age_group'}:
                benchmark_df = base_benchmarks['country_gender_age']
                
            elif set(dim_columns) == {'country', 'religion'}:
                benchmark_df = base_benchmarks['country_religion']
                
            elif set(dim_columns) == {'country', 'environment'}:
                benchmark_df = base_benchmarks['country_environment']
                
            elif set(dim_columns) == {'country'}:
                # Aggregate country-level data from country_gender_age
                benchmark_df = create_single_dimension_benchmark(base_benchmarks['country_gender_age'], 'country')
                
            else:
                print(f"    ⚠️  Skipping: Unsupported dimension combination {dim_columns}")
                continue
            
            if benchmark_df is None:
                print(f"    ❌ Failed to create benchmark for {dim_name}")
                continue
            
            # Verify proportions sum to approximately 1.0
            prop_sum = benchmark_df['population_proportion'].sum()
            if abs(prop_sum - 1.0) > 0.01:
                print(f"    ⚠️  Warning: Proportions sum to {prop_sum:.4f}, expected ~1.0")
            
            processed_benchmarks[dim_name] = benchmark_df
            print(f"    ✓ Created benchmark with {len(benchmark_df)} strata (sum={prop_sum:.4f})")
            
        except Exception as e:
            print(f"    ❌ Error processing {dim_name}: {e}")
            continue
    
    return processed_benchmarks


def save_processed_benchmarks(benchmarks: dict, output_dir: str = "data/processed"):
    """
    Save all processed benchmarks to files.
    
    Args:
        benchmarks: Dictionary of dimension name -> benchmark DataFrame
        output_dir: Output directory for files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\\nSaving {len(benchmarks)} benchmark files to {output_dir}/...")
    
    # Save the core benchmarks with original names for backwards compatibility
    core_mappings = {
        'Country × Gender × Age': 'benchmark_country_gender_age.csv',
        'Country × Religion': 'benchmark_country_religion.csv', 
        'Country × Environment': 'benchmark_country_environment.csv'
    }
    
    # Save all benchmarks
    for dim_name, benchmark_df in benchmarks.items():
        # Use core mapping if available, otherwise create filename from dimension name
        if dim_name in core_mappings:
            filename = core_mappings[dim_name]
        else:
            # Create safe filename from dimension name
            safe_name = dim_name.lower().replace(' × ', '_').replace(' ', '_').replace('×', '')
            filename = f"benchmark_{safe_name}.csv"
        
        filepath = os.path.join(output_dir, filename)
        benchmark_df.to_csv(filepath, index=False)
        
        prop_sum = benchmark_df['population_proportion'].sum()
        print(f"  ✓ {filename}: {len(benchmark_df)} strata (sum={prop_sum:.4f})")


def validate_configuration_coverage(config: GRIConfig, benchmarks: dict):
    """
    Validate that all configured dimensions have corresponding benchmarks.
    
    Args:
        config: GRI configuration
        benchmarks: Processed benchmarks dictionary
    """
    print("\\nValidating configuration coverage...")
    
    all_dimensions = config.get_all_dimensions()
    configured_names = {dim['name'] for dim in all_dimensions}
    processed_names = set(benchmarks.keys())
    
    missing = configured_names - processed_names
    extra = processed_names - configured_names
    
    if missing:
        print(f"  ⚠️  Missing benchmarks for: {missing}")
    
    if extra:
        print(f"  ℹ️  Extra benchmarks created: {extra}")
    
    coverage_pct = len(processed_names & configured_names) / len(configured_names) * 100
    print(f"  📊 Configuration coverage: {coverage_pct:.1f}% ({len(processed_names & configured_names)}/{len(configured_names)} dimensions)")
    
    return coverage_pct >= 80  # At least 80% coverage required


def main():
    """Main processing function."""
    print("Configuration-Driven GRI Data Processing")
    print("=" * 50)
    
    # Load configuration
    try:
        config = GRIConfig()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False
    
    # Process all configured benchmarks
    try:
        benchmarks = process_all_configured_benchmarks(config)
        print(f"\\n✓ Processed {len(benchmarks)} benchmark dimensions")
    except Exception as e:
        print(f"❌ Error processing benchmarks: {e}")
        return False
    
    # Save benchmarks
    try:
        save_processed_benchmarks(benchmarks)
        print("✓ All benchmarks saved successfully")
    except Exception as e:
        print(f"❌ Error saving benchmarks: {e}")
        return False
    
    # Validate coverage
    if validate_configuration_coverage(config, benchmarks):
        print("✓ Configuration coverage validation passed")
    else:
        print("⚠️  Configuration coverage validation failed")
    
    print("\\n" + "=" * 50)
    print("Configuration-driven processing complete!")
    print(f"Created {len(benchmarks)} benchmark files according to dimensions.yaml")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)