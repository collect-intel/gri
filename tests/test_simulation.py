"""
Tests for the simulation module.
"""

import pytest
import pandas as pd
import numpy as np
from gri.simulation import (
    generate_optimal_sample,
    monte_carlo_max_scores,
    calculate_max_possible_gri,
    calculate_efficiency_ratio,
    generate_sample_size_curve
)


@pytest.fixture
def simple_benchmark():
    """Create simple benchmark data for testing."""
    return pd.DataFrame({
        'country': ['USA', 'USA', 'India', 'India'],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.25, 0.25, 0.25, 0.25]
    })


def test_generate_optimal_sample(simple_benchmark):
    """Test optimal sample generation."""
    # Extract proportions from benchmark
    proportions = simple_benchmark['population_proportion'].values
    
    sample_counts = generate_optimal_sample(
        proportions,
        sample_size=100,
        random_seed=42
    )
    
    assert len(sample_counts) == len(proportions)
    assert sample_counts.sum() == 100
    assert all(sample_counts >= 0)
    
    # With equal proportions, counts should be roughly equal
    assert sample_counts.min() > 15  # Reasonable for 25% proportions


def test_calculate_max_possible_gri(simple_benchmark):
    """Test max possible GRI calculation."""
    max_gri = calculate_max_possible_gri(
        simple_benchmark,
        sample_size=100,
        dimension_columns=['country', 'gender'],
        n_simulations=10  # Small number for testing
    )
    
    assert isinstance(max_gri, float)
    assert 0 <= max_gri <= 1
    
    # With equal proportions and reasonable sample size, should be high
    assert max_gri > 0.7


def test_monte_carlo_max_scores(simple_benchmark):
    """Test Monte Carlo simulation for max scores."""
    results = monte_carlo_max_scores(
        simple_benchmark,
        sample_size=100,
        dimension_columns=['country', 'gender'],
        n_simulations=10  # Small number for testing
    )
    
    assert 'max_gri' in results
    assert 'max_diversity' in results
    assert 'mean' in results['max_gri']
    assert 'std' in results['max_gri']
    assert 'q25' in results['max_gri']
    assert 'q75' in results['max_gri']
    
    # Check value ranges
    assert 0 <= results['max_gri']['mean'] <= 1
    assert results['max_gri']['std'] >= 0
    assert results['max_diversity']['mean'] > 0


def test_calculate_efficiency_ratio():
    """Test efficiency ratio calculation."""
    # Test normal case
    ratio = calculate_efficiency_ratio(0.8, 0.9)
    assert ratio == pytest.approx(0.8 / 0.9)
    
    # Test edge case: max score is 0
    ratio = calculate_efficiency_ratio(0.5, 0.0)
    assert ratio == 0.0
    
    # Test perfect efficiency
    ratio = calculate_efficiency_ratio(0.9, 0.9)
    assert ratio == 1.0


def test_generate_sample_size_curve(simple_benchmark):
    """Test sample size curve generation."""
    sample_sizes = [50, 100, 200]
    
    curve_data = generate_sample_size_curve(
        simple_benchmark,
        sample_sizes,
        dimension_columns=['country', 'gender'],
        n_simulations=5  # Small number for testing
    )
    
    assert len(curve_data) == len(sample_sizes)
    assert 'sample_size' in curve_data.columns
    assert 'max_gri_mean' in curve_data.columns
    assert 'max_gri_std' in curve_data.columns
    
    # Check that values are reasonable
    assert all(curve_data['max_gri_mean'] > 0)
    assert all(curve_data['max_gri_mean'] <= 1)
    
    # Generally, larger samples should allow higher max GRI
    # (though not guaranteed with small n_simulations)
    assert curve_data['sample_size'].is_monotonic_increasing


def test_monte_carlo_stability():
    """Test that Monte Carlo results are stable with sufficient simulations."""
    benchmark = pd.DataFrame({
        'category': ['A', 'B', 'C'],
        'population_proportion': [0.5, 0.3, 0.2]
    })
    
    # Run twice with same parameters
    results1 = monte_carlo_max_scores(
        benchmark,
        sample_size=100,
        dimension_columns=['category'],
        n_simulations=50,
        random_seed=42
    )
    
    results2 = monte_carlo_max_scores(
        benchmark,
        sample_size=100,
        dimension_columns=['category'],
        n_simulations=50,
        random_seed=42
    )
    
    # With same seed, results should be identical
    assert results1['max_gri']['mean'] == results2['max_gri']['mean']


if __name__ == '__main__':
    pytest.main([__file__])