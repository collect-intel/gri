#!/usr/bin/env python3
"""Debug GD4 data structure to understand the format."""

import pandas as pd
from pathlib import Path

# Load GD4 data
gd4_path = Path("data/raw/survey_data/global-dialogues/Data/GD4/GD4_aggregate_standardized.csv")
df = pd.read_csv(gd4_path)

print("GD4 Data Shape:", df.shape)
print("\nFirst 5 columns:", df.columns[:5].tolist())
print("\nColumns starting with 'O':")
for col in sorted([c for c in df.columns if c.startswith('O')]):
    print(f"  {col}")

print("\nFirst row data for O2 (age) columns:")
row = df.iloc[0]
for col in df.columns:
    if col.startswith('O2:'):
        print(f"  {col}: {row[col]} (type: {type(row[col])})")

print("\nChecking if this is aggregate data (one row per response) or participant data...")
print(f"Number of unique Participant IDs: {df['Participant ID'].nunique()}")
print(f"Number of rows: {len(df)}")
print(f"Sample Participant IDs: {df['Participant ID'].head().tolist()}")