#!/usr/bin/env python3
"""
Demonstration script for the GRI configuration system.

This script shows how to use the new configuration-based GRI calculation
system for flexible dimension management and survey integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from gri import calculate_gri_scorecard, load_data
from gri.config import GRIConfig


def main():
    """Demonstrate the configuration system capabilities."""
    print("=" * 60)
    print("GRI Configuration System Demonstration")
    print("=" * 60)
    
    # Load configuration
    config = GRIConfig()
    
    print("\n1. CONFIGURATION OVERVIEW")
    print("-" * 30)
    
    # Show standard scorecard dimensions
    print("Standard Scorecard Dimensions:")
    for dim in config.get_standard_scorecard():
        print(f"  • {dim['name']}: {dim['columns']}")
    
    # Show extended dimensions
    extended_dims = config.get_extended_dimensions()
    if extended_dims:
        print(f"\nExtended Dimensions Available: {len(extended_dims)}")
        for dim in extended_dims[:5]:  # Show first 5
            print(f"  • {dim['name']}: {dim['columns']}")
    else:
        print(f"\nExtended Dimensions Available: 0")
        print("  (All common dimensions are now part of standard scorecard)")
    
    print("\n2. SEGMENT MAPPINGS")
    print("-" * 30)
    
    # Show some segment mappings
    gender_mapping = config.get_segment_mapping("benchmark_mappings", "gender")
    print("Gender mappings (benchmark → GRI):")
    for standard, sources in gender_mapping.items():
        print(f"  {standard} ← {sources}")
    
    print("\n3. REGIONAL HIERARCHIES")
    print("-" * 30)
    
    # Show regional mappings
    country_to_region = config.get_country_to_region_mapping()
    sample_countries = list(country_to_region.keys())[:5]
    print("Sample country → region mappings:")
    for country in sample_countries:
        region = country_to_region[country]
        print(f"  {country} → {region}")
    
    print("\n4. DEMO CALCULATION")
    print("-" * 30)
    
    try:
        # Create sample data for demonstration
        np.random.seed(42)
        sample_survey = pd.DataFrame({
            'country': np.random.choice([
                'United States', 'Canada', 'Germany', 'France', 
                'Japan', 'Brazil', 'India', 'Nigeria'
            ], 200),
            'gender': np.random.choice(['Male', 'Female'], 200),
            'age_group': np.random.choice([
                '18-25', '26-35', '36-45', '46-55', '56-65', '65+'
            ], 200),
            'religion': np.random.choice([
                'Christianity', 'Islam', 'Hinduism', 'Buddhism', 
                'Judaism', 'I do not identify with any religious group or faith'
            ], 200),
            'environment': np.random.choice(['Urban', 'Rural'], 200)
        })
        
        # Load benchmark data using configuration
        config = GRIConfig()
        standard_dimensions = config.get_standard_scorecard()
        
        benchmark_data = {}
        for dimension in standard_dimensions:
            # Convert dimension name to filename and key
            filename = f"benchmark_{dimension['name'].lower().replace(' × ', '_').replace(' ', '_')}.csv"
            filepath = f'data/processed/{filename}'
            key = dimension['name'].lower().replace(' × ', '_').replace(' ', '_')
            
            try:
                benchmark_data[key] = load_data(filepath)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
                continue
        
        print(f"Sample survey: {len(sample_survey)} participants")
        print(f"Countries represented: {sample_survey['country'].nunique()}")
        
        # Calculate standard scorecard
        print("\nCalculating Standard GRI Scorecard...")
        scorecard = calculate_gri_scorecard(
            sample_survey,
            benchmark_data,
            survey_source='global_dialogues',
            use_extended_dimensions=False
        )
        
        print("\nStandard GRI Scorecard:")
        print(scorecard[['Dimension', 'GRI Score', 'Diversity Score']].round(4))
        
        # Calculate extended scorecard
        print("\nCalculating Extended GRI Scorecard...")
        extended_scorecard = calculate_gri_scorecard(
            sample_survey,
            benchmark_data,
            survey_source='global_dialogues',
            use_extended_dimensions=True
        )
        
        print(f"\nExtended scorecard includes {len(extended_scorecard)} dimensions")
        print("Additional dimensions calculated:")
        extended_dims = extended_scorecard[
            ~extended_scorecard['Dimension'].isin(scorecard['Dimension'])
        ]
        if len(extended_dims) > 0:
            print(extended_dims[['Dimension', 'GRI Score', 'Diversity Score']].round(4))
        else:
            print("  (Some extended dimensions may require additional data preparation)")
        
    except Exception as e:
        print(f"Demo calculation failed: {e}")
        print("This may be expected if benchmark data is not available.")
    
    print("\n5. CONFIGURATION BENEFITS")
    print("-" * 30)
    print("✓ Flexible dimension definitions")
    print("✓ Easy integration of new survey formats")
    print("✓ Consistent segment naming across data sources")
    print("✓ Regional aggregation capabilities")
    print("✓ Extensible to new geographical hierarchies")
    print("✓ Backwards compatible with existing code")
    
    print("\n" + "=" * 60)
    print("Configuration system demonstration complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()