#!/usr/bin/env python3
"""
Data processing script for GRI benchmark data.

This script processes raw benchmark demographic data files and creates
standardized benchmark files for GRI calculations across three dimensions:
- Country x Gender x Age
- Country x Religion  
- Country x Environment (Urban/Rural)

Each output file contains strata columns and a 'population_proportion' column
where the sum of proportions equals 1.0.
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List


def load_raw_data() -> Dict[str, pd.DataFrame]:
    """Load all raw benchmark data files."""
    base_path = "data/raw/benchmark_data"
    
    data = {}
    
    # Load UN population data (male and female)
    data['male_pop'] = pd.read_csv(f"{base_path}/WPP_2023_Male_Population.csv")
    data['female_pop'] = pd.read_csv(f"{base_path}/WPP_2023_Female_Population.csv")
    
    # Load religious composition data
    data['religion'] = pd.read_csv(f"{base_path}/GLS_2010_Religious_Composition.csv")
    
    # Load urban/rural data
    data['urban_rural'] = pd.read_csv(f"{base_path}/WUP_2018_Urban_Rural.csv")
    
    return data


def process_country_gender_age(male_df: pd.DataFrame, female_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process UN population data to create Country x Gender x Age benchmark.
    
    Args:
        male_df: Male population data from UN WPP
        female_df: Female population data from UN WPP
        
    Returns:
        DataFrame with columns: country, gender, age_group, population_proportion
    """
    # Filter to get only country-level data (Type == 'Country' or Type == 'Country/Area')
    male_countries = male_df[male_df['Type'].isin(['Country', 'Country/Area'])].copy()
    female_countries = female_df[female_df['Type'].isin(['Country', 'Country/Area'])].copy()
    
    # Define age groups that match Global Dialogues segmentation
    age_columns = ['0-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-34', '35-39', 
                   '40-44', '45-49', '50-54', '55-59', '60-64', '65-69', '70-74', 
                   '75-79', '80-84', '85-89', '90-94', '95-99', '100+']
    
    # Group into broader age categories to match survey data
    age_mapping = {
        '18-25': ['15-19', '20-24'],  # Include 15-19 for approximate 18-25
        '26-35': ['25-29', '30-34'],
        '36-45': ['35-39', '40-44'],
        '46-55': ['45-49', '50-54'],
        '56-65': ['55-59', '60-64'],
        '65+': ['65-69', '70-74', '75-79', '80-84', '85-89', '90-94', '95-99', '100+']
    }
    
    result_rows = []
    
    for _, male_row in male_countries.iterrows():
        country = male_row['Region, subregion, country or area *']
        iso3 = male_row.get('ISO3 Alpha-code', '')
        
        # Find matching female row
        female_row = female_countries[
            female_countries['Region, subregion, country or area *'] == country
        ]
        
        if len(female_row) == 0:
            continue
        female_row = female_row.iloc[0]
        
        # Process each age group
        for age_group, age_cols in age_mapping.items():
            # Sum male population across age columns (handle string formatting with commas/spaces)
            male_pop = 0
            for col in age_cols:
                if col in male_row and pd.notna(male_row[col]):
                    # Convert string numbers with spaces/commas to int
                    val_str = str(male_row[col]).replace(' ', '').replace(',', '')
                    try:
                        male_pop += int(val_str)
                    except (ValueError, TypeError):
                        pass
            
            # Sum female population across age columns
            female_pop = 0
            for col in age_cols:
                if col in female_row and pd.notna(female_row[col]):
                    # Convert string numbers with spaces/commas to int
                    val_str = str(female_row[col]).replace(' ', '').replace(',', '')
                    try:
                        female_pop += int(val_str)
                    except (ValueError, TypeError):
                        pass
            
            # Add rows for male and female
            if male_pop > 0:
                result_rows.append({
                    'country': country,
                    'gender': 'Male',
                    'age_group': age_group,
                    'population': male_pop,
                    'iso3': iso3
                })
            
            if female_pop > 0:
                result_rows.append({
                    'country': country,
                    'gender': 'Female', 
                    'age_group': age_group,
                    'population': female_pop,
                    'iso3': iso3
                })
    
    # Convert to DataFrame and calculate proportions
    df = pd.DataFrame(result_rows)
    if len(df) > 0:
        total_population = df['population'].sum()
        df['population_proportion'] = df['population'] / total_population
        
        # Keep only the required columns
        df = df[['country', 'gender', 'age_group', 'population_proportion']]
    
    return df


def process_country_religion(religion_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process Pew religious composition data to create Country x Religion benchmark.
    
    Args:
        religion_df: Religious composition data from Pew Research
        
    Returns:
        DataFrame with columns: country, religion, population_proportion
    """
    # Map religious categories
    religion_mapping = {
        'Christianity': 'PERCENT CHRISTIAN',
        'Islam': 'PERCENT MUSLIM', 
        'Hinduism': 'PERCENT HINDU',
        'Buddhism': 'PERCENT BUDDHIST',
        'Judaism': 'PERCENT JEWISH',
        'I do not identify with any religious group or faith': 'PERCENT UNAFFIL.',
        'Other religious group': ['PERCENT FOLK RELIGION', 'PERCENT OTHER RELIGION']
    }
    
    result_rows = []
    
    for _, row in religion_df.iterrows():
        country = row['COUNTRY']
        pop_str = str(row['2010 COUNTRY POPULATION']).replace(',', '')
        
        # Handle special cases like '<10,000'
        if '<' in pop_str:
            country_pop = int(pop_str.replace('<', ''))
        else:
            try:
                country_pop = int(pop_str)
            except ValueError:
                continue  # Skip rows with invalid population data
        
        for religion, col_names in religion_mapping.items():
            if isinstance(col_names, list):
                # Sum multiple columns for "Other religious group"
                percent = 0
                for col in col_names:
                    val = row[col]
                    if isinstance(val, str) and '<' in val:
                        percent += 0.05  # Assume <0.1 means 0.05%
                    else:
                        try:
                            percent += float(val)
                        except (ValueError, TypeError):
                            pass
            else:
                val = row[col_names]
                if isinstance(val, str) and '<' in val:
                    percent = 0.05  # Assume <0.1 means 0.05%
                else:
                    try:
                        percent = float(val)
                    except (ValueError, TypeError):
                        percent = 0
            
            if percent > 0:
                population = country_pop * (percent / 100)
                result_rows.append({
                    'country': country,
                    'religion': religion,
                    'population': population
                })
    
    # Convert to DataFrame and calculate proportions
    df = pd.DataFrame(result_rows)
    if len(df) > 0:
        total_population = df['population'].sum()
        df['population_proportion'] = df['population'] / total_population
        
        # Keep only the required columns
        df = df[['country', 'religion', 'population_proportion']]
    
    return df


def process_country_environment(urban_rural_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process UN urban/rural data to create Country x Environment benchmark.
    
    Args:
        urban_rural_df: Urban/rural data from UN WUP
        
    Returns:
        DataFrame with columns: country, environment, population_proportion
    """
    # Filter to get only country-level data (exclude regions and aggregates)
    countries = urban_rural_df[
        ~urban_rural_df['Region, subregion, country or area'].str.contains(
            'region|WORLD|developed|income|countries', case=False, na=False
        )
    ].copy()
    
    result_rows = []
    
    for _, row in countries.iterrows():
        country = row['Region, subregion, country or area']
        
        # Get urban and rural populations (in thousands)
        try:
            urban_pop = float(str(row['Urban (thousands)']).replace(',', '').replace(' ', '')) * 1000
            rural_pop = float(str(row['Rural (thousands)']).replace(',', '').replace(' ', '')) * 1000
        except (ValueError, TypeError):
            continue
            
        if urban_pop > 0:
            result_rows.append({
                'country': country,
                'environment': 'Urban',
                'population': urban_pop
            })
            
        if rural_pop > 0:
            result_rows.append({
                'country': country,
                'environment': 'Rural', 
                'population': rural_pop
            })
    
    # Convert to DataFrame and calculate proportions
    df = pd.DataFrame(result_rows)
    if len(df) > 0:
        total_population = df['population'].sum()
        df['population_proportion'] = df['population'] / total_population
        
        # Keep only the required columns
        df = df[['country', 'environment', 'population_proportion']]
    
    return df


def main():
    """Main processing function."""
    print("Loading raw benchmark data...")
    raw_data = load_raw_data()
    
    # Ensure output directory exists
    os.makedirs("data/processed", exist_ok=True)
    
    print("Processing Country x Gender x Age benchmark...")
    country_gender_age = process_country_gender_age(
        raw_data['male_pop'], 
        raw_data['female_pop']
    )
    
    print("Processing Country x Religion benchmark...")
    country_religion = process_country_religion(raw_data['religion'])
    
    print("Processing Country x Environment benchmark...")
    country_environment = process_country_environment(raw_data['urban_rural'])
    
    # Save processed files
    print("Saving processed benchmark files...")
    
    country_gender_age.to_csv("data/processed/benchmark_country_gender_age.csv", index=False)
    print(f"  - benchmark_country_gender_age.csv: {len(country_gender_age)} strata")
    
    country_religion.to_csv("data/processed/benchmark_country_religion.csv", index=False) 
    print(f"  - benchmark_country_religion.csv: {len(country_religion)} strata")
    
    country_environment.to_csv("data/processed/benchmark_country_environment.csv", index=False)
    print(f"  - benchmark_country_environment.csv: {len(country_environment)} strata")
    
    # Verify proportions sum to 1.0
    print("\nVerifying proportion sums:")
    print(f"  - Country x Gender x Age: {country_gender_age['population_proportion'].sum():.6f}")
    print(f"  - Country x Religion: {country_religion['population_proportion'].sum():.6f}")
    print(f"  - Country x Environment: {country_environment['population_proportion'].sum():.6f}")
    
    print("\nProcessing complete!")


if __name__ == "__main__":
    main()