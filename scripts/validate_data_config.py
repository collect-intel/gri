#!/usr/bin/env python3
"""
Configuration-driven data validation script for make validate-data command.
"""

import sys
import os
from pathlib import Path
import pandas as pd

# Add the gri module to the path
sys.path.append(str(Path(__file__).parent.parent))

from gri.config import GRIConfig

def validate_processed_data():
    """Validate all processed benchmark files according to config/dimensions.yaml."""
    config = GRIConfig()
    dimensions = config.get_standard_scorecard()
    processed_dir = Path("data/processed")
    
    if not processed_dir.exists():
        print(f"Error: Processed data directory not found: {processed_dir}")
        print("Run: make process-data")
        return False
    
    print("Validating processed benchmark data...")
    
    all_valid = True
    for dimension in dimensions:
        # Convert dimension name to filename
        filename = f"benchmark_{dimension['name'].lower().replace(' × ', '_').replace(' ', '_')}.csv"
        filepath = processed_dir / filename
        
        if not filepath.exists():
            print(f"✗ Missing processed file: {filename}")
            all_valid = False
            continue
        
        try:
            df = pd.read_csv(filepath)
            total_sum = df['population_proportion'].sum()
            print(f"✓ {filename}: {len(df)} strata, sum={total_sum:.6f}")
            
            # Warn if sum is not close to 1.0
            if abs(total_sum - 1.0) > 0.01:
                print(f"  ⚠️  Warning: Proportion sum {total_sum:.6f} differs from expected 1.0")
            
        except Exception as e:
            print(f"✗ Error reading {filename}: {e}")
            all_valid = False
    
    if all_valid:
        print("Data validation completed")
        return True
    else:
        print("Data validation failed")
        return False

if __name__ == "__main__":
    success = validate_processed_data()
    sys.exit(0 if success else 1)