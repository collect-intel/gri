#!/usr/bin/env python3
"""
Process Afrobarometer Round 9 SPSS file into GRI-compatible participant format.

Reads the merged R9 .sav file and produces a standardized participant CSV with
columns: country, gender, age_group, religion, environment.

Data Source & License
=====================
Afrobarometer Round 9 (2021/2023), merged cross-country dataset.
Available for free download at https://www.afrobarometer.org/data/
Licensed for academic and non-commercial use.

Variable Mapping
================
| GRI Field    | Afrobarometer Variable | Notes                                    |
|-------------|------------------------|------------------------------------------|
| country     | COUNTRY                | Text labels, 39 countries                |
| gender      | Q100                   | 1=Man→Male, 2=Woman→Female               |
| age_group   | AGE_v1                 | 1-6=age bins, 9=DK/Refused               |
| religion    | Q95                    | Numeric codes → 7 GRI standard           |
| environment | URBRUR                 | 1=Urban, 2=Rural, 3=Peri-urban→Urban     |

Religion Mapping (Q95 numeric codes)
=====================================
Uses numeric codes from SPSS file to avoid Unicode string matching issues.
  Christianity (codes 1-17, 30-34, 100, 420, 740, 780, 820-823):
    Roman Catholic, Protestant denominations, Orthodox, Pentecostal,
    Evangelical, Independent, etc. (25+ denominations)
  Islam (codes 18-24):
    Muslim, Sunni, Shia, Ismaeli, Sufi brotherhoods
  Hinduism (code 26): Hindu
  Judaism (code 34): Jewish (n=8)
  Unaffiliated (codes 0, 28, 29): None, Atheist, Agnostic
  Other (codes 25, 27, 9995): Traditional/ethnic religion, Bahai, Other

Excluded: 9994=Not asked in country, 9998=Refused, 9999=Don't know
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

try:
    import pyreadstat
except ImportError:
    print("Error: pyreadstat required. Install with: pip install pyreadstat")
    sys.exit(1)


# Afrobarometer country names that differ from GRI standard (UN/benchmark names)
COUNTRY_NAME_MAP = {
    "Congo-Brazzaville": "Congo",
}

# Q95 Religion: numeric code → GRI standard category
# Codes from SPSS value labels (verified via pyreadstat)
RELIGION_CODE_MAP = {
    # Christianity
    1: "Christianity",     # Christian only
    2: "Christianity",     # Roman Catholic
    3: "Christianity",     # Orthodox
    4: "Christianity",     # Coptic
    5: "Christianity",     # Anglican
    6: "Christianity",     # Lutheran
    7: "Christianity",     # Methodist
    8: "Christianity",     # Presbyterian
    9: "Christianity",     # Baptist
    10: "Christianity",    # Quaker / Friends
    11: "Christianity",    # Mennonite
    12: "Christianity",    # Evangelical
    13: "Christianity",    # Pentecostal
    14: "Christianity",    # Independent (African Independent Church)
    15: "Christianity",    # Jehovah's Witness
    16: "Christianity",    # Seventh Day Adventist
    17: "Christianity",    # Mormon
    30: "Christianity",    # Dutch Reformed
    31: "Christianity",    # Calvinist
    32: "Christianity",    # Church of Christ
    33: "Christianity",    # Zionist Christian Church
    100: "Christianity",   # Eglise Du Christianisme Céleste
    420: "Christianity",   # Fifohazana
    740: "Christianity",   # Morovian
    780: "Christianity",   # Faith of Unity
    820: "Christianity",   # United Church of Zambia
    821: "Christianity",   # New Apostolic Church
    822: "Christianity",   # Christian mission in many lands
    823: "Christianity",   # Salvation Army
    # Islam
    18: "Islam",           # Muslim only
    19: "Islam",           # Sunni only
    20: "Islam",           # Ismaeli
    21: "Islam",           # Mouridiya Brotherhood
    22: "Islam",           # Tijaniya Brotherhood
    23: "Islam",           # Qadiriya Brotherhood
    24: "Islam",           # Shia
    500: "Islam",          # Ançardine
    # Hinduism
    26: "Hinduism",        # Hindu
    # Judaism
    34: "Judaism",         # Jewish
    # Unaffiliated
    0: "I do not identify with any religious group or faith",   # None
    28: "I do not identify with any religious group or faith",  # Agnostic
    29: "I do not identify with any religious group or faith",  # Atheist
    # Other
    25: "Other religious group",   # Traditional / ethnic religion
    27: "Other religious group",   # Bahai
    9995: "Other religious group", # Other
}

# Codes to exclude (not valid religion responses)
RELIGION_EXCLUDE_CODES = {9994, 9998, 9999}  # Not asked, Refused, Don't know

# Q100 Gender: 1=Man→Male, 2=Woman→Female
GENDER_CODE_MAP = {1: "Male", 2: "Female"}

# AGE_v1: pre-binned age groups
AGE_CODE_MAP = {
    1: "18-25",
    2: "26-35",
    3: "36-45",
    4: "46-55",
    5: "56-65",
    6: "65+",     # "66 and over" → standardize to "65+"
}
# Code 9 = Don't know/Refused → excluded (maps to NaN)

# URBRUR: 1=Urban, 2=Rural, 3=Peri-urban→Urban
ENVIRONMENT_CODE_MAP = {1: "Urban", 2: "Rural", 3: "Urban"}


def process_afrobarometer(input_path: str, output_path: str) -> pd.DataFrame:
    """Process Afrobarometer R9 SPSS file into GRI participant format."""
    print(f"Reading {input_path}...")

    # Read WITHOUT value labels to get raw numeric codes (avoids Unicode issues)
    df_raw, meta = pyreadstat.read_sav(input_path, apply_value_formats=False)

    # Read WITH value labels just for COUNTRY (which has clean text labels)
    df_labeled, _ = pyreadstat.read_sav(
        input_path, apply_value_formats=True, usecols=["COUNTRY"]
    )

    print(f"  Loaded {len(df_raw)} rows × {len(df_raw.columns)} columns")
    print(f"  Countries: {df_labeled['COUNTRY'].nunique()}")

    result = pd.DataFrame()

    # Country (use text labels, then standardize)
    result["country"] = df_labeled["COUNTRY"].map(lambda x: COUNTRY_NAME_MAP.get(x, x))
    print(f"  Countries after mapping: {result['country'].nunique()}")

    # Gender (numeric codes)
    result["gender"] = df_raw["Q100"].map(GENDER_CODE_MAP)
    n_valid = result["gender"].notna().sum()
    print(f"  Gender: {n_valid}/{len(df_raw)} valid ({n_valid/len(df_raw)*100:.1f}%)")

    # Age group (numeric codes)
    result["age_group"] = df_raw["AGE_v1"].map(AGE_CODE_MAP)
    n_valid = result["age_group"].notna().sum()
    print(f"  Age: {n_valid}/{len(df_raw)} valid ({n_valid/len(df_raw)*100:.1f}%)")

    # Religion (numeric codes)
    q95_raw = df_raw["Q95"]
    result["religion"] = q95_raw.map(
        lambda x: RELIGION_CODE_MAP.get(x, np.nan)
        if pd.notna(x) and x not in RELIGION_EXCLUDE_CODES
        else np.nan
    )
    n_valid = result["religion"].notna().sum()
    n_excluded = q95_raw.isin(RELIGION_EXCLUDE_CODES).sum()
    print(f"  Religion: {n_valid}/{len(df_raw)} valid ({n_valid/len(df_raw)*100:.1f}%)")
    print(f"    Excluded (refused/not asked/DK): {n_excluded}")

    # Check for unmapped codes
    all_known = set(RELIGION_CODE_MAP.keys()) | RELIGION_EXCLUDE_CODES
    unmapped_mask = ~q95_raw.isin(all_known) & q95_raw.notna()
    if unmapped_mask.any():
        print(f"    WARNING: {unmapped_mask.sum()} rows with unmapped religion codes:")
        for code, count in q95_raw[unmapped_mask].value_counts().items():
            print(f"      Code {int(code)}: {count}")

    # Environment (numeric codes)
    result["environment"] = df_raw["URBRUR"].map(ENVIRONMENT_CODE_MAP)
    n_valid = result["environment"].notna().sum()
    print(f"  Environment: {n_valid}/{len(df_raw)} valid ({n_valid/len(df_raw)*100:.1f}%)")

    # Religion distribution summary
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
    input_file = base_path / "data/raw/survey_data/afrobarometer/afrobarometer_r9_merged.sav"
    output_file = base_path / "data/processed/surveys/afrobarometer/afrobarometer_r9_participants_processed.csv"

    if not input_file.exists():
        print(f"Error: Input file not found at {input_file}")
        print("Download from https://www.afrobarometer.org/data/")
        sys.exit(1)

    process_afrobarometer(str(input_file), str(output_file))
