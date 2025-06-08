import pandas as pd
from typing import List


def load_data(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Loads data from a specified file path into a pandas DataFrame.
    
    Args:
        filepath (str): Path to the CSV file to load
        **kwargs: Additional keyword arguments to pass to pd.read_csv
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        FileNotFoundError: If the specified file does not exist
    """
    try:
        df = pd.read_csv(filepath, **kwargs)
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")


def aggregate_data(df: pd.DataFrame, strata_cols: List[str]) -> pd.DataFrame:
    """
    Aggregates a DataFrame to count occurrences in each stratum.
    
    Args:
        df (pd.DataFrame): Input DataFrame to aggregate
        strata_cols (List[str]): List of column names that define the strata
        
    Returns:
        pd.DataFrame: DataFrame with strata_cols and a 'count' column
    """
    # Group the DataFrame by the strata_cols
    grouped = df.groupby(strata_cols)
    
    # Calculate the size of each group and reset the index
    aggregated = grouped.size().reset_index()
    
    # Rename the resulting size column to 'count'
    aggregated = aggregated.rename(columns={0: 'count'})
    
    return aggregated