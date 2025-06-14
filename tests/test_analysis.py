"""
Tests for the analysis module.
"""

import pytest
import pandas as pd
import numpy as np
from gri.analysis import (
    calculate_segment_deviations,
    identify_top_contributors,
    check_category_alignment,
    generate_alignment_report,
    calculate_dimension_impact
)


@pytest.fixture
def sample_survey_df():
    """Create sample survey data."""
    return pd.DataFrame({
        'country': ['USA', 'USA', 'India', 'India', 'Brazil'],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'age_group': ['18-25', '26-35', '18-25', '26-35', '36-45']
    })


@pytest.fixture
def sample_benchmark_df():
    """Create sample benchmark data."""
    return pd.DataFrame({
        'country': ['USA', 'USA', 'India', 'India', 'Brazil', 'Brazil'],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.15, 0.15, 0.25, 0.25, 0.1, 0.1]
    })


def test_calculate_segment_deviations(sample_survey_df, sample_benchmark_df):
    """Test segment deviation calculation."""
    deviations = calculate_segment_deviations(
        sample_survey_df,
        sample_benchmark_df,
        ['country', 'gender']
    )
    
    assert 'deviation' in deviations.columns
    assert 'sample_proportion' in deviations.columns
    assert 'benchmark_proportion' in deviations.columns
    assert 'abs_deviation' in deviations.columns
    assert len(deviations) > 0
    
    # Check that deviations sum to approximately 0
    assert abs(deviations['deviation'].sum()) < 0.01


def test_identify_top_contributors():
    """Test identification of top contributing segments."""
    # Create test deviation data
    deviations = pd.DataFrame({
        'segment_name': ['A', 'B', 'C', 'D'],
        'deviation': [0.1, -0.05, 0.03, -0.08],
        'abs_deviation': [0.1, 0.05, 0.03, 0.08],
        'sample_proportion': [0.3, 0.1, 0.2, 0.4],
        'benchmark_proportion': [0.2, 0.15, 0.17, 0.48],
        'tvd_contribution': [0.05, 0.025, 0.015, 0.04]  # abs_deviation / 2
    })
    
    # Test over-represented
    over_rep = identify_top_contributors(deviations, n=2, contribution_type='over')
    assert len(over_rep) == 2
    assert over_rep.iloc[0]['segment_name'] == 'A'
    
    # Test under-represented
    under_rep = identify_top_contributors(deviations, n=2, contribution_type='under')
    assert len(under_rep) == 2
    assert under_rep.iloc[0]['segment_name'] == 'D'
    
    # Test both
    both = identify_top_contributors(deviations, n=3, contribution_type='both')
    assert len(both) == 3


def test_check_category_alignment(sample_survey_df, sample_benchmark_df):
    """Test category alignment checking."""
    alignment = check_category_alignment(
        sample_survey_df,
        sample_benchmark_df,
        ['country', 'gender']
    )
    
    assert 'country' in alignment
    assert 'gender' in alignment
    
    for col, stats in alignment.items():
        assert 'coverage' in stats
        assert 'matched' in stats
        assert 'unmatched' in stats
        assert 'total_survey' in stats
        assert stats['coverage'] >= 0 and stats['coverage'] <= 1


def test_calculate_dimension_impact(sample_survey_df, sample_benchmark_df):
    """Test dimension impact calculation."""
    # Need to ensure benchmark has required columns
    benchmark_with_pop = sample_benchmark_df.copy()
    if 'population_proportion' not in benchmark_with_pop.columns:
        # Add population proportion based on counts
        total = len(benchmark_with_pop)
        benchmark_with_pop['population_proportion'] = 1.0 / total
    
    impact = calculate_dimension_impact(
        sample_survey_df,
        benchmark_with_pop,
        ['country', 'gender'],
        n_targets=2
    )
    
    assert 'current_gri' in impact
    assert 'potential_gri' in impact
    assert 'improvement' in impact
    assert 'improvement_pct' in impact
    assert 'segment_impacts' in impact
    
    assert impact['potential_gri'] >= impact['current_gri']
    assert impact['improvement'] >= 0


def test_generate_alignment_report(sample_survey_df):
    """Test alignment report generation."""
    # Create mock benchmarks
    benchmarks = {
        'Country × Gender': pd.DataFrame({
            'country': ['USA', 'India', 'Brazil'],
            'gender': ['Male', 'Female', 'Male'],
            'population_proportion': [0.2, 0.3, 0.5]
        })
    }
    
    report = generate_alignment_report(sample_survey_df, benchmarks)
    
    assert isinstance(report, dict)
    assert 'Country × Gender' in report
    assert 'status' in report['Country × Gender']
    
    # Check report structure
    dim_report = report['Country × Gender']
    if dim_report['status'] == 'complete':
        assert 'overall_alignment' in dim_report
        assert 'column_alignment' in dim_report


if __name__ == '__main__':
    pytest.main([__file__])