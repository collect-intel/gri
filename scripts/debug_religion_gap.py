#!/usr/bin/env python3
"""
Debug script to identify the remaining gap in Region × Religion coverage.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.config import GRIConfig
from scripts.process_data_core import load_raw_data, process_country_religion

def analyze_religion_regional_gap():
    """Analyze what's causing the 6.26% gap in regional religion coverage."""
    print("Religion Regional Gap Analysis")
    print("=" * 50)
    
    config = GRIConfig()
    raw_data = load_raw_data()
    
    # Get religion benchmark data
    religion_benchmark = process_country_religion(raw_data['religion'])
    
    print(f"Religion benchmark countries: {len(religion_benchmark['country'].unique())}")
    print(f"Religion benchmark total proportion: {religion_benchmark['population_proportion'].sum():.6f}")
    
    # Get regional mappings
    region_mapping = config.get_country_to_region_mapping()
    
    # Add regional mappings to religion data
    religion_with_regions = religion_benchmark.copy()
    religion_with_regions['region'] = religion_with_regions['country'].map(region_mapping)
    
    # Identify countries without regional mappings
    missing_regions = religion_with_regions[religion_with_regions['region'].isna()]
    
    if len(missing_regions) > 0:
        print(f"\nCountries in religion data missing regional mappings: {len(missing_regions['country'].unique())}")
        
        # Calculate population impact
        missing_pop = missing_regions.groupby('country')['population_proportion'].sum().sort_values(ascending=False)
        total_missing_pop = missing_pop.sum()
        
        print(f"Total population missing from regional aggregation: {total_missing_pop:.6f} ({total_missing_pop*100:.2f}%)")
        
        print(f"\nTop missing countries by population:")
        for country, pop_prop in missing_pop.head(15).items():
            print(f"  {country}: {pop_prop:.6f} ({pop_prop*100:.3f}%)")
            
        return missing_pop
    else:
        print("All countries in religion data have regional mappings!")
        
        # Check if there's a different issue
        regional_religion = religion_with_regions.dropna(subset=['region'])
        regional_total = regional_religion['population_proportion'].sum()
        print(f"Regional religion total: {regional_total:.6f}")
        
        return None

def check_religion_vs_population_countries():
    """Compare countries in religion data vs population data."""
    print("\n" + "=" * 50)
    print("Religion vs Population Country Comparison")
    print("=" * 50)
    
    raw_data = load_raw_data()
    
    # Get countries from population data (this is our reference)
    from scripts.process_data_core import process_country_gender_age
    pop_benchmark = process_country_gender_age(raw_data['male_pop'], raw_data['female_pop'])
    pop_countries = set(pop_benchmark['country'].unique())
    
    # Get countries from religion data
    religion_benchmark = process_country_religion(raw_data['religion'])
    religion_countries = set(religion_benchmark['country'].unique())
    
    print(f"Population data countries: {len(pop_countries)}")
    print(f"Religion data countries: {len(religion_countries)}")
    
    # Find differences
    in_pop_not_religion = pop_countries - religion_countries
    in_religion_not_pop = religion_countries - pop_countries
    
    print(f"\nIn population but not in religion: {len(in_pop_not_religion)}")
    if in_pop_not_religion:
        print("Missing from religion (first 10):")
        for country in sorted(list(in_pop_not_religion)[:10]):
            print(f"  - {country}")
    
    print(f"\nIn religion but not in population: {len(in_religion_not_pop)}")
    if in_religion_not_pop:
        print("Extra in religion (first 10):")
        for country in sorted(list(in_religion_not_pop)[:10]):
            print(f"  - {country}")
    
    # Calculate population impact of missing countries
    if in_pop_not_religion:
        missing_from_religion = pop_benchmark[pop_benchmark['country'].isin(in_pop_not_religion)]
        missing_pop_impact = missing_from_religion.groupby('country')['population_proportion'].sum().sort_values(ascending=False)
        total_impact = missing_pop_impact.sum()
        
        print(f"\nPopulation impact of countries missing from religion data:")
        print(f"Total impact: {total_impact:.6f} ({total_impact*100:.2f}%)")
        
        print("Largest missing countries:")
        for country, pop in missing_pop_impact.head(10).items():
            print(f"  {country}: {pop:.6f} ({pop*100:.3f}%)")

if __name__ == "__main__":
    try:
        missing_countries = analyze_religion_regional_gap()
        check_religion_vs_population_countries()
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()