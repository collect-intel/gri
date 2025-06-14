#!/usr/bin/env python3
"""
Properly read WVS data skipping explanation rows.
"""

import pandas as pd
import numpy as np

wave7_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_7_csv_v6.csv'
wave6_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'

print("=== Reading WVS Wave 7 ===")
# Skip the explanation rows and read actual data
df7 = pd.read_csv(wave7_path, skiprows=12, encoding='utf-8')
print(f"Shape: {df7.shape}")
print(f"Columns: {list(df7.columns)}")
print(f"\nFirst 5 rows:")
print(df7.head())

print("\n=== Column Analysis ===")
print(f"D_INTERVIEW (ID): {df7['D_INTERVIEW'].dtype}, unique values: {df7['D_INTERVIEW'].nunique()}")
print(f"Q262 (Age): {df7['Q262'].dtype}, range: {df7['Q262'].min()} - {df7['Q262'].max()}")
print(f"Q266 (Country Code): {df7['Q266'].dtype}, unique countries: {df7['Q266'].nunique()}")
print(f"Q260 (Sex): {df7['Q260'].value_counts().to_dict()}")
print(f"Q289 (Religion): {df7['Q289'].value_counts().head(10).to_dict()}")
print(f"H_URBRURAL (Urban/Rural): {df7['H_URBRURAL'].value_counts().to_dict()}")

print("\n=== Country Distribution ===")
# Map country codes to names
country_counts = df7['Q266'].value_counts().head(10)
print("Top 10 countries by sample size:")
print(country_counts)

print("\n=== Reading WVS Wave 6 ===")
# Try the same for Wave 6
df6 = pd.read_csv(wave6_path, skiprows=12, encoding='utf-8', nrows=5)
print(f"Wave 6 columns: {list(df6.columns)}")
print(f"Wave 6 shape: {df6.shape}")

# Check if column names are similar
if 'D_INTERVIEW' in df6.columns:
    print("Wave 6 uses same column structure!")
else:
    print("Wave 6 may have different column names")