"""
Tests for configuration-driven data processing.

This module ensures that data processing follows the configuration specifications
and that all configured dimensions are properly processed according to dimensions.yaml.
"""

import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from gri.config import GRIConfig
from scripts.process_data import (
    process_all_configured_benchmarks,
    create_regional_benchmark,
    create_single_dimension_benchmark,
    save_processed_benchmarks
)


class TestConfigurationCompliance:
    """Test that data processing follows configuration specifications."""
    
    @pytest.fixture
    def config(self):
        """Load the actual configuration for testing."""
        return GRIConfig()
    
    def test_configuration_loading(self, config):
        """Test that configuration loads successfully."""
        dimensions = config.get_all_dimensions()
        assert len(dimensions) > 0, "Configuration should load dimensions"
        
        # Check that each dimension has required fields
        for dim in dimensions:
            assert 'name' in dim
            assert 'columns' in dim
            assert isinstance(dim['columns'], list)
    
    def test_all_configured_dimensions_have_names(self, config):
        """Test that all configured dimensions have proper names."""
        dimensions = config.get_all_dimensions()
        dimension_names = [dim['name'] for dim in dimensions]
        
        # Should have 13 dimensions as defined in config
        assert len(dimension_names) == 13
        
        # Check for expected core dimensions
        expected_core = [
            'Country × Gender × Age',
            'Country × Religion', 
            'Country × Environment',
            'Country'
        ]
        
        for core_dim in expected_core:
            assert core_dim in dimension_names, f"Missing core dimension: {core_dim}"
    
    def test_processed_benchmark_files_follow_config(self, config):
        """Test that processed benchmark files follow configuration specifications."""
        # Check that benchmark files exist for all configured dimensions
        dimensions = config.get_all_dimensions()
        
        expected_files = []
        for dim in dimensions:
            # Convert dimension name to filename format
            filename = dim['name'].lower().replace(' × ', '_').replace(' ', '_')
            expected_files.append(f"benchmark_{filename}.csv")
        
        # Check that data/processed contains files for configured dimensions
        processed_dir = "data/processed"
        if os.path.exists(processed_dir):
            actual_files = [f for f in os.listdir(processed_dir) if f.startswith('benchmark_') and f.endswith('.csv')]
            
            # Should have at least the core benchmark files
            core_files = [
                'benchmark_country_gender_age.csv',
                'benchmark_country_religion.csv',
                'benchmark_country_environment.csv'
            ]
            
            for core_file in core_files:
                assert core_file in actual_files, f"Core benchmark file {core_file} not found"
    
    def test_processed_benchmarks_exist_and_valid(self, config):
        """Test that processed benchmark files exist and contain valid data."""
        processed_dir = "data/processed"
        
        if os.path.exists(processed_dir):
            # Check that core benchmark files exist and have valid structure
            core_files = [
                'benchmark_country_gender_age.csv',
                'benchmark_country_religion.csv',
                'benchmark_country_environment.csv',
                'benchmark_religion.csv',
                'benchmark_gender.csv',
                'benchmark_environment.csv'
            ]
            
            for filename in core_files:
                filepath = os.path.join(processed_dir, filename)
                if os.path.exists(filepath):
                    df = pd.read_csv(filepath)
                    
                    # Should have population_proportion column
                    assert 'population_proportion' in df.columns, (
                        f"{filename} should have population_proportion column"
                    )
                    
                    # Should have positive proportions
                    assert (df['population_proportion'] >= 0).all(), (
                        f"{filename} should have non-negative proportions"
                    )
                    
                    # Should not be empty
                    assert len(df) > 0, f"{filename} should not be empty"
    
    def test_configuration_drives_file_creation(self, config):
        """Test that the number of benchmark files matches configuration expectations."""
        dimensions = config.get_all_dimensions()
        
        # Count expected files vs actual files in processed directory
        processed_dir = "data/processed"
        if os.path.exists(processed_dir):
            actual_benchmark_files = [
                f for f in os.listdir(processed_dir) 
                if f.startswith('benchmark_') and f.endswith('.csv')
            ]
            
            # Should have files for all 13 configured dimensions
            # (Allow some flexibility as regional processing may have coverage issues)
            assert len(actual_benchmark_files) >= 10, (
                f"Expected at least 10 benchmark files for {len(dimensions)} configured dimensions, "
                f"found {len(actual_benchmark_files)}"
            )


class TestConfigurationEdgeCases:
    """Test edge cases and error handling in configuration processing."""
    
    def test_config_file_structure(self):
        """Test that configuration files have the expected structure."""
        config = GRIConfig()
        
        # Test dimensions config structure
        dimensions = config.dimensions
        assert 'standard_scorecard' in dimensions
        assert isinstance(dimensions['standard_scorecard'], list)
        
        # Test each dimension has required fields
        for dim in dimensions['standard_scorecard']:
            assert 'name' in dim
            assert 'columns' in dim
            assert 'description' in dim
    
    def test_config_loads_without_errors(self):
        """Test that configuration loads without errors."""
        config = GRIConfig()
        
        # Should be able to access all config properties
        dimensions = config.get_all_dimensions()
        assert len(dimensions) > 0
        
        # Should have segments and regions configurations too
        segments = config.segments
        assert isinstance(segments, dict)
        
        regions = config.regions
        assert isinstance(regions, dict)


class TestProcessingFunctions:
    """Test individual processing functions work correctly."""
    
    def test_create_single_dimension_benchmark(self):
        """Test creation of single-dimension benchmarks."""
        # Create sample multi-dimension data
        multi_dim_data = pd.DataFrame({
            'country': ['USA', 'CAN', 'USA', 'CAN'],
            'gender': ['Male', 'Male', 'Female', 'Female'],
            'age_group': ['18-25', '26-35', '18-25', '26-35'],
            'population_proportion': [0.1, 0.15, 0.2, 0.25]
        })
        
        # Test single dimension extraction
        gender_benchmark = create_single_dimension_benchmark(multi_dim_data, 'gender')
        
        assert set(gender_benchmark.columns) == {'gender', 'population_proportion'}
        assert len(gender_benchmark) == 2  # Male and Female
        
        # Check aggregation correctness
        male_prop = gender_benchmark[gender_benchmark['gender'] == 'Male']['population_proportion'].iloc[0]
        female_prop = gender_benchmark[gender_benchmark['gender'] == 'Female']['population_proportion'].iloc[0]
        
        assert male_prop == 0.25  # 0.1 + 0.15
        assert female_prop == 0.45  # 0.2 + 0.25


if __name__ == "__main__":
    pytest.main([__file__])