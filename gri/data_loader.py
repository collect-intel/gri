"""
Data loading utilities for the Global Representativeness Index.

This module provides unified functions for loading benchmark data, survey data,
and applying configuration-based mappings.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union, List, Tuple
import yaml
import warnings
import logging

from .config import GRIConfig
from .utils import load_data

# Set up logger
logger = logging.getLogger(__name__)


def load_benchmark_suite(
    data_dir: Union[str, Path] = "data/processed",
    dimensions: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Load all benchmark data files at once.
    
    Parameters
    ----------
    data_dir : str or Path, default="data/processed"
        Directory containing processed benchmark CSV files
    dimensions : list of str, optional
        Specific dimensions to load. If None, loads all available benchmarks.
        
    Returns
    -------
    dict
        Dictionary mapping dimension names to benchmark DataFrames
        
    Examples
    --------
    >>> benchmarks = load_benchmark_suite()
    >>> print(benchmarks.keys())
    dict_keys(['Country × Gender × Age', 'Country × Religion', ...])
    
    >>> # Load only specific dimensions
    >>> benchmarks = load_benchmark_suite(dimensions=['Country', 'Gender'])
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise ValueError(f"Data directory not found: {data_dir}")
    
    # Map file names to dimension names
    file_mapping = {
        'benchmark_country_gender_age.csv': 'Country × Gender × Age',
        'benchmark_country_religion.csv': 'Country × Religion',
        'benchmark_country_environment.csv': 'Country × Environment',
        'benchmark_country.csv': 'Country',
        'benchmark_region_gender_age.csv': 'Region × Gender × Age',
        'benchmark_region_religion.csv': 'Region × Religion',
        'benchmark_region_environment.csv': 'Region × Environment',
        'benchmark_region.csv': 'Region',
        'benchmark_continent.csv': 'Continent',
        'benchmark_religion.csv': 'Religion',
        'benchmark_environment.csv': 'Environment',
        'benchmark_age_group.csv': 'Age Group',
        'benchmark_gender.csv': 'Gender'
    }
    
    benchmarks = {}
    
    for filename, dimension_name in file_mapping.items():
        # Skip if specific dimensions requested and this isn't one
        if dimensions and dimension_name not in dimensions:
            continue
            
        filepath = data_path / filename
        if filepath.exists():
            try:
                df = load_data(str(filepath))
                benchmarks[dimension_name] = df
            except Exception as e:
                warnings.warn(f"Could not load {filename}: {e}")
    
    if not benchmarks:
        raise ValueError("No benchmark files could be loaded")
    
    return benchmarks


def load_gd_survey(
    filepath: Union[str, Path],
    gd_version: Optional[int] = None,
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """
    Load Global Dialogues survey data with format handling.
    
    Handles various GD format quirks including malformed CSV headers,
    different column structures across versions, and applies segment mappings.
    
    Parameters
    ----------
    filepath : str or Path
        Path to GD participants CSV file
    gd_version : int, optional
        GD version number (1-4). If None, attempts to detect from filename.
    config : GRIConfig, optional
        Configuration object. If None, loads from default location.
        
    Returns
    -------
    pd.DataFrame
        Processed survey data with standardized column names
        
    Examples
    --------
    >>> survey = load_gd_survey('data/GD3_participants.csv')
    >>> print(survey.columns)
    Index(['participant_id', 'age_group', 'gender', 'country', 'religion', 
           'environment', 'region', 'continent'], dtype='object')
    """
    filepath = Path(filepath)
    
    # Try to detect GD version from filename
    if gd_version is None:
        if 'GD' in filepath.name:
            try:
                gd_version = int(filepath.name.split('GD')[1][0])
            except:
                pass
    
    # Load configuration if not provided
    if config is None:
        config = GRIConfig()
    
    # Read the CSV with different strategies
    try:
        # First try normal reading
        df = pd.read_csv(filepath, encoding='utf-8')
        
        # Check for malformed single-column format (GD4 issue)
        if df.shape[1] == 1 and ('Unnamed' in df.columns[0] or df.columns[0] == ''):
            # Skip first row and try again
            df = pd.read_csv(filepath, encoding='utf-8', skiprows=1)
            
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")
    
    # Apply GD-specific processing
    if gd_version == 4:
        df = _process_gd4_format(df)
    else:
        df = _process_standard_gd_format(df)
    
    # Apply segment mappings
    df = apply_segment_mappings(df, config)
    
    # Add geographic hierarchies
    df = _add_geographic_hierarchies(df, config)
    
    # Remove invalid rows
    df = df.dropna(subset=['country', 'gender', 'age_group'])
    
    return df


def _process_standard_gd_format(df: pd.DataFrame) -> pd.DataFrame:
    """Process standard GD1-3 format."""
    # Standard column positions for GD1-3
    column_mapping = {
        2: 'participant_id',
        5: 'age_group',
        6: 'gender',
        7: 'environment',
        9: 'religion',
        10: 'country'
    }
    
    # Skip header row and extract data
    if len(df) > 1:
        data_rows = df.iloc[1:].copy()
        
        # Extract columns by position
        processed = pd.DataFrame()
        for pos, col_name in column_mapping.items():
            if len(df.columns) > pos:
                processed[col_name] = data_rows.iloc[:, pos]
        
        # Clean up values
        for col in processed.columns:
            if col != 'participant_id':
                processed[col] = processed[col].astype(str).str.strip('"').str.strip()
                processed[col] = processed[col].replace(['', 'nan'], np.nan)
        
        return processed
    
    return pd.DataFrame()


def _process_gd4_format(df: pd.DataFrame) -> pd.DataFrame:
    """Process GD4 format which has different structure."""
    # GD4 specific processing if needed
    # This is a placeholder - implement based on actual GD4 format
    return _process_standard_gd_format(df)


def apply_segment_mappings(
    df: pd.DataFrame,
    config: Optional[GRIConfig] = None,
    survey_type: str = 'global_dialogues'
) -> pd.DataFrame:
    """
    Apply segment mappings from configuration to standardize categories.
    
    Parameters
    ----------
    df : pd.DataFrame
        Survey data with raw category values
    config : GRIConfig, optional
        Configuration object with segment mappings
    survey_type : str, default='global_dialogues'
        Type of survey for mapping selection
        
    Returns
    -------
    pd.DataFrame
        Data with standardized category values
    """
    if config is None:
        config = GRIConfig()
    
    df = df.copy()
    
    # Load segment mappings
    segments_path = Path(config.config_dir) / 'segments.yaml'
    with open(segments_path, 'r') as f:
        segments = yaml.safe_load(f)
    
    # Get mappings for this survey type
    survey_mappings = segments.get('survey_mappings', {}).get(survey_type, {})
    benchmark_mappings = segments.get('benchmark_mappings', {})
    
    # Apply mappings for each column
    for column in ['country', 'gender', 'age_group', 'religion', 'environment']:
        if column not in df.columns:
            continue
            
        # Build reverse mapping
        mapping_dict = {}
        
        # First check survey-specific mappings
        if column in survey_mappings:
            for standard_val, variations in survey_mappings[column].items():
                for variation in variations:
                    mapping_dict[variation] = standard_val
        
        # Then check benchmark mappings (for countries especially)
        if column in benchmark_mappings:
            for standard_val, variations in benchmark_mappings[column].items():
                for variation in variations:
                    mapping_dict[variation] = standard_val
        
        # Apply mapping
        if mapping_dict:
            df[column] = df[column].map(lambda x: mapping_dict.get(x, x))
    
    # Special handling for environment
    if 'environment' in df.columns:
        # Map suburban to urban
        df['environment'] = df['environment'].replace('Suburban', 'Urban')
    
    return df


def _add_geographic_hierarchies(
    df: pd.DataFrame,
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """Add region and continent columns based on country."""
    if 'country' not in df.columns:
        return df
        
    if config is None:
        config = GRIConfig()
    
    df = df.copy()
    
    # Get geographic mappings
    country_to_region = config.get_country_to_region_mapping()
    region_to_continent = config.get_region_to_continent_mapping()
    
    # Add region
    df['region'] = df['country'].map(country_to_region)
    
    # Add continent
    df['continent'] = df['region'].map(region_to_continent)
    
    return df


def load_wvs_survey(
    filepath: Union[str, Path],
    wave: Optional[int] = None,
    config: Optional[GRIConfig] = None
) -> pd.DataFrame:
    """
    Load World Values Survey data.
    
    Parameters
    ----------
    filepath : str or Path
        Path to WVS data file
    wave : int, optional
        WVS wave number (6 or 7). If None, attempts to detect from filename.
    config : GRIConfig, optional
        Configuration object
        
    Returns
    -------
    pd.DataFrame
        Processed WVS data with standardized columns
        
    Notes
    -----
    WVS uses numeric codes for many variables which need to be mapped
    to text values for GRI analysis.
    """
    filepath = Path(filepath)
    
    # Try to detect wave from filename if not provided
    if wave is None:
        if 'wave7' in str(filepath).lower() or 'wave_7' in str(filepath).lower():
            wave = 7
        elif 'wave6' in str(filepath).lower() or 'wave_6' in str(filepath).lower():
            wave = 6
        else:
            raise ValueError("Could not detect WVS wave from filename. Please specify wave parameter.")
    
    # Check if this is already processed data
    if 'processed' in str(filepath) or 'wvs_wave' in str(filepath):
        # Already in standard format
        df = pd.read_csv(filepath)
        logger.info(f"Loaded processed WVS Wave {wave} data: {len(df)} responses")
        
        # Apply standard segment mappings if config provided
        if config:
            df = apply_segment_mappings(df, config, survey_type='world_values_survey')
        
        return df
    
    # For raw WVS data, provide helpful error
    logger.error("Raw WVS data processing not available in module")
    raise NotImplementedError(
        "Raw WVS data requires preprocessing. Please either:\n"
        "1. Use pre-processed files from data/processed/surveys/wvs/\n"
        "2. Run: python scripts/process_wvs_survey.py"
    )


def validate_survey_data(
    survey_df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that survey data has required columns and valid values.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data to validate
    required_columns : list of str, optional
        Columns that must be present. Defaults to core demographic columns.
        
    Returns
    -------
    valid : bool
        Whether data passes validation
    issues : list of str
        List of validation issues found
    """
    if required_columns is None:
        required_columns = ['country', 'gender', 'age_group']
    
    issues = []
    
    # Check required columns
    missing_cols = set(required_columns) - set(survey_df.columns)
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
    
    # Check for empty dataframe
    if len(survey_df) == 0:
        issues.append("DataFrame is empty")
    
    # Check for excessive missing values
    for col in required_columns:
        if col in survey_df.columns:
            missing_pct = survey_df[col].isna().sum() / len(survey_df) * 100
            if missing_pct > 50:
                issues.append(f"{col} has {missing_pct:.1f}% missing values")
    
    return len(issues) == 0, issues