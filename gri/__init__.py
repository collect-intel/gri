"""
Global Representativeness Index (GRI) Library

This library provides tools for measuring how well survey samples represent
the global population across demographic dimensions.

The GRI is calculated using Total Variation Distance and provides scores from
0.0 (complete mismatch) to 1.0 (perfect representativeness).

Two ways to use this library:
1. **Functional API**: Direct functions for specific calculations
2. **GRIAnalysis class**: Convenience wrapper for complete analysis workflows

Main components:
- calculator: Core GRI and diversity score calculations
- calculator_config: Configuration-based calculations
- data_loader: Unified data loading for benchmarks and surveys
- analysis: Segment deviation and alignment analysis
- visualization: Standard plotting functions
- simulation: Monte Carlo simulations for maximum possible scores
- reports: Report generation and export utilities
- config: Configuration management
- utils: General utilities

Example usage:

Quick calculation using functions:
    from gri import calculate_gri, load_data
    
    survey = load_data('survey.csv')
    benchmark = load_data('benchmark.csv')
    gri_score = calculate_gri(survey, benchmark, ['country', 'gender'])
    print(f"GRI Score: {gri_score:.4f}")

Full analysis workflow using GRIAnalysis class:
    from gri import GRIAnalysis
    
    # Load and analyze survey data
    analysis = GRIAnalysis.from_survey_file('data/gd3_participants.csv')
    scorecard = analysis.calculate_scorecard(include_max_possible=True)
    
    # Generate visualizations and reports
    analysis.plot_scorecard(save_to='results/scorecard.png')
    analysis.plot_top_deviations('Country × Gender × Age')
    print(analysis.generate_report())
"""

# Core calculation functions
from .calculator import calculate_gri, calculate_diversity_score
from .calculator_config import calculate_gri_scorecard, standardize_survey_data
from .variance_weighted import calculate_vwrs, calculate_vwrs_from_dataframes
from .strategic_index import calculate_sri, calculate_sri_from_dataframes

# Data loading
from .utils import load_data, aggregate_data
from .data_loader import (
    load_benchmark_suite, 
    load_gd_survey,
    load_wvs_survey,
    apply_segment_mappings,
    validate_survey_data
)

# Analysis functions
from .analysis import (
    check_category_alignment,
    calculate_segment_deviations,
    identify_top_contributors,
    generate_alignment_report,
    calculate_dimension_impact
)

# Visualization
from .visualization import (
    plot_gri_scorecard,
    plot_sample_distribution,
    plot_diversity_coverage,
    plot_segment_deviations,
    plot_cumulative_impact,
    create_comparison_plot
)

# Simulation and max scores
from .simulation import (
    monte_carlo_max_scores,
    calculate_max_possible_gri,
    calculate_efficiency_ratio,
    generate_sample_size_curve
)

# Reports
from .reports import (
    generate_text_report,
    export_results,
    create_summary_statistics,
    generate_comparison_report
)

# Configuration
from .config import get_config, GRIConfig

# High-level analysis class
from .analyzer import GRIAnalysis

# Scorecard functionality
from .scorecard import GRIScorecard

__version__ = "2.0.0"
__author__ = "GRI Project Contributors"
__email__ = "contact@gri-project.org"

__all__ = [
    # Core functions
    "calculate_gri",
    "calculate_diversity_score",
    "calculate_gri_scorecard",
    "standardize_survey_data",
    "calculate_vwrs",
    "calculate_vwrs_from_dataframes",
    "calculate_sri",
    "calculate_sri_from_dataframes",
    
    # Data loading
    "load_data",
    "aggregate_data",
    "load_benchmark_suite",
    "load_gd_survey",
    "load_wvs_survey",
    "apply_segment_mappings",
    "validate_survey_data",
    
    # Analysis
    "check_category_alignment",
    "calculate_segment_deviations",
    "identify_top_contributors",
    "generate_alignment_report",
    "calculate_dimension_impact",
    
    # Visualization
    "plot_gri_scorecard",
    "plot_sample_distribution",
    "plot_diversity_coverage",
    "plot_segment_deviations",
    "plot_cumulative_impact",
    "create_comparison_plot",
    
    # Simulation
    "monte_carlo_max_scores",
    "calculate_max_possible_gri",
    "calculate_efficiency_ratio",
    "generate_sample_size_curve",
    
    # Reports
    "generate_text_report",
    "export_results",
    "create_summary_statistics",
    "generate_comparison_report",
    
    # Configuration
    "get_config",
    "GRIConfig",
    
    # High-level analysis class
    "GRIAnalysis",
    
    # Scorecard
    "GRIScorecard"
]