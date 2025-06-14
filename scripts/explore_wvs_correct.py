#!/usr/bin/env python3
"""
Correctly read WVS data with proper column headers.
"""

import pandas as pd
import numpy as np

wave7_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_7_csv_v6.csv'
wave6_path = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'

print("=== Reading WVS Wave 7 with correct headers ===")
# First, let's read the header line separately
with open(wave7_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    # Line 12 should have the actual column names
    header_line = lines[12].strip()
    print(f"Header line: {header_line}")

# Now read with proper settings
df7 = pd.read_csv(wave7_path, skiprows=12, encoding='utf-8')

# The first row might be headers, let's check
print(f"\nFirst row (might be headers): {df7.iloc[0].tolist()}")

# Set correct column names
if df7.iloc[0, 0] == 'D_INTERVIEW':
    # First row is actually headers
    df7.columns = df7.iloc[0]
    df7 = df7[1:].reset_index(drop=True)
    # Convert numeric columns
    for col in ['Q262', 'Q266', 'Q260', 'Q289', 'H_URBRURAL']:
        if col in df7.columns:
            df7[col] = pd.to_numeric(df7[col], errors='coerce')

print(f"\nShape after cleanup: {df7.shape}")
print(f"Columns: {list(df7.columns)}")
print(f"\nFirst 5 rows:")
print(df7.head())

print("\n=== Data Summary ===")
print(f"Age (Q262): min={df7['Q262'].min()}, max={df7['Q262'].max()}, mean={df7['Q262'].mean():.1f}")
print(f"Countries: {df7['Q266'].nunique()} unique")
print(f"Sex distribution: {df7['Q260'].value_counts().to_dict()}")
print(f"Urban/Rural: {df7['H_URBRURAL'].value_counts().to_dict()}")

# Get country names from ISO codes
print("\n=== Countries in dataset ===")
country_dist = df7.groupby('ISO3_Code').size().sort_values(ascending=False).head(15)
print("Top 15 countries by sample size:")
print(country_dist)

# Check religion coding
print("\n=== Religion Distribution ===")
religion_map = {
    0: "No denomination",
    1: "Roman Catholic", 
    2: "Protestant",
    3: "Orthodox",
    4: "Jew",
    5: "Muslim",
    6: "Hindu", 
    7: "Buddhist",
    8: "Other"
}
religion_counts = df7['Q289'].value_counts().head(10)
for code, count in religion_counts.items():
    label = religion_map.get(code, f"Code {code}")
    print(f"{label}: {count}")

print("\n=== Checking Wave 6 ===")
# Do the same for Wave 6
df6 = pd.read_csv(wave6_path, skiprows=12, encoding='utf-8', nrows=1000)
if df6.iloc[0, 0] == 'V1' or 'INTERVIEW' in str(df6.iloc[0, 0]):
    df6.columns = df6.iloc[0]
    df6 = df6[1:].reset_index(drop=True)

print(f"Wave 6 columns (first 15): {list(df6.columns[:15])}")
print(f"Wave 6 shape: {df6.shape}")