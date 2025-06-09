import pytest
import pandas as pd
from gri.calculator import calculate_gri, calculate_diversity_score


def test_gri_perfect_match():
    """Test GRI calculation when sample perfectly matches benchmark."""
    # Create survey data
    survey_df = pd.DataFrame({
        'country': ['USA', 'USA', 'Canada', 'Canada'],
        'gender': ['Male', 'Female', 'Male', 'Female']
    })
    
    # Create benchmark data that matches the survey proportions exactly
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'USA', 'Canada', 'Canada'],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.25, 0.25, 0.25, 0.25]
    })
    
    gri = calculate_gri(survey_df, benchmark_df, ['country', 'gender'])
    assert gri == 1.0


def test_gri_complete_mismatch():
    """Test GRI calculation when sample has no overlap with benchmark."""
    # Create survey data
    survey_df = pd.DataFrame({
        'country': ['USA', 'USA'],
        'gender': ['Male', 'Male']
    })
    
    # Create benchmark data with completely different strata
    benchmark_df = pd.DataFrame({
        'country': ['Canada', 'Canada'],
        'gender': ['Female', 'Female'],
        'population_proportion': [0.5, 0.5]
    })
    
    gri = calculate_gri(survey_df, benchmark_df, ['country', 'gender'])
    assert gri == 0.0


def test_gri_partial_match():
    """Test GRI calculation with a realistic partial match scenario."""
    # Create survey data - 3 USA participants, 1 Canada participant
    survey_df = pd.DataFrame({
        'country': ['USA', 'USA', 'USA', 'Canada'],
        'gender': ['Male', 'Male', 'Female', 'Male']
    })
    
    # Create benchmark data - should be 50/50 split
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'USA', 'Canada', 'Canada'],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'population_proportion': [0.25, 0.25, 0.25, 0.25]
    })
    
    gri = calculate_gri(survey_df, benchmark_df, ['country', 'gender'])
    
    # Calculate expected GRI manually:
    # Sample proportions: USA/Male=0.5, USA/Female=0.25, Canada/Male=0.25, Canada/Female=0
    # Benchmark proportions: all are 0.25
    # Absolute differences: |0.5-0.25| + |0.25-0.25| + |0.25-0.25| + |0-0.25| = 0.25 + 0 + 0 + 0.25 = 0.5
    # TVD = 0.5 * 0.5 = 0.25
    # GRI = 1 - 0.25 = 0.75
    assert abs(gri - 0.75) < 1e-10


def test_gri_empty_survey():
    """Test that empty survey returns GRI of 0.0."""
    # Empty survey
    survey_df = pd.DataFrame(columns=['country', 'gender'])
    
    # Benchmark data
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female'],
        'population_proportion': [0.5, 0.5]
    })
    
    gri = calculate_gri(survey_df, benchmark_df, ['country', 'gender'])
    assert gri == 0.0


def test_diversity_score_full_coverage():
    """Test diversity score with full coverage of relevant strata."""
    # Survey data covering all relevant strata
    survey_df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male']
    })
    
    # Benchmark data with all strata above threshold
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male'],
        'population_proportion': [0.4, 0.4, 0.2]  # All above 0.00001 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    assert diversity_score == 1.0


def test_diversity_score_partial_coverage():
    """Test diversity score with partial coverage."""
    # Survey data with 100 participants covering only 2 out of 3 relevant strata
    # Threshold X = 1/(2*100) = 0.005
    survey_df = pd.DataFrame({
        'country': ['USA'] * 50 + ['Canada'] * 50,
        'gender': ['Male'] * 50 + ['Female'] * 50
    })
    
    # Benchmark data with 3 relevant strata (all > 0.005)
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male'],
        'population_proportion': [0.4, 0.4, 0.2]  # All above 0.005 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    # 2 represented relevant strata out of 3 relevant strata: 2/3
    assert abs(diversity_score - (2/3)) < 1e-10


def test_diversity_score_zero_coverage():
    """Test diversity score with no coverage of relevant strata."""
    # Survey data with 100 participants in different strata than benchmark
    # Threshold X = 1/(2*100) = 0.005
    survey_df = pd.DataFrame({
        'country': ['Brazil'] * 100,
        'gender': ['Male'] * 100
    })
    
    # Benchmark data with different relevant strata (all > 0.005)
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada'],
        'gender': ['Male', 'Female'],
        'population_proportion': [0.5, 0.5]  # Both above 0.005 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    # 0 represented relevant strata out of 2 relevant strata: 0/2 = 0.0
    assert diversity_score == 0.0


def test_diversity_score_threshold_filtering():
    """Test that strata below threshold are excluded from diversity calculation."""
    # Survey with 100 participants, covering one stratum
    survey_df = pd.DataFrame({
        'country': ['USA'] * 100,
        'gender': ['Male'] * 100
    })
    
    # Benchmark with one relevant and one irrelevant stratum
    # With N=100, threshold X = 1/(2*100) = 0.005
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Micronesia'],
        'gender': ['Male', 'Female'],
        'population_proportion': [0.5, 0.001]  # Second below 0.005 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    # Only 1 relevant stratum (USA/Male), and it's covered, so score should be 1.0
    assert diversity_score == 1.0


def test_diversity_score_no_relevant_strata():
    """Test diversity score when no strata meet the threshold."""
    # Survey with 10 participants, threshold X = 1/(2*10) = 0.05
    survey_df = pd.DataFrame({
        'country': ['USA'] * 10,
        'gender': ['Male'] * 10
    })
    
    # Benchmark with all strata below threshold
    benchmark_df = pd.DataFrame({
        'country': ['Micronesia', 'Vatican'],
        'gender': ['Male', 'Female'],
        'population_proportion': [0.01, 0.005]  # Both below 0.05 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    assert diversity_score == 1.0  # Perfect coverage of empty relevant set


def test_diversity_score_dynamic_threshold():
    """Test that diversity score uses dynamic threshold X = 1/(2N)."""
    # Survey with 200 participants covering 2 strata, threshold X = 1/(2*200) = 0.0025
    survey_df = pd.DataFrame({
        'country': ['USA'] * 100 + ['Canada'] * 100,
        'gender': ['Male'] * 100 + ['Female'] * 100
    })
    
    # Benchmark with 3 strata: 2 above threshold, 1 below
    benchmark_df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Micronesia'],
        'gender': ['Male', 'Female', 'Male'],
        'population_proportion': [0.4, 0.4, 0.002]  # Third below 0.0025 threshold
    })
    
    diversity_score = calculate_diversity_score(survey_df, benchmark_df, ['country', 'gender'])
    # 2 relevant strata (USA/Male, Canada/Female), both covered: 2/2 = 1.0
    assert diversity_score == 1.0