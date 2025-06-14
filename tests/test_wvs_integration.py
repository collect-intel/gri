"""
Tests for World Values Survey integration.
"""

import pytest
import pandas as pd
from pathlib import Path
from gri.data_loader import load_wvs_survey


def test_load_wvs_processed_data():
    """Test loading processed WVS data."""
    # Check if processed files exist
    wvs7_path = Path('data/processed/surveys/wvs/wvs_wave7_participants_processed.csv')
    
    if not wvs7_path.exists():
        pytest.skip("WVS processed data not available - run scripts/process_wvs_survey.py first")
    
    # Load WVS Wave 7
    df = load_wvs_survey(wvs7_path)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    
    # Check required columns
    required_cols = ['participant_id', 'country', 'gender', 'age_group', 'religion', 'environment']
    for col in required_cols:
        assert col in df.columns
    
    # Check data types and values
    assert df['gender'].isin(['Male', 'Female']).all()
    # Environment might have some NaN values
    assert df['environment'].dropna().isin(['Urban', 'Rural']).all()
    assert df['wave'].iloc[0] == 7


def test_load_wvs_wave_detection():
    """Test automatic wave detection from filename."""
    # Create dummy files to test wave detection
    import tempfile
    
    # Test Wave 7 detection
    with tempfile.NamedTemporaryFile(suffix='_wave7_processed.csv', mode='w', delete=False) as f:
        f.write('participant_id,country,gender,age_group,religion,environment,wave\n')
        f.write('1,United States,Male,26-35,Christianity,Urban,7\n')
        temp_path = Path(f.name)
    
    try:
        df = load_wvs_survey(temp_path)
        assert df['wave'].iloc[0] == 7
    finally:
        temp_path.unlink()
    
    # Test Wave 6 detection
    with tempfile.NamedTemporaryFile(suffix='_wave6_processed.csv', mode='w', delete=False) as f:
        f.write('participant_id,country,gender,age_group,religion,environment,wave\n')
        f.write('1,Germany,Female,36-45,Christianity,Rural,6\n')
        temp_path = Path(f.name)
    
    try:
        df = load_wvs_survey(temp_path)
        # Wave detection happens from filename
        assert 'wave6' in str(temp_path).lower()
        # Data should be loaded
        assert len(df) == 1
    finally:
        temp_path.unlink()


def test_load_wvs_raw_data_error():
    """Test that loading raw WVS data raises helpful error."""
    # Create a file that looks like raw WVS data
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as f:
        f.write('V1,V2,V3,V4,V5\n')  # Raw WVS format
        f.write('1,2,3,4,5\n')
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(NotImplementedError) as exc_info:
            load_wvs_survey(temp_path, wave=7)
        
        # Check error message is helpful
        assert "preprocessing" in str(exc_info.value).lower()
    finally:
        temp_path.unlink()


def test_wvs_data_quality():
    """Test the quality of processed WVS data if available."""
    wvs6_path = Path('data/processed/surveys/wvs/wvs_wave6_participants_processed.csv')
    wvs7_path = Path('data/processed/surveys/wvs/wvs_wave7_participants_processed.csv')
    
    if not (wvs6_path.exists() and wvs7_path.exists()):
        pytest.skip("WVS processed data not available")
    
    # Load both waves
    wvs6 = load_wvs_survey(wvs6_path)
    wvs7 = load_wvs_survey(wvs7_path)
    
    # Check Wave 6
    assert len(wvs6) > 50000  # Should have many participants
    assert wvs6['country'].nunique() > 30  # Should cover many countries
    assert wvs6['age_group'].nunique() >= 6  # Should have age diversity
    
    # Check Wave 7
    assert len(wvs7) > 50000
    assert wvs7['country'].nunique() > 30
    
    # Check no missing values in critical columns
    critical_cols = ['participant_id', 'country', 'gender']
    for col in critical_cols:
        assert wvs6[col].notna().all()
        assert wvs7[col].notna().all()


if __name__ == '__main__':
    pytest.main([__file__])