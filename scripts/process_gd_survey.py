#!/usr/bin/env python3
"""
Global Dialogues Survey Data Processing Script

This script processes raw Global Dialogues survey data files and extracts
the demographic information needed for GRI analysis.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def process_gd_participants(file_path: str) -> pd.DataFrame:
    """
    Process a GD participants CSV file to extract demographic data.
    
    Args:
        file_path: Path to GD participants CSV file
        
    Returns:
        DataFrame with standardized demographic columns
    """
    print(f"Processing: {file_path}")
    
    # Try reading with different CSV parameters for different GD formats
    try:
        # First try normal reading
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Check if this is the problematic single-column format (like GD4)
        if df.shape[1] == 1 and 'Unnamed' in df.columns[0]:
            # Try reading with different separator or quoting
            df = pd.read_csv(file_path, encoding='utf-8', sep='\t')
            if df.shape[1] == 1:
                # Try comma separated with different quoting
                df = pd.read_csv(file_path, encoding='utf-8', quotechar='"', quoting=1)
                if df.shape[1] == 1:
                    print(f"  Warning: Could not parse CSV properly, has only {df.shape[1]} columns")
                    return pd.DataFrame()
        
        # For GD4 which has different column structure, handle it specially
        if file_path.endswith('GD4_participants.csv'):
            return process_gd4_participants_special(df)
        
        # The actual data starts from row 1 (0-indexed), with columns in specific positions
        # Based on the structure observed for GD1-GD3:
        # Column 2: Participant Id
        # Column 5: Age 
        # Column 6: Gender
        # Column 7: Environment (where they live)
        # Column 9: Religion
        # Column 10: Country
        
        # Extract data rows (skip the header row with questions)
        data_rows = df.iloc[1:].copy()
        
        # Extract demographic columns with better error handling
        demographics = pd.DataFrame({
            'participant_id': data_rows.iloc[:, 2] if len(data_rows.columns) > 2 else None,
            'age': data_rows.iloc[:, 5] if len(data_rows.columns) > 5 else None,
            'gender': data_rows.iloc[:, 6] if len(data_rows.columns) > 6 else None,
            'environment': data_rows.iloc[:, 7] if len(data_rows.columns) > 7 else None,
            'religion': data_rows.iloc[:, 9] if len(data_rows.columns) > 9 else None,
            'country': data_rows.iloc[:, 10] if len(data_rows.columns) > 10 else None
        })
        
        # Remove any completely empty rows
        demographics = demographics.dropna(how='all')
        
        # Remove rows where participant_id is empty (these are usually formatting artifacts)
        demographics = demographics[demographics['participant_id'].notna()]
        demographics = demographics[demographics['participant_id'] != '']
        
        # Clean up data
        for col in demographics.columns:
            if col != 'participant_id':
                # Remove quotes and clean up whitespace
                demographics[col] = demographics[col].astype(str).str.strip('"').str.strip()
                # Replace empty strings with NaN
                demographics[col] = demographics[col].replace('', np.nan)
        
        print(f"  Extracted {len(demographics)} participant records")
        return demographics
        
    except Exception as e:
        print(f"  Error processing file: {e}")
        if 'df' in locals():
            print(f"  File has {df.shape[0]} rows and {df.shape[1]} columns")
        return pd.DataFrame()


def process_gd4_participants_special(df: pd.DataFrame) -> pd.DataFrame:
    """
    Special processing for GD4 participants file which has a different format.
    """
    # For GD4, the data appears to be in a different format
    # Let's try to parse it by splitting the single column on whitespace/delimiters
    try:
        # The data might be space-separated or tab-separated in a single column
        all_data = []
        
        for idx, row in df.iterrows():
            if idx == 0:  # Skip header
                continue
            
            # Get the data from the single column and try to split it
            row_data = str(row.iloc[0])
            if row_data and row_data != 'nan':
                # Split on multiple whitespace/tab patterns
                parts = row_data.split()
                if len(parts) >= 11:  # We need at least 11 parts for our data
                    # Extract the demographic fields based on expected positions
                    participant_data = {
                        'participant_id': parts[0] if len(parts) > 0 else None,
                        'age': parts[5] if len(parts) > 5 else None,
                        'gender': parts[6] if len(parts) > 6 else None,
                        'environment': parts[7] if len(parts) > 7 else None,
                        'religion': parts[9] if len(parts) > 9 else None,
                        'country': parts[10] if len(parts) > 10 else None
                    }
                    all_data.append(participant_data)
        
        if all_data:
            demographics = pd.DataFrame(all_data)
            print(f"  Extracted {len(demographics)} participant records (GD4 special format)")
            return demographics
        else:
            print(f"  Could not extract data from GD4 special format")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"  Error in GD4 special processing: {e}")
        return pd.DataFrame()


def standardize_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize demographic values to match GRI configuration expectations.
    """
    df = df.copy()
    
    # Standardize age groups
    age_mapping = {
        '18-25': '18-25',
        '26-35': '26-35', 
        '36-45': '36-45',
        '46-55': '46-55',
        '56-65': '56-65',
        '65+': '65+',
        '65 or older': '65+',
        'Over 65': '65+'
    }
    
    df['age_group'] = df['age'].map(age_mapping)
    
    # Standardize gender
    gender_mapping = {
        'Male': 'Male',
        'Female': 'Female',
        'Man': 'Male',
        'Woman': 'Female'
    }
    
    df['gender'] = df['gender'].map(gender_mapping)
    
    # Standardize environment
    env_mapping = {
        'Urban': 'Urban',
        'Suburban': 'Urban',  # Map suburban to urban for GRI purposes
        'Rural': 'Rural',
        'City': 'Urban',
        'Town': 'Urban',
        'Village': 'Rural',
        'Countryside': 'Rural'
    }
    
    df['environment'] = df['environment'].map(env_mapping)
    
    # Standardize religion - keep original values as they should match config
    # Just clean up common variations
    religion_mapping = {
        'Christianity': 'Christianity',
        'Christian': 'Christianity',
        'Islam': 'Islam',
        'Muslim': 'Islam',
        'Hinduism': 'Hinduism',
        'Hindu': 'Hinduism',
        'Buddhism': 'Buddhism',
        'Buddhist': 'Buddhism',
        'Judaism': 'Judaism',
        'Jewish': 'Judaism',
        'I do not identify with any religious group or faith': 'I do not identify with any religious group or faith',
        'No religion': 'I do not identify with any religious group or faith',
        'Atheist': 'I do not identify with any religious group or faith',
        'Agnostic': 'I do not identify with any religious group or faith',
        'None': 'I do not identify with any religious group or faith',
        'Other': 'Other religious group',
        'Other religious group': 'Other religious group'
    }
    
    df['religion'] = df['religion'].map(religion_mapping)
    
    # Clean up country names - basic standardization
    country_mapping = {
        'United States': 'United States',
        'USA': 'United States',
        'US': 'United States',
        'United States of America': 'United States',
        'UK': 'United Kingdom',
        'Britain': 'United Kingdom',
        'Great Britain': 'United Kingdom'
    }
    
    # Apply country mapping where available, otherwise keep original
    df['country'] = df['country'].apply(lambda x: country_mapping.get(x, x) if pd.notna(x) else x)
    
    # Remove rows with missing key demographics
    df = df.dropna(subset=['country', 'gender', 'age_group'])
    
    return df


def process_all_gd_surveys(base_dir: str = "data/raw/survey_data/global-dialogues/Data") -> dict:
    """
    Process all available GD survey datasets.
    
    Returns:
        Dictionary mapping survey names to processed DataFrames
    """
    survey_data = {}
    
    # Look for GD directories
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Base directory not found: {base_dir}")
        return survey_data
    
    # Process each GD dataset
    for gd_dir in sorted(base_path.glob("GD*")):
        if gd_dir.is_dir():
            survey_name = gd_dir.name
            participants_file = gd_dir / f"{survey_name}_participants.csv"
            
            if participants_file.exists():
                print(f"\nProcessing {survey_name}...")
                
                # Process the participants file
                raw_demographics = process_gd_participants(str(participants_file))
                
                if len(raw_demographics) > 0:
                    # Standardize the demographics
                    standardized = standardize_demographics(raw_demographics)
                    
                    print(f"  Standardized to {len(standardized)} valid records")
                    print(f"  Countries: {standardized['country'].nunique()}")
                    print(f"  Sample countries: {list(standardized['country'].value_counts().head().index)}")
                    
                    survey_data[survey_name] = standardized
                else:
                    print(f"  No valid data extracted from {survey_name}")
            else:
                print(f"  Participants file not found for {survey_name}")
    
    return survey_data


def save_processed_data(survey_data: dict, output_dir: str = "data/processed"):
    """Save processed survey data to output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for survey_name, df in survey_data.items():
        output_file = output_path / f"{survey_name.lower()}_demographics.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved {len(df)} records to {output_file}")


def main():
    """Main processing function."""
    print("Global Dialogues Survey Data Processing")
    print("=" * 50)
    
    # Process all GD surveys
    survey_data = process_all_gd_surveys()
    
    if not survey_data:
        print("No survey data found or processed successfully.")
        return
    
    # Save processed data
    save_processed_data(survey_data)
    
    # Print summary
    print(f"\n" + "=" * 50)
    print("PROCESSING SUMMARY")
    print("=" * 50)
    
    total_participants = sum(len(df) for df in survey_data.values())
    print(f"Total surveys processed: {len(survey_data)}")
    print(f"Total participants: {total_participants:,}")
    
    for survey_name, df in survey_data.items():
        print(f"\n{survey_name}:")
        print(f"  Participants: {len(df):,}")
        print(f"  Countries: {df['country'].nunique()}")
        print(f"  Age groups: {df['age_group'].value_counts().to_dict()}")
        print(f"  Gender: {df['gender'].value_counts().to_dict()}")
        
        # Check data completeness
        completeness = {}
        for col in ['country', 'gender', 'age_group', 'religion', 'environment']:
            completeness[col] = f"{(df[col].notna().sum() / len(df) * 100):.1f}%"
        print(f"  Data completeness: {completeness}")


if __name__ == "__main__":
    main()