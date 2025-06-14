#!/usr/bin/env python3
"""Check WVS Wave 6 file structure more carefully."""

import pandas as pd

# Read the file line by line to understand structure
filepath = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'

print("=== Checking WVS Wave 6 Structure ===")
with open(filepath, 'r', encoding='utf-8') as f:
    lines = []
    for i, line in enumerate(f):
        lines.append(line.strip())
        if i < 20:
            print(f"Line {i}: {line[:80]}...")
        if i > 25:
            break

# Find where actual data starts
data_start = None
for i, line in enumerate(lines):
    # Look for a line that starts with a number (likely interview ID)
    parts = line.split(',')
    if len(parts) > 5 and parts[0].isdigit():
        data_start = i
        print(f"\nData appears to start at line {i}")
        print(f"First data line: {line[:100]}...")
        break

# Try reading with pandas from that line
if data_start:
    # Get the header line (should be just before data)
    header_line = None
    for i in range(data_start-1, -1, -1):
        if 'rowid' in lines[i].lower() or 'interview' in lines[i].lower():
            header_line = i
            break
    
    if header_line:
        print(f"\nHeader line found at {header_line}: {lines[header_line][:100]}...")
        
        # Parse headers
        headers = lines[header_line].split(',')
        print(f"\nHeaders ({len(headers)}): {headers[:10]}...")
        
        # Read a sample of data
        df = pd.read_csv(filepath, skiprows=data_start, nrows=10, header=None)
        df.columns = headers[:len(df.columns)]
        
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head())