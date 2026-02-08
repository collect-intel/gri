#!/usr/bin/env python3
"""
Analyze demographic variance across all poll questions in GD1-GD3.

This script calculates within-stratum variance for all demographic dimensions
to understand which groups have more/less internal consensus on various topics.
"""

import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


def load_config_files(base_path: Path) -> Tuple[Dict, Dict, Dict]:
    """Load configuration files for dimensions, segments, and regions."""
    with open(base_path / 'config' / 'dimensions.yaml', 'r') as f:
        dimensions = yaml.safe_load(f)
    
    with open(base_path / 'config' / 'segments.yaml', 'r') as f:
        segments = yaml.safe_load(f)
    
    with open(base_path / 'config' / 'regions.yaml', 'r') as f:
        regions = yaml.safe_load(f)
    
    return dimensions, segments, regions


def load_gd_data(gd_num: int, data_path: Path) -> pd.DataFrame:
    """Load participant data for a specific GD survey."""
    file_path = data_path / f'GD{gd_num}' / f'GD{gd_num}_participants.csv'
    
    if not file_path.exists():
        print(f"Warning: {file_path} not found, skipping GD{gd_num}")
        return None
    
    df = pd.read_csv(file_path)
    print(f"Loaded GD{gd_num}: {len(df)} participants")
    return df


def get_poll_columns(df: pd.DataFrame) -> List[str]:
    """Identify poll question columns (exclude demographics and open-text)."""
    # Common demographic columns to exclude (exact names from GD data)
    demo_cols = [
        'Participant Id', 'Sample Provider Id',
        'How old are you?', 'What is your gender?', 
        'What best describes where you live?',
        'What religious group or faith do you most identify with?',
        'What country or region do you most identify with?',
        'Please select your preferred language:',
        'Muted', 'Categories', 'Sentiment'
    ]
    
    # Also exclude columns that contain these patterns
    exclude_patterns = ['(English)', '(Original)', '(%agree)']
    
    # Identify poll columns (non-demographic, non-text columns)
    poll_cols = []
    for col in df.columns:
        # Skip if it's a known demographic column
        if col in demo_cols:
            continue
            
        # Skip if it contains exclude patterns
        if any(pattern in col for pattern in exclude_patterns):
            continue
            
        # Skip empty column names
        if col == '' or pd.isna(col):
            continue
            
        # Check if column has reasonable number of unique values (not free text)
        unique_count = df[col].nunique()
        if 2 <= unique_count <= 20:  # Typical for Likert scales, multiple choice
            poll_cols.append(col)
    
    return poll_cols


def standardize_responses(series: pd.Series) -> pd.Series:
    """Convert categorical responses to numeric scale (0-1)."""
    if series.dtype == 'object':
        # Common response patterns
        mappings = {
            # 5-point scales
            'Strongly Disagree': 0, 'Disagree': 0.25, 'Neutral': 0.5, 
            'Agree': 0.75, 'Strongly Agree': 1,
            
            'Strongly Distrust': 0, 'Somewhat Distrust': 0.25,
            'Neither Trust Nor Distrust': 0.5, 'Somewhat Trust': 0.75, 'Strongly Trust': 1,
            
            'Profoundly Worse': 0, 'Noticeably Worse': 0.25,
            'No Major Change': 0.5, 'Noticeably Better': 0.75, 'Profoundly Better': 1,
            
            'Risks far outweigh benefits': 0, 'Risks slightly outweigh benefits': 0.25,
            'Risks and benefits are equal': 0.5, 'Benefits slightly outweigh risks': 0.75,
            'Benefits far outweigh risks': 1,
            
            # Frequency scales
            'never': 0, 'annually': 0.25, 'monthly': 0.5, 'weekly': 0.75, 'daily': 1,
            'Never': 0, 'Rarely': 0.25, 'Sometimes': 0.5, 'Often': 0.75, 'Always': 1,
            
            # Binary/ternary
            'No': 0, 'Yes': 1, "Don't Know": 0.5, 'Unsure': 0.5,
            'Disagree': 0, 'Agree': 1,
            
            # 3-point scales
            'More concerned than excited': 0, 'Equally concerned and excited': 0.5,
            'More excited than concerned': 1,
        }
        
        # Try to map values
        mapped = series.map(mappings)
        
        # If many values couldn't be mapped, create ordinal encoding
        if mapped.isna().sum() > len(series) * 0.5:
            unique_vals = series.dropna().unique()
            if len(unique_vals) <= 10 and len(unique_vals) > 1:  # Reasonable number for ordinal
                val_map = {val: i/(len(unique_vals)-1) for i, val in enumerate(sorted(unique_vals))}
                mapped = series.map(val_map)
            elif len(unique_vals) == 1:
                # All values are the same
                mapped = pd.Series([0.5] * len(series), index=series.index)
        
        return mapped
    
    # Already numeric - normalize to 0-1
    if series.min() >= 0 and series.max() <= 1:
        return series
    else:
        return (series - series.min()) / (series.max() - series.min())


def standardize_demographic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize demographic column names for consistency."""
    # Map GD column names to standard names
    column_mapping = {
        'How old are you?': 'age_group',
        'What is your gender?': 'gender',
        'What best describes where you live?': 'environment',
        'What religious group or faith do you most identify with?': 'religion',
        'What country or region do you most identify with?': 'country',
        'Participant Id': 'participant_id'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Standardize environment values (Suburban -> Urban for simplicity)
    if 'environment' in df.columns:
        df['environment'] = df['environment'].replace({'Suburban': 'Urban'})
    
    return df


def add_region_mapping(df: pd.DataFrame, regions: Dict) -> pd.DataFrame:
    """Add region and continent columns based on country."""
    # Create country to region mapping
    country_to_region_map = {}
    for region, countries in regions['country_to_region'].items():
        for country in countries:
            country_to_region_map[country] = region
    
    # Create region to continent mapping
    region_to_continent_map = {}
    for continent, region_list in regions['region_to_continent'].items():
        for region in region_list:
            region_to_continent_map[region] = continent
    
    # Apply mappings
    if 'country' in df.columns:
        df['region'] = df['country'].map(country_to_region_map)
        df['continent'] = df['region'].map(region_to_continent_map)
    
    return df


def calculate_stratum_variance(
    df: pd.DataFrame, 
    stratum_cols: List[str], 
    poll_cols: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate variance for each stratum across all poll questions.
    
    Returns:
        Dict mapping stratum_value -> {question -> variance}
    """
    # Create composite stratum column
    if len(stratum_cols) == 1:
        df['stratum'] = df[stratum_cols[0]]
    else:
        df['stratum'] = df[stratum_cols].apply(lambda x: ' × '.join(x.dropna().astype(str)), axis=1)
    
    stratum_variances = {}
    
    for stratum in df['stratum'].unique():
        if pd.isna(stratum) or stratum == '':
            continue
            
        stratum_data = df[df['stratum'] == stratum]
        
        if len(stratum_data) < 2:  # Need at least 2 responses
            continue
        
        question_variances = {}
        
        for col in poll_cols:
            if col in stratum_data.columns:
                # Standardize responses to 0-1 scale
                values = standardize_responses(stratum_data[col]).dropna()
                
                if len(values) >= 2:
                    variance = values.var()
                    question_variances[col] = variance
        
        if question_variances:
            stratum_variances[stratum] = question_variances
    
    return stratum_variances


def aggregate_variance_metrics(
    stratum_variances: Dict[str, Dict[str, float]]
) -> pd.DataFrame:
    """
    Aggregate variance data into summary metrics for each stratum.
    """
    summary_data = []
    
    for stratum, question_vars in stratum_variances.items():
        if not question_vars:
            continue
            
        variances = list(question_vars.values())
        
        summary_data.append({
            'stratum': stratum,
            'n_questions': len(variances),
            'mean_variance': np.mean(variances),
            'median_variance': np.median(variances),
            'std_variance': np.std(variances),
            'min_variance': np.min(variances),
            'max_variance': np.max(variances),
            'consensus_score': 1 - np.mean(variances)  # Higher = more consensus
        })
    
    return pd.DataFrame(summary_data)


def analyze_all_dimensions(
    df: pd.DataFrame,
    dimensions: Dict,
    poll_cols: List[str]
) -> Dict[str, pd.DataFrame]:
    """Analyze variance for all configured dimensions."""
    results = {}
    
    # Analyze standard scorecard dimensions
    for dim in dimensions['standard_scorecard']:
        print(f"  Analyzing dimension: {dim['name']}")
        
        # Check if all required columns exist
        required_cols = dim['columns']
        if all(col in df.columns for col in required_cols):
            variances = calculate_stratum_variance(df, required_cols, poll_cols)
            summary = aggregate_variance_metrics(variances)
            
            if not summary.empty:
                summary['dimension'] = dim['name']
                results[dim['name']] = summary
        else:
            print(f"    Warning: Missing columns for {dim['name']}")
    
    return results


def main():
    """Main analysis function."""
    base_path = Path(__file__).parent.parent
    data_path = base_path / 'data' / 'raw' / 'survey_data' / 'global-dialogues' / 'Data'
    output_path = base_path / 'analysis_output' / 'demographic_variance'
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading configuration files...")
    dimensions, segments, regions = load_config_files(base_path)
    
    # Analyze GD1-GD3
    all_results = {}
    
    for gd_num in [1, 2, 3]:
        print(f"\nAnalyzing GD{gd_num}...")
        df = load_gd_data(gd_num, data_path)
        
        if df is None:
            continue
        
        # Standardize demographic columns
        df = standardize_demographic_columns(df)
        
        # Add region/continent mappings
        df = add_region_mapping(df, regions)
        
        # Get poll columns
        poll_cols = get_poll_columns(df)
        print(f"  Found {len(poll_cols)} poll questions")
        
        # Analyze all dimensions
        gd_results = analyze_all_dimensions(df, dimensions, poll_cols)
        all_results[f'GD{gd_num}'] = gd_results
        
        # Save detailed results
        for dim_name, summary_df in gd_results.items():
            safe_name = dim_name.replace(' × ', '_x_').replace(' ', '_')
            summary_df.to_csv(
                output_path / f'GD{gd_num}_{safe_name}_variance.csv',
                index=False
            )
    
    # Create cross-GD comparison
    print("\nCreating cross-GD comparison...")
    comparison_data = []
    
    for gd, gd_results in all_results.items():
        for dim_name, summary_df in gd_results.items():
            if not summary_df.empty:
                avg_consensus = summary_df['consensus_score'].mean()
                comparison_data.append({
                    'survey': gd,
                    'dimension': dim_name,
                    'n_strata': len(summary_df),
                    'avg_consensus_score': avg_consensus,
                    'min_consensus': summary_df['consensus_score'].min(),
                    'max_consensus': summary_df['consensus_score'].max(),
                    'std_consensus': summary_df['consensus_score'].std()
                })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv(output_path / 'cross_gd_variance_comparison.csv', index=False)
    
    # Create variance lookup table for optimal allocation
    print("\nCreating variance lookup tables...")
    
    for gd, gd_results in all_results.items():
        variance_lookup = {}
        
        for dim_name, summary_df in gd_results.items():
            if not summary_df.empty:
                # Use mean variance as the within-stratum variance estimate
                stratum_variances = dict(zip(
                    summary_df['stratum'],
                    summary_df['mean_variance']
                ))
                variance_lookup[dim_name] = stratum_variances
        
        # Save as JSON for easy loading
        with open(output_path / f'{gd}_variance_lookup.json', 'w') as f:
            json.dump(variance_lookup, f, indent=2)
    
    print("\nAnalysis complete! Results saved to:", output_path)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("=" * 60)
    
    if not comparison_df.empty:
        print("\nAverage Consensus Scores by Dimension:")
        dim_avg = comparison_df.groupby('dimension')['avg_consensus_score'].mean().sort_values(ascending=False)
        for dim, score in dim_avg.items():
            print(f"  {dim}: {score:.3f}")
        
        print("\nMost Variable Dimensions (lowest consensus):")
        most_variable = comparison_df.nsmallest(5, 'avg_consensus_score')[['survey', 'dimension', 'avg_consensus_score']]
        print(most_variable.to_string(index=False))
        
        print("\nMost Consistent Dimensions (highest consensus):")
        most_consistent = comparison_df.nlargest(5, 'avg_consensus_score')[['survey', 'dimension', 'avg_consensus_score']]
        print(most_consistent.to_string(index=False))


if __name__ == "__main__":
    main()