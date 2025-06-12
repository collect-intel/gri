#!/usr/bin/env python3
"""
Configuration-driven benchmark display script for make show-benchmarks command.
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add the gri module to the path
sys.path.append(str(Path(__file__).parent.parent))

from gri.config import GRIConfig

def show_benchmark_summary():
    """Display summary of all benchmark files according to config/dimensions.yaml."""
    config = GRIConfig()
    dimensions = config.get_standard_scorecard()
    processed_dir = Path("data/processed")
    
    print("Benchmark Data Summary:")
    print("=" * 60)
    
    for dimension in dimensions:
        # Convert dimension name to filename
        filename = f"benchmark_{dimension['name'].lower().replace(' × ', '_').replace(' ', '_')}.csv"
        filepath = processed_dir / filename
        
        if not filepath.exists():
            print(f"\n{dimension['name']}:")
            print(f"  ✗ File not found: {filename}")
            continue
        
        try:
            df = pd.read_csv(filepath)
            
            print(f"\n{dimension['name']}:")
            print(f"  Strata: {len(df):,}")
            print(f"  Proportion sum: {df['population_proportion'].sum():.6f}")
            
            # Show breakdown by each column
            for col in dimension['columns']:
                if col in df.columns and col != 'population_proportion':
                    unique_values = df[col].unique()
                    if len(unique_values) <= 20:  # Only show if reasonable number
                        print(f"  {col.replace('_', ' ').title()}: {sorted(unique_values)}")
                    else:
                        print(f"  {col.replace('_', ' ').title()}: {len(unique_values)} unique values")
            
        except Exception as e:
            print(f"\n{dimension['name']}:")
            print(f"  ✗ Error reading file: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    show_benchmark_summary()