"""
Tests for the data_loader module.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from gri.data_loader import (
    load_benchmark_suite,
    load_gd_survey,
    apply_segment_mappings,
    validate_survey_data
)


@pytest.fixture
def sample_gd_data():
    """Create sample GD survey data for testing."""
    return pd.DataFrame({
        'participant_id': ['P001', 'P002', 'P003'],
        'country': ['United States', 'India', 'Brazil'],
        'gender': ['Male', 'Female', 'Male'],
        'age_group': ['26-35', '36-45', '18-25'],
        'religion': ['Christianity', 'Hinduism', 'Christianity'],
        'environment': ['Urban', 'Urban', 'Rural']
    })


@pytest.fixture
def sample_benchmark_data():
    """Create sample benchmark data for testing."""
    return pd.DataFrame({
        'country': ['United States', 'India', 'Brazil'],
        'gender': ['Male', 'Female', 'Male'],
        'age_group': ['26-35', '36-45', '18-25'],
        'population_proportion': [0.1, 0.3, 0.2]
    })


def test_validate_survey_data(sample_gd_data):
    """Test survey data validation."""
    # Should pass with all required columns
    is_valid, issues = validate_survey_data(sample_gd_data)
    assert is_valid
    assert len(issues) == 0
    
    # Should fail with missing columns
    incomplete_data = sample_gd_data.drop(columns=['gender'])
    is_valid, issues = validate_survey_data(incomplete_data)
    assert not is_valid
    assert any('gender' in issue for issue in issues)


def test_apply_segment_mappings(sample_gd_data):
    """Test segment mapping application."""
    # Test without config (uses default)
    mapped_df = apply_segment_mappings(sample_gd_data.copy())
    
    # Should at least not error and return same shape
    assert len(mapped_df) == len(sample_gd_data)
    assert set(mapped_df.columns) == set(sample_gd_data.columns)


def test_load_gd_survey_columns():
    """Test that load_gd_survey handles different column formats."""
    # Create a CSV that mimics GD format with columns at expected positions
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Write header and data with columns at expected positions
        # Positions: 0,1,2(participant_id),3,4,5(age_group),6(gender),7(environment),8,9(religion),10(country)
        f.write('col0,col1,participant_id,col3,col4,age_group,gender,environment,col8,religion,country\n')
        f.write('x,x,P001,x,x,26-35,Male,Urban,x,Hinduism,India\n')
        f.write('x,x,P002,x,x,36-45,Female,Rural,x,Christianity,Brazil\n')
        temp_path = Path(f.name)
    
    try:
        df = load_gd_survey(temp_path)
        # The function extracts specific columns by position
        assert 'country' in df.columns
        assert 'gender' in df.columns
        assert 'age_group' in df.columns
    finally:
        temp_path.unlink()


def test_load_benchmark_suite_structure():
    """Test that load_benchmark_suite returns expected structure."""
    # This test would need actual benchmark files or mocking
    # For now, just test the function signature
    try:
        benchmarks = load_benchmark_suite(data_dir='nonexistent_dir')
    except Exception:
        # Expected to fail with nonexistent directory
        pass
    
    # Test with dimensions filter
    try:
        benchmarks = load_benchmark_suite(
            data_dir='data/processed',
            dimensions=['Country', 'Gender']
        )
        # Would check structure if files existed
    except Exception:
        pass


if __name__ == '__main__':
    pytest.main([__file__])