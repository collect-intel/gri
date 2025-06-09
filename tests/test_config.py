import pytest
import tempfile
import os
from pathlib import Path
from gri.config import GRIConfig


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory with test config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        
        # Create test dimensions.yaml
        dimensions_content = """
standard_scorecard:
  - name: "Country × Gender × Age"
    columns: ["country", "gender", "age_group"]
    description: "Test dimension"

extended_dimensions:
  - name: "Country"
    columns: ["country"]
    description: "Single country dimension"
  - name: "Region"
    columns: ["region"]
    description: "Regional dimension"
    requires_mapping: ["country_to_region"]
"""
        
        # Create test segments.yaml
        segments_content = """
benchmark_mappings:
  gender:
    "Male": ["Male", "male"]
    "Female": ["Female", "female"]

survey_mappings:
  test_survey:
    gender:
      "Male": ["M"]
      "Female": ["F"]
"""
        
        # Create test regions.yaml
        regions_content = """
country_to_region:
  "North America":
    - "United States"
    - "Canada"
  "Europe":
    - "Germany"
    - "France"

region_to_continent:
  "North America":
    - "North America"
  "Asia":
    - "Europe"
"""
        
        # Write test files
        (config_dir / "dimensions.yaml").write_text(dimensions_content)
        (config_dir / "segments.yaml").write_text(segments_content)
        (config_dir / "regions.yaml").write_text(regions_content)
        
        yield str(config_dir)


def test_config_initialization(temp_config_dir):
    """Test basic configuration initialization."""
    config = GRIConfig(temp_config_dir)
    assert config.config_dir == Path(temp_config_dir)


def test_load_dimensions(temp_config_dir):
    """Test loading dimensions configuration."""
    config = GRIConfig(temp_config_dir)
    
    # Test standard scorecard
    scorecard = config.get_standard_scorecard()
    assert len(scorecard) == 1
    assert scorecard[0]["name"] == "Country × Gender × Age"
    assert scorecard[0]["columns"] == ["country", "gender", "age_group"]
    
    # Test extended dimensions
    extended = config.get_extended_dimensions()
    assert len(extended) == 2
    assert extended[0]["name"] == "Country"
    assert extended[1]["name"] == "Region"


def test_get_dimension_by_name(temp_config_dir):
    """Test retrieving specific dimensions by name."""
    config = GRIConfig(temp_config_dir)
    
    # Test existing dimension
    dim = config.get_dimension_by_name("Country")
    assert dim is not None
    assert dim["columns"] == ["country"]
    
    # Test non-existing dimension
    dim = config.get_dimension_by_name("NonExistent")
    assert dim is None


def test_segment_mappings(temp_config_dir):
    """Test segment mapping retrieval."""
    config = GRIConfig(temp_config_dir)
    
    # Test benchmark mapping
    gender_mapping = config.get_segment_mapping("benchmark_mappings", "gender")
    assert gender_mapping["Male"] == ["Male", "male"]
    assert gender_mapping["Female"] == ["Female", "female"]
    
    # Test survey mapping
    survey_mapping = config.get_segment_mapping("test_survey", "gender")
    assert survey_mapping["Male"] == ["M"]
    assert survey_mapping["Female"] == ["F"]
    
    # Test non-existent mapping
    empty_mapping = config.get_segment_mapping("nonexistent", "gender")
    assert empty_mapping == {}


def test_regional_mappings(temp_config_dir):
    """Test regional mapping functionality."""
    config = GRIConfig(temp_config_dir)
    
    # Test country to region mapping
    country_to_region = config.get_country_to_region_mapping()
    assert country_to_region["United States"] == "North America"
    assert country_to_region["Canada"] == "North America"
    assert country_to_region["Germany"] == "Europe"
    
    # Test region to continent mapping
    region_to_continent = config.get_region_to_continent_mapping()
    assert region_to_continent["North America"] == "North America"


def test_dimension_requirements_validation(temp_config_dir):
    """Test validation of dimension requirements."""
    config = GRIConfig(temp_config_dir)
    
    # Test dimension with satisfied requirements
    region_dim = config.get_dimension_by_name("Region")
    assert config.validate_dimension_requirements(region_dim) == True
    
    # Test dimension without requirements
    country_dim = config.get_dimension_by_name("Country")
    assert config.validate_dimension_requirements(country_dim) == True


def test_file_not_found():
    """Test handling of missing configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = GRIConfig(temp_dir)
        
        with pytest.raises(FileNotFoundError):
            config.dimensions


def test_get_all_dimensions(temp_config_dir):
    """Test getting all dimensions (standard + extended)."""
    config = GRIConfig(temp_config_dir)
    
    all_dims = config.get_all_dimensions()
    assert len(all_dims) == 3  # 1 standard + 2 extended
    
    names = [dim["name"] for dim in all_dims]
    assert "Country × Gender × Age" in names
    assert "Country" in names
    assert "Region" in names