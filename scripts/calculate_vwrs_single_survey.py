#!/usr/bin/env python3
"""
Calculate Variance-Weighted Representativeness Score (VWRS) for a single survey.

VWRS accounts for sampling reliability by weighting deviations by their standard error.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
from typing import Dict, Tuple


def calculate_vwrs_for_survey(
    survey_df: pd.DataFrame,
    benchmark_data: Dict[str, float],
    dimension_columns: list[str]
) -> Tuple[float, float, pd.DataFrame]:
    """
    Calculate both traditional GRI and VWRS for a survey dimension.
    
    Args:
        survey_df: Survey data with demographic columns
        benchmark_data: Population proportions for each stratum
        dimension_columns: List of columns defining the dimension 
                          (e.g., ['country'] or ['country', 'gender', 'age_group'])
    
    Returns:
        Tuple of (GRI score, VWRS score, detailed breakdown DataFrame)
    """
    # Create stratum identifier
    if len(dimension_columns) == 1:
        survey_df['stratum'] = survey_df[dimension_columns[0]]
    else:
        survey_df['stratum'] = survey_df[dimension_columns].apply(
            lambda x: ' × '.join(x.dropna().astype(str)), axis=1
        )
    
    # Calculate sample counts and proportions
    sample_counts = survey_df['stratum'].value_counts()
    total_sample = len(survey_df)
    sample_proportions = (sample_counts / total_sample).to_dict()
    
    # Calculate scores
    traditional_gri = 0
    weighted_error = 0
    total_weight = 0
    
    details = []
    
    for stratum, pop_prop in benchmark_data.items():
        # Get sample statistics
        sample_prop = sample_proportions.get(stratum, 0)
        sample_count = sample_counts.get(stratum, 0)
        
        # Calculate standard error
        if sample_count > 0:
            # Standard error of proportion: sqrt(p*(1-p)/n)
            se = np.sqrt(sample_prop * (1 - sample_prop) / sample_count)
        else:
            # Maximum uncertainty for unsampled strata
            se = 0.5  # This gives maximum SE for a proportion
        
        # Absolute deviation
        deviation = abs(sample_prop - pop_prop)
        
        # Traditional GRI contribution
        traditional_gri += 0.5 * deviation
        
        # VWRS weight (population size × standard error)
        # This gives more weight to deviations in large populations with high uncertainty
        weight = pop_prop * se
        weighted_error += weight * deviation
        total_weight += weight
        
        details.append({
            'stratum': stratum,
            'population_prop': pop_prop,
            'sample_prop': sample_prop,
            'sample_count': sample_count,
            'standard_error': se,
            'deviation': deviation,
            'gri_contribution': 0.5 * deviation,
            'vwrs_weight': weight,
            'weighted_contribution': weight * deviation
        })
    
    # Calculate final scores
    traditional_gri = 1 - traditional_gri
    
    if total_weight > 0:
        vwrs = 1 - (weighted_error / total_weight)
    else:
        vwrs = 0
    
    details_df = pd.DataFrame(details).sort_values('population_prop', ascending=False)
    
    return traditional_gri, vwrs, details_df


def main():
    """Example usage calculating VWRS for a survey."""
    
    # Example: Load GD3 data
    base_path = Path(__file__).parent.parent
    survey_path = base_path / 'data' / 'raw' / 'survey_data' / 'global-dialogues' / 'Data' / 'GD3' / 'GD3_participants.csv'
    
    # Load survey data
    df = pd.read_csv(survey_path)
    
    # Standardize column names
    column_mapping = {
        'What country or region do you most identify with?': 'country',
        'What is your gender?': 'gender',
        'How old are you?': 'age_group'
    }
    df = df.rename(columns=column_mapping)
    
    # Example benchmark data (you'd load this from your benchmark files)
    # Here's a simplified country-level example
    country_benchmark = {
        'China': 0.180,
        'India': 0.175,
        'United States': 0.042,
        'Indonesia': 0.035,
        'Pakistan': 0.028,
        'Brazil': 0.027,
        'Nigeria': 0.026,
        'Bangladesh': 0.021,
        'Russian Federation': 0.018,
        'Mexico': 0.016,
        'Japan': 0.016,
        'Ethiopia': 0.015,
        'Philippines': 0.014,
        'Egypt': 0.013,
        'Viet Nam': 0.012,
        # ... add all countries
    }
    
    # Normalize to sum to 1
    total = sum(country_benchmark.values())
    country_benchmark = {k: v/total for k, v in country_benchmark.items()}
    
    # Calculate scores
    gri, vwrs, details = calculate_vwrs_for_survey(
        df, 
        country_benchmark,
        ['country']
    )
    
    print(f"Traditional GRI: {gri:.4f}")
    print(f"VWRS: {vwrs:.4f}")
    print(f"Difference: {vwrs - gri:+.4f}")
    
    print("\nTop 10 strata by weighted contribution to error:")
    print(details.nlargest(10, 'weighted_contribution')[
        ['stratum', 'population_prop', 'sample_prop', 'sample_count', 'weighted_contribution']
    ].to_string(index=False))
    
    print("\nComparison of approaches:")
    print("Traditional GRI penalizes all deviations equally")
    print("VWRS gives less penalty to:")
    print("  - Small populations (less important globally)")
    print("  - Large sample sizes (more reliable estimates)")
    print("  - Strata with low internal variance (SE approaches 0)")
    
    # Save detailed results
    output_path = base_path / 'analysis_output' / 'vwrs_example.csv'
    details.to_csv(output_path, index=False)
    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()