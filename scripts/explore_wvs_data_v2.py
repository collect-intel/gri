#!/usr/bin/env python3
"""
Explore WVS data structure, handling header rows properly.
"""

import pandas as pd
import numpy as np

wave7_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_7_csv_v6.csv'
wave6_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'

print("=== Checking raw file structure ===")
# Read raw lines to understand structure
with open(wave7_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i < 15:  # Check first 15 lines
            print(f"Line {i}: {line[:100]}...")
        else:
            break

print("\n=== Trying to read actual data ===")
# Try reading with different skip patterns
for skip in [0, 1, 2, 3, 4, 5]:
    try:
        df = pd.read_csv(wave7_path, skiprows=skip, nrows=5, encoding='utf-8')
        print(f"\nSkipping {skip} rows:")
        print(f"Columns: {list(df.columns[:10])}")
        print(f"First data row sample: {df.iloc[0, :5].tolist() if len(df) > 0 else 'No data'}")
        
        # Check if this looks like actual data (numeric values)
        if len(df) > 0:
            first_vals = df.iloc[0, :5]
            if any(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit()) for v in first_vals):
                print("This looks like actual data!")
                break
    except Exception as e:
        print(f"Error with skip={skip}: {e}")

# Also check the column names more carefully
print("\n=== Checking column pattern ===")
df_header = pd.read_csv(wave7_path, nrows=0)
print(f"Header columns: {list(df_header.columns[:20])}")

# Check if these are WVS variable codes (like V1, V2, etc.)
v_cols = [col for col in df_header.columns if str(col).startswith('V') and any(c.isdigit() for c in str(col))]
print(f"\nFound {len(v_cols)} V-coded columns (typical WVS format)")
if v_cols:
    print(f"Examples: {v_cols[:10]}")