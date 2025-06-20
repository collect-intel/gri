#!/usr/bin/env python3
"""
Calculate Variance-Weighted Representativeness Score (VWRS) for all dimensions.

This script:
1. Loads survey participant data and aggregate agreement rates
2. Calculates VWRS for all dimensions specified in config/dimensions.yaml
3. Uses agreement rates from Ask Opinion questions as the measure of consensus
4. Outputs results in the same format as traditional GRI calculations
"""

import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import sys
sys.path.append(str(Path(__file__).parent.parent))

from gri.variance_weighted import calculate_vwrs


def load_benchmark_proportions(dimension_name: str, dimension_cols: List[str]) -> Dict[str, float]:
    """
    Load population benchmark proportions for a given dimension.
    
    This is a placeholder - in production, this would load from the actual
    benchmark data files based on the dimension.
    """
    # Example proportions for demonstration
    # In reality, these would be calculated from UN/Pew benchmark data
    example_benchmarks = {
        'Country': {
            'China': 0.180, 'India': 0.175, 'United States': 0.042,
            'Indonesia': 0.035, 'Pakistan': 0.028, 'Brazil': 0.027,
            'Nigeria': 0.026, 'Bangladesh': 0.021, 'Russian Federation': 0.018,
            'Mexico': 0.016, 'Japan': 0.016, 'Ethiopia': 0.015,
            'Philippines': 0.014, 'Egypt': 0.013, 'Viet Nam': 0.012
        },
        'Gender': {
            'Male': 0.505, 'Female': 0.495
        },
        'Age Group': {
            '18-25': 0.18, '26-35': 0.22, '36-45': 0.20,
            '46-55': 0.17, '56-65': 0.13, '65+': 0.10
        },
        'Religion': {
            'Christianity': 0.31, 'Islam': 0.24, 'Hinduism': 0.15,
            'Buddhism': 0.07, 'I do not identify with any religious group or faith': 0.16,
            'Other religious group': 0.06, 'Judaism': 0.002
        },
        'Environment': {
            'Urban': 0.56, 'Rural': 0.44
        }
    }
    
    # For single dimensions, return directly
    if len(dimension_cols) == 1 and dimension_cols[0] in example_benchmarks:
        return example_benchmarks[dimension_cols[0]]
    
    # For composite dimensions, would need to calculate joint distribution
    # This is simplified for demonstration
    return {}


def calculate_agreement_variance(
    aggregate_df: pd.DataFrame,
    participant_df: pd.DataFrame,
    dimension_cols: List[str]
) -> Dict[str, float]:
    """
    Calculate variance in agreement rates for each stratum.
    
    Uses Ask Opinion questions' agreement rates as a measure of internal consensus.
    """
    # Filter to Ask Opinion questions only
    opinion_questions = aggregate_df[aggregate_df['Question Type'] == 'Ask Opinion']
    
    if opinion_questions.empty:
        print("Warning: No Ask Opinion questions found")
        return {}
    
    # Get unique questions
    unique_questions = opinion_questions['Question ID'].unique()
    
    # Create stratum identifier in participant data
    if len(dimension_cols) == 1:
        participant_df['stratum'] = participant_df[dimension_cols[0]]
    else:
        participant_df['stratum'] = participant_df[dimension_cols].apply(
            lambda x: ' × '.join(x.dropna().astype(str)), axis=1
        )
    
    # Calculate variance for each stratum
    stratum_variances = {}
    
    for stratum in participant_df['stratum'].unique():
        if pd.isna(stratum):
            continue
            
        # Get column name for this stratum's agreement rates
        # Column names in aggregate_df are like "O7: United States", "O3: Male", etc.
        stratum_col = None
        
        # Try to find matching column
        if len(dimension_cols) == 1:
            # Simple dimension - look for exact match
            for col in aggregate_df.columns:
                if col.endswith(f': {stratum}'):
                    stratum_col = col
                    break
        
        if stratum_col and stratum_col in opinion_questions.columns:
            # Get agreement rates for this stratum across all opinion questions
            agreement_rates = opinion_questions[stratum_col].str.rstrip('%').astype(float) / 100
            agreement_rates = agreement_rates.dropna()
            
            if len(agreement_rates) > 1:
                # Calculate variance of agreement rates
                # Low variance = high consensus within group
                variance = agreement_rates.var()
                stratum_variances[stratum] = variance
            else:
                # Default to moderate variance if insufficient data
                stratum_variances[stratum] = 0.25
        else:
            # No data for this stratum
            stratum_variances[stratum] = 0.25
    
    return stratum_variances


def standardize_participant_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize demographic column names."""
    column_mapping = {
        'How old are you?': 'age_group',
        'What is your gender?': 'gender',
        'What best describes where you live?': 'environment',
        'What religious group or faith do you most identify with?': 'religion',
        'What country or region do you most identify with?': 'country',
        'Participant Id': 'participant_id'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Standardize environment values
    if 'environment' in df.columns:
        df['environment'] = df['environment'].replace({'Suburban': 'Urban'})
    
    return df


def add_geographic_mappings(df: pd.DataFrame, regions_config: Dict) -> pd.DataFrame:
    """Add region and continent based on country."""
    # Create mappings
    country_to_region = {}
    for region, countries in regions_config['country_to_region'].items():
        for country in countries:
            country_to_region[country] = region
    
    region_to_continent = {}
    for continent, regions in regions_config['region_to_continent'].items():
        for region in regions:
            region_to_continent[region] = continent
    
    # Apply mappings
    if 'country' in df.columns:
        df['region'] = df['country'].map(country_to_region)
        df['continent'] = df['region'].map(region_to_continent)
    
    return df


def calculate_vwrs_all_dimensions(
    gd_num: int,
    base_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """Calculate VWRS for all configured dimensions."""
    
    # Load configuration
    with open(base_path / 'config' / 'dimensions.yaml', 'r') as f:
        dimensions_config = yaml.safe_load(f)
    
    with open(base_path / 'config' / 'regions.yaml', 'r') as f:
        regions_config = yaml.safe_load(f)
    
    # Load survey data
    participant_path = base_path / 'data' / 'raw' / 'survey_data' / 'global-dialogues' / 'Data' / f'GD{gd_num}' / f'GD{gd_num}_participants.csv'
    aggregate_path = base_path / 'data' / 'raw' / 'survey_data' / 'global-dialogues' / 'Data' / f'GD{gd_num}' / f'GD{gd_num}_aggregate_standardized.csv'
    
    if not participant_path.exists() or not aggregate_path.exists():
        print(f"Data files not found for GD{gd_num}")
        return {}
    
    # Load data
    participant_df = pd.read_csv(participant_path)
    aggregate_df = pd.read_csv(aggregate_path)
    
    # Standardize columns
    participant_df = standardize_participant_data(participant_df)
    participant_df = add_geographic_mappings(participant_df, regions_config)
    
    # Results storage
    results = {
        'survey': f'GD{gd_num}',
        'dimensions': {}
    }
    
    # Calculate for each dimension
    for dim in dimensions_config['standard_scorecard']:
        dim_name = dim['name']
        dim_cols = dim['columns']
        
        print(f"Calculating VWRS for {dim_name}...")
        
        # Check if required columns exist
        missing_cols = [col for col in dim_cols if col not in participant_df.columns]
        if missing_cols:
            print(f"  Skipping - missing columns: {missing_cols}")
            continue
        
        # Get benchmark proportions
        benchmark_props = load_benchmark_proportions(dim_name, dim_cols)
        if not benchmark_props:
            print(f"  Skipping - no benchmark data available")
            continue
        
        # Calculate sample proportions and counts
        if len(dim_cols) == 1:
            participant_df['stratum'] = participant_df[dim_cols[0]]
        else:
            participant_df['stratum'] = participant_df[dim_cols].apply(
                lambda x: ' × '.join(x.dropna().astype(str)), axis=1
            )
        
        sample_counts = participant_df['stratum'].value_counts()
        total_sample = len(participant_df)
        sample_props = (sample_counts / total_sample).to_dict()
        sample_sizes = sample_counts.to_dict()
        
        # Calculate agreement-based variance
        agreement_variances = calculate_agreement_variance(
            aggregate_df, participant_df, dim_cols
        )
        
        # Calculate traditional GRI
        traditional_gri = 0
        for stratum, pop_prop in benchmark_props.items():
            sample_prop = sample_props.get(stratum, 0)
            traditional_gri += 0.5 * abs(sample_prop - pop_prop)
        traditional_gri = 1 - traditional_gri
        
        # Calculate VWRS using agreement variance
        # Convert agreement variance to weight (high variance = low weight)
        variance_weights = {}
        for stratum in benchmark_props:
            # Use agreement variance if available, otherwise default
            var = agreement_variances.get(stratum, 0.25)
            # Convert to weight: low variance (high consensus) = high reliability
            variance_weights[stratum] = 1 - var
        
        # Modified VWRS calculation using agreement-based weights
        weighted_error = 0
        total_weight = 0
        
        for stratum, pop_prop in benchmark_props.items():
            sample_prop = sample_props.get(stratum, 0)
            n = sample_sizes.get(stratum, 0)
            
            # Standard error
            if n > 0:
                se = np.sqrt(sample_prop * (1 - sample_prop) / n)
            else:
                se = 0.5
            
            # Weight combines population size, standard error, and agreement consistency
            reliability_weight = variance_weights.get(stratum, 0.75)
            weight = pop_prop * se * reliability_weight
            
            deviation = abs(sample_prop - pop_prop)
            weighted_error += weight * deviation
            total_weight += weight
        
        if total_weight > 0:
            vwrs = 1 - (weighted_error / total_weight)
        else:
            vwrs = 0
        
        # Store results
        results['dimensions'][dim_name] = {
            'traditional_gri': traditional_gri,
            'vwrs': vwrs,
            'difference': vwrs - traditional_gri,
            'n_strata': len(benchmark_props),
            'n_sampled': len(sample_props),
            'mean_agreement_variance': np.mean(list(agreement_variances.values())) if agreement_variances else None
        }
    
    # Save results
    results_df = pd.DataFrame([
        {
            'survey': results['survey'],
            'dimension': dim_name,
            'traditional_gri': dim_data['traditional_gri'],
            'vwrs': dim_data['vwrs'],
            'difference': dim_data['difference'],
            'n_strata': dim_data['n_strata'],
            'n_sampled': dim_data['n_sampled'],
            'mean_agreement_variance': dim_data['mean_agreement_variance']
        }
        for dim_name, dim_data in results['dimensions'].items()
    ])
    
    output_file = output_path / f'GD{gd_num}_vwrs_comparison.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Also save detailed JSON
    json_file = output_path / f'GD{gd_num}_vwrs_details.json'
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def main():
    """Calculate VWRS for all GD surveys."""
    base_path = Path(__file__).parent.parent
    output_path = base_path / 'analysis_output' / 'vwrs_results'
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_results = []
    
    # Process each GD survey
    for gd_num in [1, 2, 3]:
        print(f"\n{'='*60}")
        print(f"Processing GD{gd_num}")
        print('='*60)
        
        results = calculate_vwrs_all_dimensions(gd_num, base_path, output_path)
        if results:
            all_results.append(results)
    
    # Create summary comparison
    if all_results:
        print("\n\nSummary Comparison")
        print("="*60)
        
        comparison_data = []
        for result in all_results:
            for dim_name, dim_data in result['dimensions'].items():
                comparison_data.append({
                    'survey': result['survey'],
                    'dimension': dim_name,
                    'traditional_gri': dim_data['traditional_gri'],
                    'vwrs': dim_data['vwrs'],
                    'improvement': dim_data['difference']
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Print average improvements by dimension
        avg_improvement = comparison_df.groupby('dimension')['improvement'].mean().sort_values(ascending=False)
        print("\nAverage VWRS improvement over traditional GRI by dimension:")
        for dim, imp in avg_improvement.items():
            print(f"  {dim}: {imp:+.4f}")
        
        # Save comparison
        comparison_df.to_csv(output_path / 'all_surveys_vwrs_comparison.csv', index=False)


if __name__ == "__main__":
    main()