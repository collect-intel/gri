"""
Global Representativeness Index (GRI) Library

This library provides tools for measuring how well survey samples represent
the global population across demographic dimensions.

The GRI is calculated using Total Variation Distance and provides scores from
0.0 (complete mismatch) to 1.0 (perfect representativeness).

Main functions:
- calculate_gri: Calculate the Global Representativeness Index
- calculate_diversity_score: Calculate demographic diversity coverage
- calculate_gri_scorecard: Calculate full scorecard using configuration
- load_data: Load CSV data files
- aggregate_data: Aggregate survey data by demographic strata
- get_config: Access configuration management

Example usage:
    import pandas as pd
    from gri import calculate_gri, calculate_gri_scorecard, load_data
    
    # Basic usage
    survey_df = load_data('survey_data.csv')
    benchmark_df = load_data('benchmark_data.csv')
    
    gri_score = calculate_gri(
        survey_df, 
        benchmark_df, 
        ['country', 'gender', 'age_group']
    )
    
    # Configuration-based usage
    benchmark_data = {
        'age_gender': load_data('benchmark_age_gender.csv'),
        'religion': load_data('benchmark_religion.csv'),
        'environment': load_data('benchmark_environment.csv')
    }
    
    scorecard = calculate_gri_scorecard(
        survey_df, 
        benchmark_data,
        survey_source='global_dialogues'
    )
    
    print(scorecard)
"""

from .calculator import calculate_gri, calculate_diversity_score
from .calculator_config import calculate_gri_scorecard, standardize_survey_data
from .utils import load_data, aggregate_data
from .config import get_config

__version__ = "1.0.0"
__author__ = "GRI Project Contributors"
__email__ = "contact@gri-project.org"

__all__ = [
    "calculate_gri",
    "calculate_diversity_score",
    "calculate_gri_scorecard",
    "standardize_survey_data",
    "load_data",
    "aggregate_data",
    "get_config"
]