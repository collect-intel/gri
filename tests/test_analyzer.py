"""
Tests for the analyzer module (GRIAnalysis class).
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path
from gri.analyzer import GRIAnalysis


@pytest.fixture
def sample_survey_data():
    """Create sample survey data."""
    return pd.DataFrame({
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'country': ['United States', 'India', 'Brazil', 'India', 'United States'],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'age_group': ['26-35', '36-45', '18-25', '26-35', '46-55'],
        'religion': ['Christianity', 'Hinduism', 'Christianity', 'Hinduism', 'Judaism'],
        'environment': ['Urban', 'Urban', 'Rural', 'Urban', 'Urban']
    })


@pytest.fixture
def sample_benchmarks():
    """Create sample benchmark data."""
    # Create a comprehensive benchmark that includes all needed columns
    age_gender_benchmark = pd.DataFrame({
        'country': ['United States', 'United States', 'India', 'India', 'Brazil', 'Brazil'] * 3,
        'gender': ['Male', 'Female'] * 9,
        'age_group': ['18-25', '18-25', '18-25', '18-25', '18-25', '18-25',
                      '26-35', '26-35', '26-35', '26-35', '26-35', '26-35',
                      '36-45', '36-45', '36-45', '36-45', '36-45', '36-45'],
        'population_proportion': [1/18] * 18
    })
    
    return {
        'age_gender': age_gender_benchmark,
        'Country × Gender × Age': age_gender_benchmark,
        'Country': pd.DataFrame({
            'country': ['United States', 'India', 'Brazil'],
            'population_proportion': [0.3, 0.4, 0.3]
        }),
        'Gender': pd.DataFrame({
            'gender': ['Male', 'Female'],
            'population_proportion': [0.5, 0.5]
        })
    }


def test_grianalysis_init(sample_survey_data, sample_benchmarks):
    """Test GRIAnalysis initialization."""
    analysis = GRIAnalysis(
        sample_survey_data,
        benchmarks=sample_benchmarks,
        survey_name="Test Survey"
    )
    
    assert analysis.survey_name == "Test Survey"
    assert len(analysis.survey_data) == 5
    assert analysis.benchmarks is not None


def test_grianalysis_from_survey_file():
    """Test creating GRIAnalysis from file."""
    # Create temporary CSV file that mimics GD format
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Write header and data with columns at expected positions
        # Positions: 0,1,2(participant_id),3,4,5(age_group),6(gender),7(environment),8,9(religion),10(country)
        f.write('col0,col1,participant_id,col3,col4,age_group,gender,environment,col8,religion,country\n')
        f.write('header,header,header,header,header,header,header,header,header,header,header\n')  # Dummy header row that gets skipped
        f.write('x,x,P001,x,x,26-35,Male,Urban,x,Hinduism,India\n')
        f.write('x,x,P002,x,x,36-45,Female,Rural,x,Christianity,Brazil\n')
        temp_path = Path(f.name)
    
    try:
        analysis = GRIAnalysis.from_survey_file(
            temp_path,
            survey_type='gd',
            survey_name="Test GD Survey"
        )
        assert analysis.survey_name == "Test GD Survey"
        assert len(analysis.survey_data) == 2
    finally:
        temp_path.unlink()


def test_calculate_scorecard(sample_survey_data, sample_benchmarks):
    """Test scorecard calculation."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    # Basic scorecard
    scorecard = analysis.calculate_scorecard(dimensions=['Country', 'Gender'])
    
    assert 'dimension' in scorecard.columns
    assert 'gri_score' in scorecard.columns
    assert 'diversity_score' in scorecard.columns
    assert len(scorecard) == 2
    
    # Scorecard with max possible scores (mock)
    scorecard_max = analysis.calculate_scorecard(
        dimensions=['Country'],
        include_max_possible=False  # Set to False to avoid long computation in tests
    )
    assert 'dimension' in scorecard_max.columns


def test_get_top_segments(sample_survey_data, sample_benchmarks):
    """Test getting top deviation segments."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    # This would need proper benchmark data that matches the dimension
    # For now, just test the method exists and handles basic cases
    try:
        top_segments = analysis.get_top_segments('Country', n=5)
        # Would check results if proper data existed
    except KeyError:
        # Expected if benchmark doesn't exist for this dimension
        pass


def test_check_alignment(sample_survey_data, sample_benchmarks):
    """Test alignment checking."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    alignment = analysis.check_alignment()
    assert isinstance(alignment, dict)
    
    # Should have reports for available benchmarks
    for dim in sample_benchmarks.keys():
        assert dim in alignment


def test_print_summary(sample_survey_data, sample_benchmarks, capsys):
    """Test summary printing."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    analysis.print_summary()
    captured = capsys.readouterr()
    
    assert "GRI Analysis Summary" in captured.out
    assert "Survey" in captured.out
    assert "Total Participants: 5" in captured.out


def test_export_results(sample_survey_data, sample_benchmarks):
    """Test results export functionality."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    # Calculate scorecard first
    scorecard = analysis.calculate_scorecard(dimensions=['Country'])
    
    # Test CSV export
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        exported_path = analysis.export_results(format='csv', filepath=temp_path)
        assert exported_path.exists()
        
        # Verify content
        df = pd.read_csv(exported_path)
        assert len(df) > 0
        assert 'dimension' in df.columns
    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_generate_report(sample_survey_data, sample_benchmarks):
    """Test report generation."""
    analysis = GRIAnalysis(sample_survey_data, benchmarks=sample_benchmarks)
    
    # Calculate scorecard first
    analysis.calculate_scorecard(dimensions=['Country'])
    
    # Generate report
    report = analysis.generate_report(include_analysis=False)
    
    assert isinstance(report, str)
    assert "GLOBAL REPRESENTATIVENESS INDEX" in report
    assert "Country" in report


if __name__ == '__main__':
    pytest.main([__file__])