import pytest
import pandas as pd
import tempfile
from pathlib import Path
from gri.calculator_config import (
    standardize_survey_data, 
    add_regional_dimensions,
    aggregate_benchmark_for_dimension,
    calculate_gri_for_dimension,
    calculate_gri_scorecard
)
from gri.config import GRIConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        
        # Minimal config files for testing
        dimensions_content = """
standard_scorecard:
  - name: "Country × Gender"
    columns: ["country", "gender"]
    description: "Test dimension"
  - name: "Country"
    columns: ["country"] 
    description: "Country only"

extended_dimensions:
  - name: "Region"
    columns: ["region"]
    description: "Regional dimension"
    requires_mapping: ["country_to_region"]
"""
        
        segments_content = """
benchmark_mappings:
  gender:
    "Male": ["Male"]
    "Female": ["Female"]
  country:
    "United States": ["USA", "US"]

survey_mappings:
  test_survey:
    gender:
      "Male": ["M", "male"]
      "Female": ["F", "female"]
    country:
      "United States": ["USA"]
      "Canada": ["CAN"]
"""
        
        regions_content = """
country_to_region:
  "North America":
    - "United States"
    - "Canada"
  "Europe":
    - "Germany"

region_to_continent:
  "North America":
    - "North America"
  "Asia":
    - "Europe"
"""
        
        (config_dir / "dimensions.yaml").write_text(dimensions_content)
        (config_dir / "segments.yaml").write_text(segments_content)
        (config_dir / "regions.yaml").write_text(regions_content)
        
        yield GRIConfig(str(config_dir))


@pytest.fixture
def sample_survey_data():
    """Create sample survey data."""
    return pd.DataFrame({
        'country': ['USA', 'USA', 'CAN', 'CAN'],
        'gender': ['M', 'F', 'M', 'F'],
        'age_group': ['25-35', '25-35', '35-45', '35-45']
    })


@pytest.fixture
def sample_benchmark_data():
    """Create sample benchmark data."""
    return pd.DataFrame({
        'country': ['United States', 'United States', 'Canada', 'Canada'],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.25, 0.25, 0.25, 0.25]
    })


def test_standardize_survey_data(sample_config, sample_survey_data):
    """Test survey data standardization."""
    standardized = standardize_survey_data(
        sample_survey_data, 
        'test_survey', 
        sample_config
    )
    
    # Check that mappings were applied
    assert 'Male' in standardized['gender'].values
    assert 'Female' in standardized['gender'].values
    assert 'M' not in standardized['gender'].values
    assert 'F' not in standardized['gender'].values
    
    assert 'United States' in standardized['country'].values
    assert 'Canada' in standardized['country'].values
    assert 'USA' not in standardized['country'].values
    assert 'CAN' not in standardized['country'].values


def test_add_regional_dimensions(sample_config):
    """Test adding regional dimensions to data."""
    df = pd.DataFrame({
        'country': ['United States', 'Canada', 'Germany'],
        'value': [1, 2, 3]
    })
    
    result = add_regional_dimensions(df, sample_config)
    
    # Check that regional columns were added
    assert 'region' in result.columns
    assert 'continent' in result.columns
    
    # Check mappings
    us_row = result[result['country'] == 'United States'].iloc[0]
    assert us_row['region'] == 'North America'
    
    canada_row = result[result['country'] == 'Canada'].iloc[0]
    assert canada_row['region'] == 'North America'


def test_aggregate_benchmark_for_dimension(sample_config, sample_benchmark_data):
    """Test benchmark aggregation for different dimensions."""
    # Test country-only dimension
    country_agg = aggregate_benchmark_for_dimension(
        sample_benchmark_data, 
        ['country'], 
        sample_config
    )
    
    assert len(country_agg) == 2  # US and Canada
    assert 'gender' not in country_agg.columns
    
    # Check proportions sum correctly
    us_prop = country_agg[country_agg['country'] == 'United States']['population_proportion'].iloc[0]
    assert abs(us_prop - 0.5) < 1e-10  # 0.25 + 0.25


def test_calculate_gri_for_dimension(sample_config, sample_survey_data, sample_benchmark_data):
    """Test GRI calculation for a specific dimension."""
    # Standardize survey data first
    survey_std = standardize_survey_data(sample_survey_data, 'test_survey', sample_config)
    
    # Get country dimension config
    dimension = sample_config.get_dimension_by_name("Country")
    
    # Calculate scores
    gri_score, diversity_score = calculate_gri_for_dimension(
        survey_std,
        sample_benchmark_data,
        dimension,
        sample_config
    )
    
    # Basic validation
    assert 0.0 <= gri_score <= 1.0
    assert 0.0 <= diversity_score <= 1.0


def test_calculate_gri_scorecard(sample_config, sample_survey_data):
    """Test full scorecard calculation."""
    # Create comprehensive benchmark data
    benchmark_data = {
        'age_gender': pd.DataFrame({
            'country': ['United States', 'United States', 'Canada', 'Canada'],
            'gender': ['Male', 'Female', 'Male', 'Female'],
            'population_proportion': [0.25, 0.25, 0.25, 0.25]
        }),
        'religion': pd.DataFrame({
            'country': ['United States', 'Canada'],
            'religion': ['Christianity', 'Christianity'],
            'population_proportion': [0.5, 0.5]
        })
    }
    
    # Calculate scorecard
    scorecard = calculate_gri_scorecard(
        sample_survey_data,
        benchmark_data,
        survey_source='test_survey',
        use_extended_dimensions=False,
        config=sample_config
    )
    
    # Check structure
    assert 'Dimension' in scorecard.columns
    assert 'GRI Score' in scorecard.columns
    assert 'Diversity Score' in scorecard.columns
    
    # Should have results for standard dimensions that can be calculated
    assert len(scorecard) > 0
    
    # Check that scores are valid
    for _, row in scorecard.iterrows():
        if row['Dimension'] != 'AVERAGE':
            assert 0.0 <= row['GRI Score'] <= 1.0
            assert 0.0 <= row['Diversity Score'] <= 1.0


def test_standardize_survey_data_with_exclusions(sample_config):
    """Test that unmapped segments are excluded."""
    survey_data = pd.DataFrame({
        'country': ['USA', 'Brazil'],  # Brazil not in mapping
        'gender': ['M', 'F'],
        'age_group': ['25-35', '35-45']
    })
    
    standardized = standardize_survey_data(
        survey_data, 
        'test_survey', 
        sample_config
    )
    
    # Brazil should be excluded (no mapping)
    assert 'Brazil' not in standardized['country'].values
    assert len(standardized) == 1  # Only USA row remains


def test_calculate_scorecard_with_extended_dimensions(sample_config, sample_survey_data):
    """Test scorecard with extended dimensions."""
    benchmark_data = {
        'age_gender': pd.DataFrame({
            'country': ['United States', 'United States', 'Canada', 'Canada'],
            'gender': ['Male', 'Female', 'Male', 'Female'],
            'population_proportion': [0.25, 0.25, 0.25, 0.25]
        })
    }
    
    # Calculate with extended dimensions
    scorecard = calculate_gri_scorecard(
        sample_survey_data,
        benchmark_data,
        survey_source='test_survey',
        use_extended_dimensions=True,
        config=sample_config
    )
    
    # Should have more dimensions than standard scorecard
    dimension_names = scorecard['Dimension'].tolist()
    assert 'Country' in dimension_names  # Extended dimension
    
    # Regional dimension should be skipped due to missing mapping validation
    # (our test config has minimal regional data)