#!/usr/bin/env python3
"""
Process Latinobarómetro survey files into GRI-compatible participant format.

Reads the 2023 Stata (.dta) and 2024 CSV files and produces standardized
participant CSVs with columns: country, gender, age_group, religion, environment.

Data Source & License
=====================
Latinobarómetro surveys (2023, 2024), available at https://www.latinobarometro.org/
Licensed for academic and non-commercial use.

Variable Mapping (2023 Stata file)
==================================
| GRI Field    | Variable | Notes                                       |
|-------------|----------|---------------------------------------------|
| country     | idenpa   | Text labels, 17 Latin American countries     |
| gender      | sexo     | Man/Woman → Male/Female                      |
| age_group   | edad     | Continuous age → binned to GRI standard      |
| religion    | S1       | 13 categories → 7 GRI standard               |
| environment | tamciud  | City size (8 categories) → Urban/Rural       |

Variable Mapping (2024 CSV file)
================================
Same variables but with numeric codes (semicolon-delimited CSV).
| GRI Field    | Variable | Notes                                       |
|-------------|----------|---------------------------------------------|
| country     | IDENPA   | ISO numeric codes → country names             |
| gender      | SEXO     | 1=Male, 2=Female                              |
| age_group   | EDAD     | Continuous age → binned to GRI standard       |
| religion    | S1       | Numeric codes → text labels → GRI standard    |
| environment | TAMCIUD  | 1-8 scale → Urban/Rural                       |

Environment (Urban/Rural) Derivation
=====================================
Latinobarómetro uses city size (TAMCIUD) rather than explicit urban/rural:
  1 = Less than 5,000    → Rural
  2 = 5,001 to 10,000    → Rural
  3 = 10,001 to 20,000   → Urban
  4 = 20,001 to 50,000   → Urban
  5 = 50,001 to 100,000  → Urban
  6 = 100,001 to 500,000 → Urban
  7 = Over 500,000        → Urban
  8 = Capital              → Urban

Threshold: <10,000 = Rural, 10,000+ = Urban (consistent with WVS convention).

Religion Mapping
================
2023 text labels → GRI standard:
  Christianity: Catholic, Evangelical, Other Christian, Jehovah's Witness, Mormon,
                Pentecostal, Seventh Day Adventist, Other Protestant
  Judaism:      Jewish
  Unaffiliated: None, Atheist, Agnostic, Believer not belonging to church
  Other:        Other

2024 numeric codes:
  1=Catholic, 2=Evangelical, 3=Pentecostal, 5=Other Christian, 6=Jewish,
  7=Other Protestant, 8=Seventh Day Adventist, 10=Jehovah's Witness,
  12=Mormon, 13=Believer not belonging, 14=Atheist, 96=Other, 97=None
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

try:
    import pyreadstat
except ImportError:
    print("Note: pyreadstat not available, 2023 Stata file will be skipped")
    pyreadstat = None


# Country name mapping: Latinobarómetro names → GRI standard
# 2023 Stata has leading spaces in country names and some Spanish names
COUNTRY_NAME_MAP_2023 = {
    "Argentina": "Argentina",
    "Bolivia": "Bolivia",
    "Brasil": "Brazil",
    "Chile": "Chile",
    "Colombia": "Colombia",
    "Costa Rica": "Costa Rica",
    "Dominican Republic": "Dominican Republic",
    "Rep. Dominicana": "Dominican Republic",
    "Ecuador": "Ecuador",
    "El Salvador": "El Salvador",
    "Guatemala": "Guatemala",
    "Honduras": "Honduras",
    "Mexico": "Mexico",
    "Nicaragua": "Nicaragua",
    "Panama": "Panama",
    "Paraguay": "Paraguay",
    "Peru": "Peru",
    "Uruguay": "Uruguay",
    "Venezuela": "Venezuela",
    # Handle Spanish names
    "República Dominicana": "Dominican Republic",
    "México": "Mexico",
    "Panamá": "Panama",
    "Perú": "Peru",
}

# 2024 CSV uses ISO numeric country codes
COUNTRY_CODE_MAP_2024 = {
    32: "Argentina",
    68: "Bolivia",
    76: "Brazil",
    152: "Chile",
    170: "Colombia",
    188: "Costa Rica",
    214: "Dominican Republic",
    218: "Ecuador",
    222: "El Salvador",
    320: "Guatemala",
    340: "Honduras",
    484: "Mexico",
    558: "Nicaragua",
    591: "Panama",
    600: "Paraguay",
    604: "Peru",
    858: "Uruguay",
    862: "Venezuela",
}

# Religion mapping for 2023 text labels (exact labels from Stata value formats)
RELIGION_MAP_2023 = {
    "Catholic": "Christianity",
    "Evangelical (no specific)": "Christianity",
    "Evangelical Pentecostal": "Christianity",
    "Evangelical methodist": "Christianity",
    "Evangelican baptism": "Christianity",  # sic - typo in source data
    "Jehovah's Witnesses": "Christianity",
    "Adventist": "Christianity",
    "Mormon": "Christianity",
    "Protestant": "Christianity",
    "Jewish": "Judaism",
    "None": "I do not identify with any religious group or faith",
    "Atheist": "I do not identify with any religious group or faith",
    "Agnostic": "I do not identify with any religious group or faith",
    "Believer, not belong to the church": "I do not identify with any religious group or faith",
    "African American Cults/umbanda": "Other religious group",
    "Other": "Other religious group",
}

# Values to exclude (not valid religion responses)
RELIGION_EXCLUDE_2023 = {"Don't know", "Does not answer"}

# Religion mapping for 2024 numeric codes
RELIGION_CODE_MAP_2024 = {
    1: "Christianity",       # Catholic
    2: "Christianity",       # Evangelical
    3: "Christianity",       # Pentecostal
    5: "Christianity",       # Other Christian
    6: "Judaism",            # Jewish
    7: "Christianity",       # Other Protestant
    8: "Christianity",       # Seventh Day Adventist
    10: "Christianity",      # Jehovah's Witness
    12: "Christianity",      # Mormon
    13: "I do not identify with any religious group or faith",  # Believer not belonging
    14: "I do not identify with any religious group or faith",  # Atheist
    96: "Other religious group",  # Other
    97: "I do not identify with any religious group or faith",  # None
}

# Gender mapping
GENDER_MAP_2023 = {
    "Man": "Male",
    "Woman": "Female",
    "Hombre": "Male",
    "Mujer": "Female",
}

GENDER_CODE_MAP_2024 = {
    1: "Male",
    2: "Female",
}

# City size → Urban/Rural (consistent with WVS: <10K = Rural, 10K+ = Urban)
# 2023 text labels (exact labels from Stata value formats, use period as thousands sep)
ENVIRONMENT_MAP_2023 = {
    "Less than 5.000": "Rural",
    "5.001 - 10.000": "Rural",
    "5.001 to 10.000": "Rural",
    "10.001 - 20.000": "Urban",
    "10.001 to 20.000": "Urban",
    "20.001 - 40.000": "Urban",
    "20.001 to 50.000": "Urban",
    "40.001 - 50.000": "Urban",
    "50.001 - 100.000": "Urban",
    "50.001 to 100.000": "Urban",
    "100.001 and more": "Urban",
    "100.001 to 500.000": "Urban",
    "Over 500.000": "Urban",
    "(Capital)": "Urban",
    "Capital": "Urban",
}

# 2024 numeric codes
ENVIRONMENT_CODE_MAP_2024 = {
    1: "Rural",   # Less than 5,000
    2: "Rural",   # 5,001 to 10,000
    3: "Urban",   # 10,001 to 20,000
    4: "Urban",   # 20,001 to 50,000
    5: "Urban",   # 50,001 to 100,000
    6: "Urban",   # 100,001 to 500,000
    7: "Urban",   # Over 500,000
    8: "Urban",   # Capital
}


def bin_age(age):
    """Bin continuous age into GRI standard age groups."""
    if pd.isna(age) or age < 16:
        return np.nan
    elif age <= 25:
        return "18-25"
    elif age <= 35:
        return "26-35"
    elif age <= 45:
        return "36-45"
    elif age <= 55:
        return "46-55"
    elif age <= 65:
        return "56-65"
    else:
        return "65+"


def process_2023_stata(input_path: str, output_path: str) -> pd.DataFrame:
    """Process Latinobarómetro 2023 Stata file."""
    if pyreadstat is None:
        print("  Skipping 2023: pyreadstat not available")
        return None

    print(f"Reading {input_path}...")
    df, meta = pyreadstat.read_dta(input_path, apply_value_formats=True)
    print(f"  Loaded {len(df)} rows × {len(df.columns)} columns")

    result = pd.DataFrame()

    # Country (strip leading spaces from Stata labels)
    result["country"] = df["idenpa"].str.strip().map(lambda x: COUNTRY_NAME_MAP_2023.get(x, x))
    print(f"  Countries: {result['country'].nunique()} ({', '.join(sorted(result['country'].unique()))})")

    # Gender
    result["gender"] = df["sexo"].map(GENDER_MAP_2023)
    n_valid = result["gender"].notna().sum()
    print(f"  Gender: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Age (bin continuous edad)
    result["age_group"] = df["edad"].apply(bin_age)
    n_valid = result["age_group"].notna().sum()
    print(f"  Age: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Religion
    religion_raw = df["S1"]
    result["religion"] = religion_raw.map(
        lambda x: RELIGION_MAP_2023.get(x, np.nan)
        if pd.notna(x) and x not in RELIGION_EXCLUDE_2023
        else np.nan
    )
    n_valid = result["religion"].notna().sum()
    n_excluded = religion_raw.isin(RELIGION_EXCLUDE_2023).sum()
    print(f"  Religion: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")
    print(f"    Excluded (DK/no answer): {n_excluded}")

    # Check unmapped
    all_mapped = set(RELIGION_MAP_2023.keys()) | RELIGION_EXCLUDE_2023
    unmapped = religion_raw[~religion_raw.isin(all_mapped) & religion_raw.notna()]
    if len(unmapped) > 0:
        print(f"    Unmapped religion values:")
        for v, c in unmapped.value_counts().head(10).items():
            print(f"      '{v}': {c}")

    # Environment (city size → Urban/Rural)
    tamciud_raw = df["tamciud"]
    result["environment"] = tamciud_raw.map(
        lambda x: ENVIRONMENT_MAP_2023.get(x, np.nan) if pd.notna(x) else np.nan
    )
    n_valid = result["environment"].notna().sum()
    print(f"  Environment: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Check unmapped tamciud
    all_env_mapped = set(ENVIRONMENT_MAP_2023.keys())
    unmapped_env = tamciud_raw[~tamciud_raw.isin(all_env_mapped) & tamciud_raw.notna()]
    if len(unmapped_env) > 0:
        print(f"    Unmapped environment values:")
        for v, c in unmapped_env.value_counts().head(10).items():
            print(f"      '{v}': {c}")

    # Religion distribution
    print("\n  Religion distribution (GRI categories):")
    for val, count in result["religion"].value_counts().items():
        print(f"    {val}: {count} ({count/len(result)*100:.1f}%)")

    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    print(f"\n  Saved {len(result)} participants to {output_file}")

    return result


def process_2024_csv(input_path: str, output_path: str) -> pd.DataFrame:
    """Process Latinobarómetro 2024 CSV file (semicolon-delimited, numeric codes)."""
    print(f"\nReading {input_path}...")
    df = pd.read_csv(input_path, sep=';', low_memory=False)
    print(f"  Loaded {len(df)} rows × {len(df.columns)} columns")

    result = pd.DataFrame()

    # Country (ISO numeric codes)
    result["country"] = df["IDENPA"].map(COUNTRY_CODE_MAP_2024)
    n_valid = result["country"].notna().sum()
    print(f"  Countries: {result['country'].nunique()} mapped, {len(df)-n_valid} unmapped")

    # Check unmapped country codes
    unmapped_codes = df.loc[result["country"].isna(), "IDENPA"].unique()
    if len(unmapped_codes) > 0:
        print(f"    Unmapped country codes: {unmapped_codes}")

    # Gender (1=Male, 2=Female)
    result["gender"] = df["SEXO"].map(GENDER_CODE_MAP_2024)
    n_valid = result["gender"].notna().sum()
    print(f"  Gender: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Age (bin continuous EDAD)
    result["age_group"] = df["EDAD"].apply(bin_age)
    n_valid = result["age_group"].notna().sum()
    print(f"  Age: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Religion (numeric codes)
    result["religion"] = df["S1"].map(RELIGION_CODE_MAP_2024)
    n_valid = result["religion"].notna().sum()
    print(f"  Religion: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Check unmapped religion codes
    unmapped_relig = df.loc[result["religion"].isna(), "S1"]
    unmapped_relig = unmapped_relig[unmapped_relig.notna()]
    if len(unmapped_relig) > 0:
        print(f"    Unmapped religion codes:")
        for v, c in unmapped_relig.value_counts().head(10).items():
            print(f"      {v}: {c}")

    # Environment (city size codes → Urban/Rural)
    result["environment"] = df["TAMCIUD"].map(ENVIRONMENT_CODE_MAP_2024)
    n_valid = result["environment"].notna().sum()
    print(f"  Environment: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

    # Religion distribution
    print("\n  Religion distribution (GRI categories):")
    for val, count in result["religion"].value_counts().items():
        print(f"    {val}: {count} ({count/len(result)*100:.1f}%)")

    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    print(f"\n  Saved {len(result)} participants to {output_file}")

    return result


if __name__ == "__main__":
    base_path = Path(__file__).parent.parent
    raw_dir = base_path / "data/raw/survey_data/latinobarometro"
    out_dir = base_path / "data/processed/surveys/latinobarometro"

    # Process 2023 Stata file
    stata_file = raw_dir / "Latinobarometro_2023_Eng_Stata_v1_0.dta"
    if stata_file.exists():
        process_2023_stata(
            str(stata_file),
            str(out_dir / "latinobarometro_2023_participants_processed.csv"),
        )
    else:
        print(f"2023 Stata file not found at {stata_file}")

    # Process 2024 CSV file
    csv_file = raw_dir / "Latinobarometro_2024_Csv_eng_v20250817.csv"
    if csv_file.exists():
        process_2024_csv(
            str(csv_file),
            str(out_dir / "latinobarometro_2024_participants_processed.csv"),
        )
    else:
        print(f"2024 CSV file not found at {csv_file}")
