"""
Configuration and Data Validation Module

This module provides validation functions for GRI configuration files and survey data
to ensure data quality and catch configuration errors early.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import yaml
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_survey_data(df: pd.DataFrame, required_columns: List[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate survey data format and quality.
    
    Args:
        df: Survey data DataFrame
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check basic DataFrame properties
    if df.empty:
        issues.append("Survey data is empty")
        return False, issues
    
    # Check required columns
    if required_columns:
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
    
    # Check for completely null columns
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        issues.append(f"Columns with all null values: {null_columns}")
    
    # Check data types
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check for mixed types in string columns
            non_string_mask = ~df[col].astype(str).str.match(r'^[a-zA-Z0-9\s\-_.,()]+$', na=False)
            if non_string_mask.any():
                issues.append(f"Column '{col}' contains unusual characters")
    
    # Check for reasonable data ranges
    for col in df.columns:
        if 'age' in col.lower():
            # Check age values are reasonable
            numeric_ages = pd.to_numeric(df[col], errors='coerce')
            if numeric_ages.notna().any():
                if (numeric_ages < 0).any() or (numeric_ages > 120).any():
                    issues.append(f"Column '{col}' contains unrealistic age values")
    
    # Check for data completeness
    for col in df.columns:
        null_pct = df[col].isnull().sum() / len(df) * 100
        if null_pct > 50:
            issues.append(f"Column '{col}' has {null_pct:.1f}% missing values")
        elif null_pct > 20:
            issues.append(f"Warning: Column '{col}' has {null_pct:.1f}% missing values")
    
    # Check for suspicious duplicates
    if len(df) > 1:
        duplicate_rows = df.duplicated().sum()
        if duplicate_rows > len(df) * 0.1:  # More than 10% duplicates
            issues.append(f"High number of duplicate rows: {duplicate_rows} ({duplicate_rows/len(df)*100:.1f}%)")
    
    is_valid = len([issue for issue in issues if not issue.startswith("Warning:")]) == 0
    
    return is_valid, issues


def validate_benchmark_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate benchmark data format and completeness.
    
    Args:
        df: Benchmark data DataFrame
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required column
    if 'population_proportion' not in df.columns:
        issues.append("Missing required 'population_proportion' column")
        return False, issues
    
    # Check population proportions sum to approximately 1
    prop_sum = df['population_proportion'].sum()
    if abs(prop_sum - 1.0) > 0.01:  # Allow 1% tolerance
        issues.append(f"Population proportions sum to {prop_sum:.4f}, expected ~1.0")
    
    # Check for negative proportions
    if (df['population_proportion'] < 0).any():
        issues.append("Found negative population proportions")
    
    # Check for NaN proportions
    if df['population_proportion'].isnull().any():
        issues.append("Found null population proportions")
    
    # Check for unreasonably large proportions
    if (df['population_proportion'] > 0.5).any():
        large_props = df[df['population_proportion'] > 0.5]['population_proportion'].tolist()
        issues.append(f"Found unusually large proportions (>50%): {large_props}")
    
    # Check for reasonable number of strata
    if len(df) < 2:
        issues.append("Benchmark data has fewer than 2 strata")
    elif len(df) > 10000:
        issues.append(f"Benchmark data has many strata ({len(df)}), may impact performance")
    
    is_valid = len([issue for issue in issues if not issue.startswith("Warning:")]) == 0
    
    return is_valid, issues


def validate_yaml_config(config_path: str) -> Tuple[bool, List[str]]:
    """
    Validate YAML configuration file structure and content.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        issues.append(f"Configuration file not found: {config_path}")
        return False, issues
    except yaml.YAMLError as e:
        issues.append(f"Invalid YAML syntax: {e}")
        return False, issues
    
    # Validate based on file type
    config_name = Path(config_path).stem
    
    if config_name == 'dimensions':
        return validate_dimensions_config(config)
    elif config_name == 'segments':
        return validate_segments_config(config)
    elif config_name == 'regions':
        return validate_regions_config(config)
    else:
        issues.append(f"Unknown configuration file type: {config_name}")
        return False, issues


def validate_dimensions_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate dimensions configuration structure."""
    issues = []
    
    # Check required top-level keys
    required_keys = ['standard_scorecard', 'extended_dimensions']
    for key in required_keys:
        if key not in config:
            issues.append(f"Missing required key in dimensions config: {key}")
    
    # Validate standard scorecard
    if 'standard_scorecard' in config:
        scorecard = config['standard_scorecard']
        if not isinstance(scorecard, list):
            issues.append("standard_scorecard must be a list")
        else:
            for i, dimension in enumerate(scorecard):
                if not isinstance(dimension, list):
                    issues.append(f"Dimension {i} in standard_scorecard must be a list")
                elif len(dimension) == 0:
                    issues.append(f"Dimension {i} in standard_scorecard is empty")
    
    # Validate extended dimensions
    if 'extended_dimensions' in config:
        extended = config['extended_dimensions']
        if extended is not None:  # Allow None/null
            if not isinstance(extended, dict):
                issues.append("extended_dimensions must be a dictionary or null")
            else:
                for granularity, dims in extended.items():
                    if not isinstance(dims, list):
                        issues.append(f"Granularity '{granularity}' must contain a list of dimensions")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def validate_segments_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate segments configuration structure."""
    issues = []
    
    # Check for benchmark and survey mappings
    if 'benchmark_mappings' not in config:
        issues.append("Missing 'benchmark_mappings' in segments config")
    
    if 'survey_mappings' not in config:
        issues.append("Missing 'survey_mappings' in segments config")
    
    # Validate mapping structure
    for mapping_type in ['benchmark_mappings', 'survey_mappings']:
        if mapping_type in config:
            mappings = config[mapping_type]
            if not isinstance(mappings, dict):
                issues.append(f"{mapping_type} must be a dictionary")
                continue
                
            for source, mapping in mappings.items():
                if not isinstance(mapping, dict):
                    issues.append(f"Mapping for '{source}' in {mapping_type} must be a dictionary")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def validate_regions_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate regions configuration structure."""
    issues = []
    
    # Check required keys
    required_keys = ['country_to_region', 'region_to_continent']
    for key in required_keys:
        if key not in config:
            issues.append(f"Missing required key in regions config: {key}")
    
    # Validate country to region mapping
    if 'country_to_region' in config:
        country_mapping = config['country_to_region']
        if not isinstance(country_mapping, dict):
            issues.append("country_to_region must be a dictionary")
        else:
            # Check for reasonable number of countries per region
            for region, countries in country_mapping.items():
                if not isinstance(countries, list):
                    issues.append(f"Countries for region '{region}' must be a list")
                elif len(countries) == 0:
                    issues.append(f"Region '{region}' has no countries")
                elif len(countries) > 100:
                    issues.append(f"Region '{region}' has unusually many countries ({len(countries)})")
    
    # Validate region to continent mapping
    if 'region_to_continent' in config:
        continent_mapping = config['region_to_continent']
        if not isinstance(continent_mapping, dict):
            issues.append("region_to_continent must be a dictionary")
    
    is_valid = len(issues) == 0
    return is_valid, issues


def validate_gri_calculation_inputs(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, 
                                   strata_cols: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate inputs for GRI calculation.
    
    Args:
        survey_df: Survey data
        benchmark_df: Benchmark data  
        strata_cols: Strata column names
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Validate survey data
    survey_valid, survey_issues = validate_survey_data(survey_df, strata_cols)
    issues.extend([f"Survey: {issue}" for issue in survey_issues])
    
    # Validate benchmark data
    benchmark_valid, benchmark_issues = validate_benchmark_data(benchmark_df)
    issues.extend([f"Benchmark: {issue}" for issue in benchmark_issues])
    
    # Check strata columns exist in both datasets
    missing_survey_cols = set(strata_cols) - set(survey_df.columns)
    if missing_survey_cols:
        issues.append(f"Survey missing strata columns: {missing_survey_cols}")
    
    missing_benchmark_cols = set(strata_cols) - set(benchmark_df.columns)
    if missing_benchmark_cols:
        issues.append(f"Benchmark missing strata columns: {missing_benchmark_cols}")
    
    # Check for common strata between survey and benchmark
    if not missing_survey_cols and not missing_benchmark_cols:
        survey_strata = set(survey_df[strata_cols].apply(tuple, axis=1))
        benchmark_strata = set(benchmark_df[strata_cols].apply(tuple, axis=1))
        
        overlap = survey_strata & benchmark_strata
        if len(overlap) == 0:
            issues.append("No common strata found between survey and benchmark data")
        elif len(overlap) < len(survey_strata) * 0.1:  # Less than 10% overlap
            overlap_pct = len(overlap) / len(survey_strata) * 100
            issues.append(f"Low strata overlap: {overlap_pct:.1f}% of survey strata found in benchmark")
    
    is_valid = len([issue for issue in issues if not issue.startswith("Warning:")]) == 0
    
    return is_valid, issues


def run_comprehensive_validation(config_dir: str = "config", 
                                survey_file: str = None,
                                benchmark_files: List[str] = None) -> Dict[str, Any]:
    """
    Run comprehensive validation of GRI system components.
    
    Args:
        config_dir: Directory containing configuration files
        survey_file: Optional path to survey data for validation
        benchmark_files: Optional list of benchmark files to validate
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'overall_valid': True,
        'config_validation': {},
        'data_validation': {},
        'summary': []
    }
    
    # Validate configuration files
    config_files = ['dimensions.yaml', 'segments.yaml', 'regions.yaml']
    for config_file in config_files:
        config_path = Path(config_dir) / config_file
        if config_path.exists():
            is_valid, issues = validate_yaml_config(str(config_path))
            results['config_validation'][config_file] = {
                'valid': is_valid,
                'issues': issues
            }
            if not is_valid:
                results['overall_valid'] = False
                results['summary'].append(f"❌ {config_file}: {len(issues)} issues")
            else:
                results['summary'].append(f"✅ {config_file}: Valid")
        else:
            results['overall_valid'] = False
            results['summary'].append(f"❌ {config_file}: File not found")
    
    # Validate data files if provided
    if survey_file:
        try:
            from gri.utils import load_data
            survey_df = load_data(survey_file)
            is_valid, issues = validate_survey_data(survey_df)
            results['data_validation']['survey'] = {
                'valid': is_valid,
                'issues': issues,
                'rows': len(survey_df),
                'columns': len(survey_df.columns)
            }
            if not is_valid:
                results['overall_valid'] = False
                results['summary'].append(f"❌ Survey data: {len(issues)} issues")
            else:
                results['summary'].append(f"✅ Survey data: Valid ({len(survey_df):,} rows)")
        except Exception as e:
            results['overall_valid'] = False
            results['summary'].append(f"❌ Survey data: Failed to load ({e})")
    
    if benchmark_files:
        for benchmark_file in benchmark_files:
            try:
                from gri.utils import load_data
                benchmark_df = load_data(benchmark_file)
                is_valid, issues = validate_benchmark_data(benchmark_df)
                file_name = Path(benchmark_file).name
                results['data_validation'][file_name] = {
                    'valid': is_valid,
                    'issues': issues,
                    'rows': len(benchmark_df),
                    'proportion_sum': benchmark_df['population_proportion'].sum()
                }
                if not is_valid:
                    results['overall_valid'] = False
                    results['summary'].append(f"❌ {file_name}: {len(issues)} issues")
                else:
                    results['summary'].append(f"✅ {file_name}: Valid ({len(benchmark_df):,} strata)")
            except Exception as e:
                results['overall_valid'] = False
                results['summary'].append(f"❌ {Path(benchmark_file).name}: Failed to load ({e})")
    
    return results