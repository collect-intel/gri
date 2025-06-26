#!/usr/bin/env python3
"""Debug GD4 participants data structure."""

import pandas as pd
from pathlib import Path

# Load GD4 participants data
gd4_path = Path("data/raw/survey_data/global-dialogues/Data/GD4/GD4_participants.csv")

# Read with proper handling of the header row
df = pd.read_csv(gd4_path, skiprows=1)

print("GD4 Participants Data Shape:", df.shape)
print("\nColumn names:")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

print("\nFirst few rows of key columns:")
key_cols = [col for col in df.columns if any(term in col.lower() for term in ['country', 'age', 'gender', 'religion', 'environment', 'live'])]
print(df[key_cols].head())

print("\nUnique values in demographic columns:")
for col in key_cols:
    print(f"\n{col}:")
    print(df[col].value_counts().head(10))