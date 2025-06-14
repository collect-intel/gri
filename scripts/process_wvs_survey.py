#!/usr/bin/env python3
"""
Process World Values Survey data for GRI analysis.

This script converts WVS data into the standardized format expected by the GRI module.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import argparse

def load_wvs_raw(filepath, wave):
    """Load raw WVS data file with proper column handling."""
    print(f"Loading WVS Wave {wave} from {filepath}")
    
    # Read the header line to get column names
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Find the line with actual column headers
        header_line_idx = None
        for i, line in enumerate(lines):
            if wave == 7 and 'D_INTERVIEW' in line:
                header_line_idx = i
                break
            elif wave == 6 and 'rowid' in line.lower():
                header_line_idx = i
                break
        
        if header_line_idx is None:
            # Default to line 12 for Wave 7, line 23 for Wave 6
            header_line_idx = 12 if wave == 7 else 23
        
        # Get column names
        columns = lines[header_line_idx].strip().split(',')
    
    # Read data starting after header line
    df = pd.read_csv(filepath, skiprows=header_line_idx+1, names=columns, encoding='utf-8')
    
    # Convert numeric columns based on wave
    if wave == 7:
        numeric_cols = ['Q262', 'Q266', 'Q260', 'Q289', 'H_URBRURAL']
    else:
        # Wave 6 uses different column names - we'll identify them from the data
        numeric_cols = []
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try to convert to numeric
                    pd.to_numeric(df[col], errors='raise')
                    numeric_cols.append(col)
                except:
                    pass
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Print column info for debugging
    print(f"Columns found: {list(df.columns[:10])}")
    print(f"Loaded {len(df)} responses")
    return df

def get_wvs_mappings():
    """Get WVS-specific mappings for standardization."""
    # Country code mappings (WVS uses numeric codes)
    country_map = {
        # Major countries from WVS
        840: 'United States', 276: 'Germany', 826: 'United Kingdom',
        724: 'Spain', 620: 'Portugal', 250: 'France', 380: 'Italy',
        528: 'Netherlands', 752: 'Sweden', 578: 'Norway', 
        124: 'Canada', 36: 'Australia', 554: 'New Zealand',
        392: 'Japan', 410: 'South Korea', 156: 'China', 356: 'India',
        76: 'Brazil', 484: 'Mexico', 32: 'Argentina', 152: 'Chile',
        170: 'Colombia', 604: 'Peru', 862: 'Venezuela',
        818: 'Egypt', 634: 'Qatar', 682: 'Saudi Arabia', 784: 'United Arab Emirates',
        566: 'Nigeria', 710: 'South Africa', 404: 'Kenya', 231: 'Ethiopia',
        20: 'Andorra', 51: 'Armenia', 40: 'Austria', 112: 'Belarus',
        100: 'Bulgaria', 191: 'Croatia', 196: 'Cyprus', 203: 'Czechia',
        233: 'Estonia', 268: 'Georgia', 300: 'Greece', 348: 'Hungary',
        364: 'Iran', 368: 'Iraq', 398: 'Kazakhstan', 417: 'Kyrgyzstan',
        428: 'Latvia', 440: 'Lithuania', 807: 'North Macedonia', 499: 'Montenegro',
        642: 'Romania', 643: 'Russia', 688: 'Serbia', 703: 'Slovakia',
        705: 'Slovenia', 792: 'Turkey', 804: 'Ukraine',
        12: 'Algeria', 50: 'Bangladesh', 604: 'Peru', 608: 'Philippines',
        616: 'Poland', 630: 'Puerto Rico', 646: 'Rwanda', 764: 'Thailand',
        858: 'Uruguay', 704: 'Vietnam', 887: 'Yemen', 894: 'Zambia', 716: 'Zimbabwe'
    }
    
    # Sex mapping
    sex_map = {1: 'Male', 2: 'Female'}
    
    # Religion mapping (WVS codes)
    religion_map = {
        0: 'No religious denomination',
        1: 'Roman Catholic',
        2: 'Protestant', 
        3: 'Orthodox',
        4: 'Jew',
        5: 'Muslim',
        6: 'Hindu',
        7: 'Buddhist', 
        8: 'Other',
        -1: 'No answer',
        -2: 'No answer'
    }
    
    # Urban/Rural mapping
    urban_map = {1: 'Urban', 2: 'Rural'}
    
    # Age groups (create from continuous age)
    def age_to_group(age):
        if pd.isna(age) or age < 0:
            return np.nan
        elif age < 18:
            return 'Under 18'
        elif age < 26:
            return '18-25'
        elif age < 36:
            return '26-35'
        elif age < 46:
            return '36-45'
        elif age < 56:
            return '46-55'
        elif age < 66:
            return '56-65'
        else:
            return '66+'
    
    return {
        'country': country_map,
        'sex': sex_map,
        'religion': religion_map,
        'urban_rural': urban_map,
        'age_to_group': age_to_group
    }

def standardize_wvs_data(df, wave):
    """Convert WVS data to GRI standard format."""
    mappings = get_wvs_mappings()
    
    # Create standardized dataframe
    standardized = pd.DataFrame()
    
    # Map based on wave version
    if wave == 7:
        # Wave 7 column mappings
        standardized['participant_id'] = df['D_INTERVIEW'].astype(str)
        standardized['country_code'] = df['Q266']
        standardized['country'] = df['Q266'].map(mappings['country'])
        standardized['gender'] = df['Q260'].map(mappings['sex'])
        standardized['age'] = df['Q262']
        standardized['age_group'] = df['Q262'].apply(mappings['age_to_group'])
        standardized['religion'] = df['Q289'].map(mappings['religion'])
        standardized['environment'] = df['H_URBRURAL'].map(mappings['urban_rural'])
        standardized['iso3_code'] = df['ISO3_Code'] if 'ISO3_Code' in df.columns else None
        standardized['wave'] = 7
    else:
        # Wave 6 uses V-codes: V3 (ID), V242 (Age), V253 (Size of town), V240 (Sex), 
        # V144G (Religion), (Conversion) column, B_COUNTRY_ALPHA (Country)
        
        # First, convert the B_COUNTRY_ALPHA to country names
        country_alpha_map = {
            'DZA': 'Algeria', 'ARG': 'Argentina', 'AUS': 'Australia', 'BRA': 'Brazil',
            'CHL': 'Chile', 'CHN': 'China', 'COL': 'Colombia', 'EGY': 'Egypt',
            'EST': 'Estonia', 'DEU': 'Germany', 'GHA': 'Ghana', 'IND': 'India',
            'JPN': 'Japan', 'JOR': 'Jordan', 'KAZ': 'Kazakhstan', 'KOR': 'South Korea',
            'MEX': 'Mexico', 'NLD': 'Netherlands', 'NZL': 'New Zealand', 'NGA': 'Nigeria',
            'PAK': 'Pakistan', 'PER': 'Peru', 'PHL': 'Philippines', 'POL': 'Poland',
            'ROU': 'Romania', 'RUS': 'Russia', 'RWA': 'Rwanda', 'SGP': 'Singapore',
            'ZAF': 'South Africa', 'ESP': 'Spain', 'SWE': 'Sweden', 'THA': 'Thailand',
            'TUR': 'Turkey', 'UKR': 'Ukraine', 'USA': 'United States', 'URY': 'Uruguay',
            'ZWE': 'Zimbabwe', 'AND': 'Andorra', 'ARM': 'Armenia', 'AZE': 'Azerbaijan',
            'BLR': 'Belarus', 'CYP': 'Cyprus', 'ECU': 'Ecuador', 'GEO': 'Georgia',
            'IRQ': 'Iraq', 'KGZ': 'Kyrgyzstan', 'LBN': 'Lebanon', 'LBY': 'Libya',
            'MYS': 'Malaysia', 'MAR': 'Morocco', 'QAT': 'Qatar', 'SVN': 'Slovenia',
            'TTO': 'Trinidad and Tobago', 'TUN': 'Tunisia', 'UZB': 'Uzbekistan',
            'YEM': 'Yemen', 'BHR': 'Bahrain', 'HKG': 'Hong Kong', 'KWT': 'Kuwait'
        }
        
        # Map V-codes to standard format
        if 'V3' in df.columns:
            standardized['participant_id'] = df['V3'].astype(str)
        if 'B_COUNTRY_ALPHA' in df.columns:
            standardized['country'] = df['B_COUNTRY_ALPHA'].map(country_alpha_map)
            standardized['iso3_code'] = df['B_COUNTRY_ALPHA']
        if 'V240' in df.columns:
            standardized['gender'] = pd.to_numeric(df['V240'], errors='coerce').map(mappings['sex'])
        if 'V242' in df.columns:
            standardized['age'] = pd.to_numeric(df['V242'], errors='coerce')
            standardized['age_group'] = standardized['age'].apply(mappings['age_to_group'])
        if 'V144G' in df.columns:
            standardized['religion'] = pd.to_numeric(df['V144G'], errors='coerce').map(mappings['religion'])
        
        # For urban/rural, we need to convert V253 (Size of town) using the conversion rules
        # 1-3 = Rural, 4-8 = Urban
        if 'V253' in df.columns:
            town_size = pd.to_numeric(df['V253'], errors='coerce')
            standardized['environment'] = town_size.apply(lambda x: 'Rural' if x <= 3 else 'Urban' if x <= 8 else np.nan)
        
        standardized['wave'] = 6
    
    # Remove rows with missing critical data
    required_cols = ['participant_id', 'country', 'gender']
    standardized = standardized.dropna(subset=required_cols)
    
    # Add survey metadata
    standardized['survey'] = f'WVS_Wave_{wave}'
    standardized['year'] = 2022 if wave == 7 else 2014  # Approximate survey years
    
    print(f"Standardized {len(standardized)} responses with complete demographic data")
    return standardized

def save_processed_data(df, output_dir, wave):
    """Save processed WVS data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save main participant file
    output_file = output_dir / f'wvs_wave{wave}_participants_processed.csv'
    df.to_csv(output_file, index=False)
    print(f"Saved processed data to {output_file}")
    
    # Save summary statistics
    summary = {
        'total_participants': len(df),
        'countries': df['country'].nunique(),
        'country_distribution': df['country'].value_counts().to_dict(),
        'gender_distribution': df['gender'].value_counts().to_dict(),
        'age_distribution': df['age_group'].value_counts().to_dict(),
        'religion_distribution': df['religion'].value_counts().head(10).to_dict(),
        'environment_distribution': df['environment'].value_counts().to_dict()
    }
    
    summary_file = output_dir / f'wvs_wave{wave}_summary.yaml'
    with open(summary_file, 'w') as f:
        yaml.dump(summary, f, default_flow_style=False)
    print(f"Saved summary to {summary_file}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Process WVS data for GRI analysis')
    parser.add_argument('--wave', type=int, choices=[6, 7], help='WVS wave number')
    parser.add_argument('--input', type=str, help='Input WVS CSV file')
    parser.add_argument('--output-dir', type=str, default='data/processed/surveys/wvs',
                       help='Output directory for processed files')
    args = parser.parse_args()
    
    # Process Wave 7 by default
    if not args.wave and not args.input:
        # Process both waves
        wave7_file = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_7_csv_v6.csv'
        wave6_file = 'data/raw/survey_data/wvs/WVS_Cross-National_Wave_6_csv.csv'
        
        # Process Wave 7
        if Path(wave7_file).exists():
            print("\n=== Processing WVS Wave 7 ===")
            df7 = load_wvs_raw(wave7_file, wave=7)
            standardized7 = standardize_wvs_data(df7, wave=7)
            save_processed_data(standardized7, args.output_dir, wave=7)
        
        # Process Wave 6
        if Path(wave6_file).exists():
            print("\n=== Processing WVS Wave 6 ===")
            df6 = load_wvs_raw(wave6_file, wave=6)
            standardized6 = standardize_wvs_data(df6, wave=6)
            save_processed_data(standardized6, args.output_dir, wave=6)
    else:
        # Process specific file
        df = load_wvs_raw(args.input, wave=args.wave)
        standardized = standardize_wvs_data(df, wave=args.wave)
        save_processed_data(standardized, args.output_dir, wave=args.wave)

if __name__ == '__main__':
    main()