#!/usr/bin/env python3
"""
Debug script to analyze regional mapping coverage issues.
"""

import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.config import GRIConfig
from scripts.process_data_core import load_raw_data, process_country_gender_age

def analyze_country_coverage():
    """Analyze which countries are missing from regional mappings."""
    print("Regional Mapping Coverage Analysis")
    print("=" * 50)
    
    # Load configuration
    config = GRIConfig()
    
    # Load raw data to see what countries we have
    print("Loading raw data...")
    raw_data = load_raw_data()
    
    # Process baseline country data
    country_benchmark = process_country_gender_age(raw_data['male_pop'], raw_data['female_pop'])
    
    # Get unique countries from benchmark data
    benchmark_countries = set(country_benchmark['country'].unique())
    print(f"Countries in benchmark data: {len(benchmark_countries)}")
    
    # Get countries in regional mapping
    region_mapping = config.get_country_to_region_mapping()
    mapped_countries = set(region_mapping.keys())
    print(f"Countries in regional mapping: {len(mapped_countries)}")
    
    # Find missing countries
    missing_countries = benchmark_countries - mapped_countries
    extra_mapped = mapped_countries - benchmark_countries
    
    print(f"\nCountries in benchmark but missing from regional mapping: {len(missing_countries)}")
    if missing_countries:
        print("Missing countries (first 20):")
        for country in sorted(list(missing_countries)[:20]):
            print(f"  - {country}")
        if len(missing_countries) > 20:
            print(f"  ... and {len(missing_countries) - 20} more")
    
    print(f"\nCountries in mapping but not in benchmark: {len(extra_mapped)}")
    if extra_mapped:
        print("Extra mapped countries (first 10):")
        for country in sorted(list(extra_mapped)[:10]):
            print(f"  - {country}")
    
    # Calculate coverage
    coverage = len(benchmark_countries & mapped_countries) / len(benchmark_countries) * 100
    print(f"\nRegional mapping coverage: {coverage:.1f}%")
    
    # Analyze population impact
    print("\nPopulation impact analysis...")
    
    # Create country mapping
    country_benchmark['region'] = country_benchmark['country'].map(region_mapping)
    
    # Calculate what proportion of population is covered
    total_population = country_benchmark['population_proportion'].sum()
    covered_population = country_benchmark.dropna(subset=['region'])['population_proportion'].sum()
    
    print(f"Total population proportion: {total_population:.6f}")
    print(f"Covered population proportion: {covered_population:.6f}")
    print(f"Population coverage: {covered_population/total_population*100:.1f}%")
    
    # Show largest missing countries by population
    missing_countries_df = country_benchmark[country_benchmark['region'].isna()]
    if len(missing_countries_df) > 0:
        missing_by_pop = missing_countries_df.groupby('country')['population_proportion'].sum().sort_values(ascending=False)
        print(f"\nLargest missing countries by population (top 10):")
        for country, pop in missing_by_pop.head(10).items():
            print(f"  {country}: {pop:.6f} ({pop/total_population*100:.1f}% of total)")
    
    return coverage, covered_population/total_population

def analyze_continent_coverage():
    """Analyze continental mapping coverage."""
    print("\n" + "=" * 50)
    print("Continental Mapping Coverage Analysis")
    print("=" * 50)
    
    config = GRIConfig()
    raw_data = load_raw_data()
    country_benchmark = process_country_gender_age(raw_data['male_pop'], raw_data['female_pop'])
    
    benchmark_countries = set(country_benchmark['country'].unique())
    continent_mapping = config.get_country_to_continent_mapping()
    mapped_countries = set(continent_mapping.keys())
    
    missing_countries = benchmark_countries - mapped_countries
    coverage = len(benchmark_countries & mapped_countries) / len(benchmark_countries) * 100
    
    print(f"Continental mapping coverage: {coverage:.1f}%")
    print(f"Missing countries: {len(missing_countries)}")
    
    # Population impact
    country_benchmark['continent'] = country_benchmark['country'].map(continent_mapping)
    total_population = country_benchmark['population_proportion'].sum()
    covered_population = country_benchmark.dropna(subset=['continent'])['population_proportion'].sum()
    
    print(f"Population coverage: {covered_population/total_population*100:.1f}%")
    
    return coverage, covered_population/total_population

def suggest_fixes():
    """Suggest ways to fix the coverage issues."""
    print("\n" + "=" * 50)
    print("Suggested Fixes")
    print("=" * 50)
    
    print("1. Add missing countries to regional mappings in config/regions.yaml")
    print("2. Use country name standardization/mapping")
    print("3. Renormalize regional proportions after aggregation")
    print("4. Use fallback mapping for unmapped countries")

if __name__ == "__main__":
    try:
        region_coverage, region_pop_coverage = analyze_country_coverage()
        continent_coverage, continent_pop_coverage = analyze_continent_coverage()
        suggest_fixes()
        
        print(f"\nSummary:")
        print(f"Regional coverage: {region_coverage:.1f}% countries, {region_pop_coverage*100:.1f}% population")
        print(f"Continental coverage: {continent_coverage:.1f}% countries, {continent_pop_coverage*100:.1f}% population")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()