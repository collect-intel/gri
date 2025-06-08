import pytest
import pandas as pd
import tempfile
import os
from gri.utils import load_data, aggregate_data


def test_load_data_success():
    """Test successful loading of CSV data."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age,city\n")
        f.write("Alice,25,NYC\n")
        f.write("Bob,30,LA\n")
        temp_path = f.name
    
    try:
        # Load the data
        df = load_data(temp_path)
        
        # Check the result
        expected_df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'age': [25, 30],
            'city': ['NYC', 'LA']
        })
        
        pd.testing.assert_frame_equal(df, expected_df)
    finally:
        # Clean up
        os.unlink(temp_path)


def test_load_data_with_kwargs():
    """Test loading data with additional pandas kwargs."""
    # Create a temporary CSV file with custom separator
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name;age;city\n")
        f.write("Alice;25;NYC\n")
        f.write("Bob;30;LA\n")
        temp_path = f.name
    
    try:
        # Load the data with custom separator
        df = load_data(temp_path, sep=';')
        
        # Check the result
        expected_df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'age': [25, 30],
            'city': ['NYC', 'LA']
        })
        
        pd.testing.assert_frame_equal(df, expected_df)
    finally:
        # Clean up
        os.unlink(temp_path)


def test_load_data_file_not_found():
    """Test that FileNotFoundError is raised for non-existent files."""
    with pytest.raises(FileNotFoundError, match="File not found: /nonexistent/file.csv"):
        load_data("/nonexistent/file.csv")


def test_aggregate_data():
    """Test basic aggregation functionality."""
    # Create test data
    df = pd.DataFrame({
        'country': ['USA', 'USA', 'Canada', 'Canada', 'USA'],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male'],
        'other_col': [1, 2, 3, 4, 5]
    })
    
    # Aggregate by country and gender
    result = aggregate_data(df, ['country', 'gender'])
    
    # Expected result
    expected = pd.DataFrame({
        'country': ['Canada', 'Canada', 'USA', 'USA'],
        'gender': ['Female', 'Male', 'Female', 'Male'],
        'count': [1, 1, 1, 2]
    })
    
    # Sort both dataframes to ensure consistent order for comparison
    result = result.sort_values(['country', 'gender']).reset_index(drop=True)
    expected = expected.sort_values(['country', 'gender']).reset_index(drop=True)
    
    pd.testing.assert_frame_equal(result, expected)


def test_aggregate_data_single_column():
    """Test aggregation with a single grouping column."""
    df = pd.DataFrame({
        'country': ['USA', 'USA', 'Canada', 'Canada', 'USA'],
        'value': [1, 2, 3, 4, 5]
    })
    
    result = aggregate_data(df, ['country'])
    
    expected = pd.DataFrame({
        'country': ['Canada', 'USA'],
        'count': [2, 3]
    })
    
    # Sort for consistent comparison
    result = result.sort_values('country').reset_index(drop=True)
    expected = expected.sort_values('country').reset_index(drop=True)
    
    pd.testing.assert_frame_equal(result, expected)


def test_aggregate_data_empty_dataframe():
    """Test aggregation with empty DataFrame."""
    df = pd.DataFrame(columns=['country', 'gender'])
    
    result = aggregate_data(df, ['country', 'gender'])
    
    expected = pd.DataFrame(columns=['country', 'gender', 'count'])
    # Convert columns to appropriate dtypes since empty DataFrames may have different dtypes
    expected['count'] = expected['count'].astype('int64')
    
    pd.testing.assert_frame_equal(result, expected)


def test_aggregate_data_all_unique():
    """Test aggregation where each row is unique."""
    df = pd.DataFrame({
        'country': ['USA', 'Canada', 'Mexico'],
        'gender': ['Male', 'Female', 'Male']
    })
    
    result = aggregate_data(df, ['country', 'gender'])
    
    expected = pd.DataFrame({
        'country': ['Canada', 'Mexico', 'USA'],
        'gender': ['Female', 'Male', 'Male'],
        'count': [1, 1, 1]
    })
    
    # Sort for consistent comparison
    result = result.sort_values(['country', 'gender']).reset_index(drop=True)
    expected = expected.sort_values(['country', 'gender']).reset_index(drop=True)
    
    pd.testing.assert_frame_equal(result, expected)