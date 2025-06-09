import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from gri.validation import (
    validate_survey_data,
    validate_benchmark_data,
    validate_yaml_config,
    validate_gri_calculation_inputs,
    ValidationError
)


def test_validate_survey_data_valid():
    """Test validation of valid survey data."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male'],
        'age_group': ['18-25', '26-35', '36-45']
    })
    
    is_valid, issues = validate_survey_data(df, ['country', 'gender', 'age_group'])
    assert is_valid
    assert len(issues) == 0


def test_validate_survey_data_missing_columns():
    """Test validation with missing required columns."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female']
    })
    
    is_valid, issues = validate_survey_data(df, ['country', 'gender', 'age_group'])
    assert not is_valid
    assert any('Missing required columns' in issue for issue in issues)


def test_validate_survey_data_empty():
    """Test validation of empty DataFrame."""
    df = pd.DataFrame()
    
    is_valid, issues = validate_survey_data(df)
    assert not is_valid
    assert 'Survey data is empty' in issues


def test_validate_survey_data_high_nulls():
    """Test validation with high percentage of null values."""
    df = pd.DataFrame({
        'country': ['USA', None, None, None, None],
        'gender': ['Male', 'Female', None, None, None]
    })
    
    is_valid, issues = validate_survey_data(df)
    # Should have warnings about high null percentages
    assert any('missing values' in issue for issue in issues)


def test_validate_benchmark_data_valid():
    """Test validation of valid benchmark data."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male'],
        'population_proportion': [0.4, 0.35, 0.25]
    })
    
    is_valid, issues = validate_benchmark_data(df)
    assert is_valid
    assert len(issues) == 0


def test_validate_benchmark_data_missing_proportion_column():
    """Test validation with missing population_proportion column."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female']
    })
    
    is_valid, issues = validate_benchmark_data(df)
    assert not is_valid
    assert "Missing required 'population_proportion' column" in issues


def test_validate_benchmark_data_proportions_dont_sum_to_one():
    """Test validation when proportions don't sum to 1."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'population_proportion': [0.6, 0.6]  # Sum = 1.2
    })
    
    is_valid, issues = validate_benchmark_data(df)
    assert not is_valid
    assert any('sum to' in issue for issue in issues)


def test_validate_benchmark_data_negative_proportions():
    """Test validation with negative proportions."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'population_proportion': [0.8, -0.2]
    })
    
    is_valid, issues = validate_benchmark_data(df)
    assert not is_valid
    assert 'Found negative population proportions' in issues


def test_validate_benchmark_data_null_proportions():
    """Test validation with null proportions."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'population_proportion': [0.5, None]
    })
    
    is_valid, issues = validate_benchmark_data(df)
    assert not is_valid
    assert 'Found null population proportions' in issues


def test_validate_yaml_config_file_not_found():
    """Test validation when config file doesn't exist."""
    is_valid, issues = validate_yaml_config('nonexistent.yaml')
    assert not is_valid
    assert any('not found' in issue for issue in issues)


def test_validate_yaml_config_valid_dimensions():
    """Test validation of valid dimensions config."""
    config_content = """
standard_scorecard:
  - ['country', 'gender', 'age_group']
  - ['country', 'religion']

extended_dimensions:
  coarse:
    - ['country']
    - ['gender']
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_dimensions.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        
        # Rename to have 'dimensions' in the stem for validation
        new_name = f.name.replace('_dimensions', '/dimensions')
        new_dir = Path(f.name).parent / 'temp_config'
        new_dir.mkdir(exist_ok=True)
        new_path = new_dir / 'dimensions.yaml'
        
        with open(new_path, 'w') as new_f:
            new_f.write(config_content)
        
        try:
            is_valid, issues = validate_yaml_config(str(new_path))
            assert is_valid
            assert len(issues) == 0
        finally:
            os.unlink(f.name)
            if new_path.exists():
                os.unlink(new_path)
            if new_dir.exists():
                new_dir.rmdir()


def test_validate_gri_calculation_inputs_valid():
    """Test validation of valid GRI calculation inputs."""
    survey_df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female']
    })
    
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female'],
        'population_proportion': [0.5, 0.5]
    })
    
    is_valid, issues = validate_gri_calculation_inputs(
        survey_df, benchmark_df, ['country', 'gender']
    )
    assert is_valid
    assert len(issues) == 0


def test_validate_gri_calculation_inputs_no_overlap():
    """Test validation when survey and benchmark have no common strata."""
    survey_df = pd.DataFrame({
        'country': ['USA', 'USA'],
        'gender': ['Male', 'Male']
    })
    
    benchmark_df = pd.DataFrame({
        'country': ['Canada', 'Mexico'],
        'gender': ['Female', 'Female'],
        'population_proportion': [0.5, 0.5]
    })
    
    is_valid, issues = validate_gri_calculation_inputs(
        survey_df, benchmark_df, ['country', 'gender']
    )
    assert not is_valid
    assert any('No common strata' in issue for issue in issues)


def test_validate_gri_calculation_inputs_missing_strata_columns():
    """Test validation with missing strata columns."""
    survey_df = pd.DataFrame({
        'country': ['USA', 'Canada']
    })
    
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'population_proportion': [0.5, 0.5]
    })
    
    is_valid, issues = validate_gri_calculation_inputs(
        survey_df, benchmark_df, ['country', 'gender']
    )
    assert not is_valid
    assert any('missing strata columns' in issue for issue in issues)