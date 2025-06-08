"""
Global Representativeness Index (GRI) Library

This library provides tools for measuring how well survey samples represent
the global population across demographic dimensions.

The GRI is calculated using Total Variation Distance and provides scores from
0.0 (complete mismatch) to 1.0 (perfect representativeness).

Main functions:
- calculate_gri: Calculate the Global Representativeness Index
- calculate_diversity_score: Calculate demographic diversity coverage
- load_data: Load CSV data files
- aggregate_data: Aggregate survey data by demographic strata

Example usage:
    import pandas as pd
    from gri import calculate_gri, load_data
    
    # Load your survey and benchmark data
    survey_df = load_data('survey_data.csv')
    benchmark_df = load_data('benchmark_data.csv')
    
    # Calculate GRI for country x gender x age
    gri_score = calculate_gri(
        survey_df, 
        benchmark_df, 
        ['country', 'gender', 'age_group']
    )
    
    print(f"GRI Score: {gri_score:.4f}")
"""

from .calculator import calculate_gri, calculate_diversity_score
from .utils import load_data, aggregate_data

__version__ = "1.0.0"
__author__ = "GRI Project Contributors"
__email__ = "contact@gri-project.org"

__all__ = [
    "calculate_gri",
    "calculate_diversity_score", 
    "load_data",
    "aggregate_data"
]