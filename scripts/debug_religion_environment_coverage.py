#!/usr/bin/env python3
"""
Debug script to analyze religion and environment data coverage.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.config import GRIConfig
from scripts.process_data_core import load_raw_data, process_country_religion, process_country_environment

def analyze_religion_coverage():
    """Analyze religion data coverage."""
    print("Religion Data Coverage Analysis")
    print("=" * 50)
    
    config = GRIConfig()
    raw_data = load_raw_data()
    
    # Check religion data
    religion_benchmark = process_country_religion(raw_data['religion'])
    total_religion_prop = religion_benchmark['population_proportion'].sum()
    
    print(f"Religion benchmark total proportion: {total_religion_prop:.6f}")
    print(f"Religion benchmark countries: {len(religion_benchmark['country'].unique())}")
    
    # Check which countries are missing
    all_countries = set(load_raw_data()['male_pop']['country'].unique())
    religion_countries = set(religion_benchmark['country'].unique())
    
    missing_religion = all_countries - religion_countries
    print(f"Countries missing from religion data: {len(missing_religion)}")
    
    if missing_religion:
        print("Missing countries (first 10):")
        for country in sorted(list(missing_religion)[:10]):
            print(f"  - {country}")
    
    return total_religion_prop

def analyze_environment_coverage():
    """Analyze environment data coverage."""
    print("\n" + "=" * 50)
    print("Environment Data Coverage Analysis")
    print("=" * 50)
    
    raw_data = load_raw_data()
    
    # Check environment data
    environment_benchmark = process_country_environment(raw_data['urban_rural'])
    total_env_prop = environment_benchmark['population_proportion'].sum()
    
    print(f"Environment benchmark total proportion: {total_env_prop:.6f}")
    print(f"Environment benchmark countries: {len(environment_benchmark['country'].unique())}")
    
    # Check which countries are missing
    all_countries = set(raw_data['male_pop']['country'].unique())
    env_countries = set(environment_benchmark['country'].unique())
    
    missing_env = all_countries - env_countries
    print(f"Countries missing from environment data: {len(missing_env)}")
    
    if missing_env:
        print("Missing countries (first 10):")
        for country in sorted(list(missing_env)[:10]):
            print(f"  - {country}")
    
    return total_env_prop

def analyze_raw_data_completeness():
    """Analyze raw data completeness."""
    print("\n" + "=" * 50)
    print("Raw Data Completeness Analysis")
    print("=" * 50)
    
    raw_data = load_raw_data()
    
    print("Dataset sizes:")
    print(f"Male population: {len(raw_data['male_pop'])} rows")
    print(f"Female population: {len(raw_data['female_pop'])} rows")
    print(f"Religion: {len(raw_data['religion'])} rows")
    print(f"Urban/Rural: {len(raw_data['urban_rural'])} rows")
    
    print("\nColumn names by dataset:")
    print(f"Male population columns: {list(raw_data['male_pop'].columns[:5])}...")
    print(f"Religion columns: {list(raw_data['religion'].columns[:5])}...")
    print(f"Urban/Rural columns: {list(raw_data['urban_rural'].columns[:5])}...")
    
    # Look for country identifier columns
    for name, df in raw_data.items():
        country_cols = [col for col in df.columns if 'country' in col.lower() or 'location' in col.lower() or 'name' in col.lower()]
        print(f"{name} potential country columns: {country_cols}")

if __name__ == "__main__":
    try:
        analyze_raw_data_completeness()
        religion_prop = analyze_religion_coverage()
        env_prop = analyze_environment_coverage()
        
        print(f"\nSummary:")
        print(f"Religion data covers {religion_prop*100:.1f}% of global population")
        print(f"Environment data covers {env_prop*100:.1f}% of global population")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()