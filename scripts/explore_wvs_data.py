#!/usr/bin/env python3
"""
Quick exploration of WVS data structure to understand format.
"""

import pandas as pd
import numpy as np

# Load first few rows of Wave 7 to understand structure
wave7_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_7_csv_v6.csv'
wave6_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'

print("=== WVS Wave 7 Structure ===")
# Read with different encodings to handle special characters
try:
    df7 = pd.read_csv(wave7_path, nrows=5, encoding='utf-8')
except:
    df7 = pd.read_csv(wave7_path, nrows=5, encoding='latin-1')

print(f"Shape: {df7.shape}")
print(f"Columns (first 20): {list(df7.columns[:20])}")
print("\nFirst few rows of key columns:")
# Look for key demographic columns
key_cols = []
for col in df7.columns:
    col_lower = str(col).lower()
    if any(term in col_lower for term in ['age', 'sex', 'country', 'education', 'religion', 'rural', 'urban']):
        key_cols.append(col)
        if len(key_cols) >= 10:
            break

print(f"Found demographic columns: {key_cols}")

print("\n=== WVS Wave 6 Structure ===")
try:
    df6 = pd.read_csv(wave6_path, nrows=5, encoding='utf-8')
except:
    df6 = pd.read_csv(wave6_path, nrows=5, encoding='latin-1')

print(f"Shape: {df6.shape}")
print(f"Columns (first 20): {list(df6.columns[:20])}")

# Check if columns are similar
common_cols = set(df6.columns).intersection(set(df7.columns))
print(f"\nCommon columns between waves: {len(common_cols)} out of {len(df7.columns)} (Wave 7) and {len(df6.columns)} (Wave 6)")

# Look for specific WVS variable codes
print("\n=== Looking for standard WVS variables ===")
# Standard WVS demographic variables:
# V2: Country code
# V242: Sex
# V239: Age
# V147: Religious denomination
# V248: Education level
# V190: Urban/Rural

wvs_vars = ['V2', 'V242', 'V239', 'V147', 'V248', 'V190']
for var in wvs_vars:
    if var in df7.columns:
        print(f"{var} found in Wave 7")
    if var in df6.columns:
        print(f"{var} found in Wave 6")