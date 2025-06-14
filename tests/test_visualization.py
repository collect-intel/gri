"""
Tests for the visualization module.
"""

import pytest
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
from gri.visualization import (
    plot_gri_scorecard,
    plot_segment_deviations,
    plot_sample_distribution,
    plot_diversity_coverage,
    create_comparison_plot,
    plot_cumulative_impact
)


@pytest.fixture
def sample_scorecard():
    """Create sample scorecard data."""
    return pd.DataFrame({
        'dimension': ['Country', 'Gender', 'Age Group'],
        'gri_score': [0.85, 0.92, 0.78],
        'diversity_score': [0.90, 0.95, 0.82],
        'sample_size': [1000, 1000, 1000]
    })


@pytest.fixture
def sample_deviations():
    """Create sample deviation data."""
    return pd.DataFrame({
        'segment_name': ['USA-Male', 'India-Female', 'Brazil-Male', 'China-Female'],
        'deviation': [0.05, -0.03, 0.02, -0.04],
        'absolute_deviation': [0.05, 0.03, 0.02, 0.04],
        'sample_proportion': [0.15, 0.07, 0.12, 0.06],
        'benchmark_proportion': [0.10, 0.10, 0.10, 0.10]
    })


def test_plot_gri_scorecard(sample_scorecard):
    """Test GRI scorecard plotting."""
    # Test basic plot
    fig = plot_gri_scorecard(sample_scorecard)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test with title
    fig = plot_gri_scorecard(sample_scorecard, title="Test Scorecard")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test saving to file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        fig = plot_gri_scorecard(sample_scorecard, save_path=temp_path)
        assert temp_path.exists()
        plt.close(fig)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_plot_segment_deviations(sample_deviations):
    """Test segment deviation plotting."""
    # The function expects specific columns
    deviations_with_required_cols = sample_deviations.copy()
    if 'tvd_contribution' not in deviations_with_required_cols.columns:
        deviations_with_required_cols['tvd_contribution'] = deviations_with_required_cols['absolute_deviation'] / 2
    
    # Test basic plot
    fig = plot_segment_deviations(deviations_with_required_cols)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test with top_n parameter
    fig = plot_segment_deviations(deviations_with_required_cols, top_n=2)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_plot_sample_distribution():
    """Test sample distribution plotting."""
    # Create sample data
    survey_df = pd.DataFrame({
        'country': ['USA'] * 50 + ['India'] * 30 + ['Brazil'] * 20,
        'gender': ['Male'] * 60 + ['Female'] * 40
    })
    
    # Test plotting single dimension
    fig = plot_sample_distribution(survey_df, 'country')
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test with benchmark comparison
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'India', 'Brazil'],
        'population_proportion': [0.3, 0.5, 0.2]
    })
    
    fig = plot_sample_distribution(
        survey_df, 
        'country',
        benchmark_df=benchmark_df
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_plot_diversity_coverage():
    """Test diversity coverage plotting."""
    diversity_scores = {
        'Country': 0.85,
        'Gender': 1.0,
        'Age Group': 0.75,
        'Religion': 0.60
    }
    
    fig = plot_diversity_coverage(diversity_scores)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_create_comparison_plot():
    """Test survey comparison plotting."""
    # Create sample data for multiple surveys
    surveys = {
        'Survey 1': pd.DataFrame({
            'dimension': ['Country', 'Gender'],
            'gri_score': [0.85, 0.90],
            'diversity_score': [0.88, 0.95]
        }),
        'Survey 2': pd.DataFrame({
            'dimension': ['Country', 'Gender'],
            'gri_score': [0.82, 0.88],
            'diversity_score': [0.85, 0.92]
        })
    }
    
    # Test specific dimension (function requires dimension parameter)
    fig = create_comparison_plot(surveys, 'Country')
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test with different metric
    fig = create_comparison_plot(surveys, 'Gender', metric='diversity_score')
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_plot_cumulative_impact():
    """Test cumulative impact plotting."""
    deviations = pd.DataFrame({
        'segment_name': ['USA-Male', 'India-Female', 'Brazil-Male', 'China-Female'],
        'deviation': [0.05, -0.03, 0.02, -0.04],
        'abs_deviation': [0.05, 0.03, 0.02, 0.04],
        'tvd_contribution': [0.025, 0.015, 0.010, 0.020]
    })
    
    fig = plot_cumulative_impact(deviations)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    
    # Test with custom n_segments
    fig = plot_cumulative_impact(deviations, n_segments=3)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_plot_error_handling():
    """Test error handling in plotting functions."""
    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    
    with pytest.raises((ValueError, KeyError)):
        plot_gri_scorecard(empty_df)
    
    # Test with missing columns
    bad_df = pd.DataFrame({'wrong_column': [1, 2, 3]})
    
    with pytest.raises((ValueError, KeyError)):
        plot_segment_deviations(bad_df)


if __name__ == '__main__':
    pytest.main([__file__])