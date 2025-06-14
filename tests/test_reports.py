"""
Tests for the reports module.
"""

import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from gri.reports import (
    generate_text_report,
    export_results,
    create_summary_statistics,
    generate_comparison_report
)


@pytest.fixture
def sample_scorecard():
    """Create sample scorecard data."""
    return pd.DataFrame({
        'dimension': ['Country × Gender × Age', 'Country × Religion', 'Country × Environment'],
        'gri_score': [0.8234, 0.7856, 0.8912],
        'diversity_score': [0.9123, 0.8734, 0.9234],
        'sample_size': [1000, 1000, 1000],
        'n_strata': [240, 84, 120],
        'n_represented': [218, 73, 115]
    })


@pytest.fixture
def sample_survey_df():
    """Create sample survey data."""
    return pd.DataFrame({
        'country': ['USA'] * 50 + ['India'] * 30 + ['Brazil'] * 20,
        'gender': ['Male'] * 60 + ['Female'] * 40,
        'age_group': ['18-25'] * 40 + ['26-35'] * 30 + ['36-45'] * 30
    })


@pytest.fixture
def sample_benchmark_df():
    """Create sample benchmark data."""
    return pd.DataFrame({
        'country': ['USA', 'India', 'Brazil'],
        'population_proportion': [0.3, 0.5, 0.2]
    })


def test_generate_text_report(sample_scorecard):
    """Test text report generation."""
    # Basic report
    report = generate_text_report(sample_scorecard)
    assert isinstance(report, str)
    assert "GLOBAL REPRESENTATIVENESS INDEX" in report
    assert "Country × Gender × Age" in report
    assert "0.8234" in report
    
    # Report with survey name
    report = generate_text_report(sample_scorecard, survey_name="Test Survey")
    assert "Test Survey" in report
    
    # Report without analysis
    report = generate_text_report(sample_scorecard, include_analysis=False)
    assert len(report) > 100  # Should have content
    
    # Report with analysis
    report = generate_text_report(sample_scorecard, include_analysis=True)
    assert "ANALYSIS" in report or "Analysis" in report or "Interpretation" in report


def test_export_results(sample_scorecard):
    """Test unified export results function."""
    # Test CSV export
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        exported_path = export_results(sample_scorecard, format='csv', filepath=temp_path)
        assert temp_path.exists()
        
        # Verify content
        df = pd.read_csv(temp_path)
        assert len(df) == len(sample_scorecard)
        assert 'dimension' in df.columns
    finally:
        if temp_path.exists():
            temp_path.unlink()
    
    # Test JSON export
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        exported_path = export_results(sample_scorecard, format='json', filepath=temp_path)
        assert temp_path.exists()
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_create_summary_statistics(sample_survey_df):
    """Test summary statistics creation."""
    # Create a proper benchmark with both country and gender
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'USA', 'India', 'India', 'Brazil', 'Brazil'],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.15, 0.15, 0.25, 0.25, 0.1, 0.1]
    })
    
    stats = create_summary_statistics(
        sample_survey_df, 
        benchmark_df,
        dimension_columns=['country', 'gender']
    )
    
    assert isinstance(stats, dict)
    assert 'total_participants' in stats
    assert 'dimension' in stats
    assert 'dimension_columns' in stats
    
    assert stats['total_participants'] == 100
    assert stats['dimension'] == 'country × gender'




def test_generate_comparison_report():
    """Test comparison report generation."""
    # Create sample data for multiple surveys
    surveys = {
        'Survey 1': pd.DataFrame({
            'dimension': ['Country', 'Gender', 'Age Group'],
            'gri_score': [0.85, 0.90, 0.82],
            'diversity_score': [0.88, 0.95, 0.85]
        }),
        'Survey 2': pd.DataFrame({
            'dimension': ['Country', 'Gender', 'Age Group'],
            'gri_score': [0.82, 0.88, 0.80],
            'diversity_score': [0.85, 0.92, 0.83]
        })
    }
    
    # Basic comparison report
    report = generate_comparison_report(surveys)
    assert isinstance(report, str)
    assert "Survey 1" in report
    assert "Survey 2" in report
    assert "COMPARISON" in report or "Comparison" in report
    
    # Report with trends
    report = generate_comparison_report(surveys, include_trends=True)
    assert "trend" in report.lower() or "change" in report.lower()
    
    # Report to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        report = generate_comparison_report(
            surveys,
            output_file=temp_path,
            include_trends=True
        )
        assert temp_path.exists()
        
        # Verify content
        with open(temp_path, 'r') as f:
            content = f.read()
        assert len(content) > 100
        assert "Survey 1" in content
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == '__main__':
    pytest.main([__file__])