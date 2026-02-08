"""
Process WVS Wave 1-5 cross-national CSV files into GRI-compatible participant format.

Reads the raw wave-specific cross-national CSVs downloaded from the WVS website
and produces standardized participant files matching the GRI pipeline format.

Data Source & License
=====================
World Values Survey data files are available for non-profit use only.
Raw data files cannot be redistributed (see WVS_license.txt).
The processed outputs contain only derived demographic categories, not raw survey
responses, which is consistent with the WVS conditions of use.

Variable Mapping by Wave
========================
Each WVS wave uses different variable names for the same concepts:

| Concept      | Wave 1  | Wave 2  | Wave 3  | Wave 4  | Wave 5  |
|-------------|---------|---------|---------|---------|---------|
| Country     | V2      | V2      | V2      | V2      | V2      |
| Sex         | V214    | V353    | V214    | V223    | V235    |
| Age         | V216    | V355    | V216    | V225    | V237    |
| Religion    | V179    | V144    | V179    | V184G   | V185    |
| Urban/Rural | V232*   | V372*   | --      | V248    | V263    |
| Size of Town| --      | V368    | V232    | V241    | V255    |
| Year        | S021**  | S021**  | S021**  | V246    | S021**  |

*  Wave 1 V232 is a 3-category habitat variable (not size of town)
   Wave 2 V372 is a 3-category habitat variable
** Year is extracted from last 4 digits of S021 composite ID

Environment (Urban/Rural) Derivation
=====================================
Each wave has different environment variable availability and coverage.
We use a primary + fallback strategy to maximize coverage:

Wave 1: V232 habitat (1=Rural→Rural, 2=Small/med town→Urban, 3=Large town→Urban)
        Coverage: ~87%. No size-of-town fallback available.

Wave 2: V372 habitat primary (2=Rural→Rural, 3=Urban→Urban)
        V368 size-of-town fallback (1-3→Rural [<10K], 4-8→Urban [10K+])
        V372 has only 14.3% coverage; V368 adds ~51% more.

Wave 3: V232 size-of-town only (1-3→Rural [<10K], 4-8→Urban [10K+])
        Coverage: ~68%. No binary urban/rural variable exists.

Wave 4: V248 primary (1=Urban, 2=Rural, 3=Mixed→Urban)
        V241 size-of-town fallback (1-3→Rural [<10K], 4-8→Urban [10K+])
        V248 has only 21.9% coverage; V241 adds ~38% more.

Wave 5: V263 primary (1=Urban, 2=Rural, 3=Mix→Urban)
        V255 size-of-town fallback (1-3→Rural [<10K], 4-8→Urban [10K+])
        V263 has only 13.6% coverage; V255 adds ~54% more.

Size of Town → Urban/Rural conversion:
  Codes 1-3 (under 10,000 population) → Rural
  Codes 4-8 (10,000+ population) → Urban
  This follows the WVS Wave 6 documentation (V253 codes 1-3 → Rural, 4-8 → Urban)
  and is consistent with the user-specified rule (<10K = Rural, 10K+ = Urban).
  "Mixed"/"Suburban" environments → Urban (per GRI convention in config/segments.yaml).

Religion Mapping
================
All religion codes are mapped to 7 GRI standard categories:
  Christianity, Islam, Hinduism, Buddhism, Judaism, Unaffiliated, Other

Mappings were validated by cross-referencing raw wave codes against the WVS
Time Series harmonized F025 variable (9-category scheme). Each raw code was
checked for 100% agreement with its F025 mapping. See per-wave dictionaries
below for detailed source documentation.

Key religion coding notes:
- Wave 1 V179: Simple 0-8 scheme (same codes as WVS harmonized F025)
- Wave 2 V144: Non-sequential codes; all map cleanly to F025
- Wave 3 V179: 53 substantive codes; all 100% clean except V179=84 (n=6)
- Wave 4 V184G: Pre-harmonized 0-9 grouped scheme; code 9 is a heterogeneous
  catch-all (49% Muslim, 25% Protestant, 17% Other) → mapped to "Other"
- Wave 5 V185: 50 substantive codes; V185=25 (n=2781) is 72% Protestant /
  28% Other (country-dependent) → mapped to "Christianity" (majority rule)

Country Code Mapping
====================
V2 uses ISO 3166-1 numeric codes. Four non-standard codes appear in Wave 3:
  101 = Tambov (Russian Federation sub-sample)
  911 = Northern Ireland (separate from UK)
  912 = Republika Srpska (Bosnian Serb entity)
  914 = Montenegro (pre-2006 independence; standard 499 used from Wave 4)

Citations (required by WVS license)
====================================
Wave 1: Inglehart, R., et al. (2022). World Values Survey: Round One.
        JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.17
Wave 2: Inglehart, R., et al. (2022). World Values Survey: Round Two.
        JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.18
Wave 3: Inglehart, R., et al. (2022). World Values Survey: Round Three.
        JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.19
Wave 4: Inglehart, R., et al. (2022). World Values Survey: Round Four.
        JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.20
Wave 5: Inglehart, R., et al. (2022). World Values Survey: Round Five.
        JD Systems Institute & WVSA Secretariat. doi:10.14281/18241.21

Usage:
    python scripts/process_wvs_waves.py [--waves 1 2 3 4 5]
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Country code mapping (V2 → country name)
# ISO 3166-1 numeric codes + 4 WVS-specific codes (101, 911, 912, 914)
# ---------------------------------------------------------------------------
V2_COUNTRY_MAP = {
    8: "Albania",
    12: "Algeria",
    20: "Andorra",
    31: "Azerbaijan",
    32: "Argentina",
    36: "Australia",
    50: "Bangladesh",
    51: "Armenia",
    70: "Bosnia and Herzegovina",
    76: "Brazil",
    100: "Bulgaria",
    101: "Russian Federation",  # Tambov sub-sample → treat as Russia for GRI
    112: "Belarus",
    124: "Canada",
    152: "Chile",
    156: "China",
    158: "China, Taiwan Province of China",
    170: "Colombia",
    191: "Croatia",
    196: "Cyprus",
    203: "Czechia",
    214: "Dominican Republic",
    222: "El Salvador",
    231: "Ethiopia",
    233: "Estonia",
    246: "Finland",
    250: "France",
    268: "Georgia",
    276: "Germany",
    288: "Ghana",
    320: "Guatemala",
    344: "China, Hong Kong SAR",
    348: "Hungary",
    356: "India",
    360: "Indonesia",
    364: "Iran (Islamic Republic of)",
    368: "Iraq",
    376: "Israel",
    380: "Italy",
    392: "Japan",
    400: "Jordan",
    410: "Republic of Korea",
    417: "Kyrgyzstan",
    428: "Latvia",
    440: "Lithuania",
    458: "Malaysia",
    466: "Mali",
    484: "Mexico",
    498: "Republic of Moldova",
    499: "Montenegro",
    504: "Morocco",
    528: "Netherlands",
    554: "New Zealand",
    566: "Nigeria",
    578: "Norway",
    586: "Pakistan",
    604: "Peru",
    608: "Philippines",
    616: "Poland",
    630: "Puerto Rico",
    642: "Romania",
    643: "Russian Federation",
    646: "Rwanda",
    682: "Saudi Arabia",
    688: "Serbia",
    702: "Singapore",
    703: "Slovakia",
    704: "Viet Nam",
    705: "Slovenia",
    710: "South Africa",
    716: "Zimbabwe",
    724: "Spain",
    752: "Sweden",
    756: "Switzerland",
    764: "Thailand",
    780: "Trinidad and Tobago",
    792: "Türkiye",
    800: "Uganda",
    804: "Ukraine",
    807: "North Macedonia",
    818: "Egypt",
    826: "United Kingdom",
    834: "United Republic of Tanzania",
    840: "United States of America",
    854: "Burkina Faso",
    858: "Uruguay",
    862: "Venezuela (Bolivarian Republic of)",
    894: "Zambia",
    911: "United Kingdom",  # Northern Ireland → UK for GRI
    912: "Bosnia and Herzegovina",  # Republika Srpska → BiH for GRI
    914: "Montenegro",  # Pre-2006 code
}

# ---------------------------------------------------------------------------
# Gender mapping (consistent across all waves)
# ---------------------------------------------------------------------------
GENDER_MAP = {1: "Male", 2: "Female"}

# ---------------------------------------------------------------------------
# Religion mappings per wave → 7 GRI standard categories
# Validated against WVS Time Series harmonized F025 variable
# ---------------------------------------------------------------------------

# Wave 1: V179 (0-8 simple scheme, identical to F025)
WV1_RELIGION_MAP = {
    0: "Unaffiliated",   # No religious denomination
    1: "Christianity",   # Roman Catholic
    2: "Christianity",   # Protestant
    3: "Christianity",   # Orthodox
    4: "Judaism",        # Jewish
    5: "Islam",          # Muslim
    6: "Hinduism",       # Hindu
    7: "Buddhism",       # Buddhist
    8: "Other",          # Other
}

# Wave 2: V144 (non-sequential codes)
WV2_RELIGION_MAP = {
    0:  "Unaffiliated",   # No denomination
    5:  "Christianity",   # Anglican → Protestant
    9:  "Christianity",   # Baptist → Protestant
    12: "Buddhism",       # Buddhist
    17: "Other",          # Other Christian sect → Other
    28: "Christianity",   # Free church → Protestant
    31: "Hinduism",       # Hindu
    42: "Judaism",        # Jewish
    49: "Islam",          # Muslim
    52: "Christianity",   # Orthodox
    53: "Other",          # Other denomination
    61: "Christianity",   # Presbyterian → Protestant
    62: "Christianity",   # Protestant
    64: "Christianity",   # Roman Catholic
}

# Wave 3: V179 (53 substantive codes)
WV3_RELIGION_MAP = {
    1:  "Christianity",   # Roman Catholic
    2:  "Christianity",   # Protestant
    3:  "Christianity",   # Orthodox
    4:  "Judaism",        # Jewish
    5:  "Islam",          # Muslim
    6:  "Hinduism",       # Hindu
    7:  "Buddhism",       # Buddhist
    8:  "Christianity",   # Catholic sub-type
    10: "Christianity",   # Evangelical
    11: "Christianity",   # Protestant sub-type
    12: "Christianity",   # Protestant sub-type
    13: "Christianity",   # Protestant sub-type
    15: "Other",          # Other
    17: "Other",          # Traditional/folk religion
    19: "Christianity",   # Orthodox sub-type
    21: "Other",          # Other
    22: "Other",          # Other denomination
    30: "Christianity",   # Protestant sub-type
    37: "Christianity",   # Protestant sub-type
    40: "Other",          # Other denomination
    43: "Other",          # Other denomination
    44: "Christianity",   # Protestant sub-type
    47: "Christianity",   # Protestant sub-type
    48: "Other",          # Other denomination
    51: "Other",          # Other denomination
    54: "Other",          # Other denomination
    56: "Other",          # Other
    57: "Christianity",   # Protestant sub-type
    58: "Other",          # Other denomination
    59: "Other",          # Other
    65: "Christianity",   # Protestant sub-type
    66: "Christianity",   # Protestant sub-type
    67: "Islam",          # Sunni Muslim
    68: "Islam",          # Shia Muslim
    69: "Islam",          # Muslim sub-type
    70: "Islam",          # Muslim sub-type
    71: "Other",          # Other
    72: "Other",          # Other denomination
    73: "Christianity",   # Protestant sub-type
    74: "Other",          # Other denomination
    75: "Other",          # Other denomination
    76: "Christianity",   # Pentecostal
    77: "Christianity",   # Orthodox sub-type
    78: "Christianity",   # Armenian Apostolic etc.
    79: "Christianity",   # Protestant sub-type
    80: "Other",          # Other denomination
    81: "Other",          # Other denomination
    82: "Other",          # Other denomination
    83: "Other",          # Traditional/folk religion
    84: "Other",          # Ambiguous (n=6)
    85: "Other",          # Other denomination
    96: "Unaffiliated",   # No denomination
}

# Wave 4: V184G (grouped 0-9 scheme)
WV4_RELIGION_MAP = {
    0: "Unaffiliated",   # No denomination
    1: "Christianity",   # Roman Catholic
    2: "Christianity",   # Protestant
    3: "Christianity",   # Orthodox
    4: "Judaism",        # Jewish
    5: "Islam",          # Muslim
    6: "Hinduism",       # Hindu
    7: "Buddhism",       # Buddhist
    8: "Other",          # Other
    9: "Other",          # Heterogeneous catch-all (49% Muslim, 25% Prot, 17% Other)
}

# Wave 5: V185 (50 substantive codes)
WV5_RELIGION_MAP = {
    0:  "Unaffiliated",   # No denomination
    4:  "Other",          # Other denomination
    5:  "Christianity",   # Anglican → Protestant
    6:  "Christianity",   # Orthodox sub-type
    7:  "Christianity",   # Protestant sub-type
    8:  "Islam",          # Muslim sub-type
    9:  "Christianity",   # Baptist → Protestant
    12: "Buddhism",       # Buddhist
    14: "Other",          # Other
    17: "Other",          # Traditional/folk religion
    19: "Christianity",   # Protestant sub-type
    20: "Christianity",   # Protestant
    25: "Christianity",   # Independent churches (72% Protestant, 28% Other)
    28: "Christianity",   # Free church → Protestant
    29: "Christianity",   # Orthodox sub-type
    30: "Christianity",   # Orthodox sub-type
    31: "Hinduism",       # Hindu
    32: "Buddhism",       # Buddhist sub-type
    35: "Christianity",   # Protestant sub-type
    37: "Other",          # Other
    38: "Other",          # Other denomination
    39: "Other",          # Other
    42: "Judaism",        # Jewish
    44: "Christianity",   # Protestant sub-type
    46: "Christianity",   # Protestant sub-type
    48: "Other",          # Other
    49: "Islam",          # Muslim
    50: "Other",          # Other denomination
    52: "Christianity",   # Orthodox
    53: "Other",          # Other denomination
    54: "Other",          # Other denomination
    55: "Other",          # Other
    56: "Other",          # Other denomination
    60: "Christianity",   # Protestant sub-type
    61: "Christianity",   # Presbyterian → Protestant
    62: "Christianity",   # Protestant
    64: "Christianity",   # Roman Catholic
    66: "Christianity",   # Protestant sub-type
    68: "Christianity",   # Protestant sub-type
    70: "Islam",          # Sunni/Shia Muslim
    71: "Other",          # Other denomination
    73: "Other",          # Other denomination
    74: "Other",          # Other
    75: "Islam",          # Muslim sub-type
    77: "Other",          # Other denomination
    78: "Christianity",   # Pentecostal
    86: "Other",          # Other denomination
    87: "Other",          # Other denomination
    89: "Christianity",   # Protestant sub-type
    90: "Other",          # Other denomination
}

# ---------------------------------------------------------------------------
# Per-wave configuration
# ---------------------------------------------------------------------------
WAVE_CONFIG = {
    1: {
        "file": "WV1_Data_csv_v20200208.csv",
        "sex_var": "V214",
        "age_var": "V216",
        "religion_var": "V179",
        "religion_map": WV1_RELIGION_MAP,
        "env_primary": "V232",       # habitat 3-cat
        "env_fallback": None,
        "year_var": "S021",          # extract last 4 digits
        "year_method": "s021_suffix",
        "years": "1981-1984",
    },
    2: {
        "file": "WV2_Data_csv_v20180912.csv",
        "sex_var": "V353",
        "age_var": "V355",
        "religion_var": "V144",
        "religion_map": WV2_RELIGION_MAP,
        "env_primary": "V372",       # habitat 3-cat
        "env_fallback": "V368",      # size of town 1-8
        "year_var": "S021",
        "year_method": "s021_suffix",
        "years": "1989-1993",
    },
    3: {
        "file": "WV3_Data_csv_v20180912.csv",
        "sex_var": "V214",
        "age_var": "V216",
        "religion_var": "V179",
        "religion_map": WV3_RELIGION_MAP,
        "env_primary": None,
        "env_fallback": "V232",      # size of town 1-8 (same var name, different meaning!)
        "year_var": "S021",
        "year_method": "s021_suffix",
        "years": "1994-1999",
    },
    4: {
        "file": "WV4_Data_csv_v20201117.csv",
        "sex_var": "V223",
        "age_var": "V225",
        "religion_var": "V184G",
        "religion_map": WV4_RELIGION_MAP,
        "env_primary": "V248",       # urban/rural binary
        "env_fallback": "V241",      # size of town 1-8
        "year_var": "V246",
        "year_method": "direct",
        "years": "1999-2004",
    },
    5: {
        "file": "WV5_Data_csv_v20180912.csv",
        "sex_var": "V235",
        "age_var": "V237",
        "religion_var": "V185",
        "religion_map": WV5_RELIGION_MAP,
        "env_primary": "V263",       # urban/rural binary
        "env_fallback": "V255",      # size of town 1-8
        "year_var": "S021",
        "year_method": "s021_suffix",
        "years": "2005-2009",
    },
}


def age_to_group(age):
    """Convert continuous age to age group matching GRI standard."""
    if pd.isna(age) or age < 0:
        return np.nan
    age = int(age)
    if age < 18:
        return "Under 18"
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
        return "66+"


def derive_environment_habitat_3cat(series):
    """
    Derive Urban/Rural from a 3-category habitat variable.

    Wave 1 V232: 1=Rural, 2=Small/medium town, 3=Large town
    Wave 2 V372: 1=Farm/rural, 2=Rural village, 3=Urban (city/suburb)

    Small/medium towns, villages near cities, and suburban areas all map
    to Urban following GRI convention (Suburban → Urban).
    """
    env = pd.Series(np.nan, index=series.index, dtype=object)
    env[series == 1] = "Rural"
    env[series == 2] = "Urban"  # small-med town / rural village near city
    env[series == 3] = "Urban"  # large town / city-suburb
    return env


def derive_environment_urban_rural(series):
    """
    Derive Urban/Rural from a binary urban/rural variable.

    Waves 4-5: 1=Urban, 2=Rural, 3=Mixed/Suburban → Urban
    """
    env = pd.Series(np.nan, index=series.index, dtype=object)
    env[series == 1] = "Urban"
    env[series == 2] = "Rural"
    env[series == 3] = "Urban"  # Mixed/Suburban → Urban per GRI convention
    return env


def derive_environment_town_size(series):
    """
    Derive Urban/Rural from 8-point size-of-town scale.

    Standard WVS coding (documented in Wave 6 cross-national codebook):
      1 = Under 2,000          → Rural
      2 = 2,000 - 5,000        → Rural
      3 = 5,000 - 10,000       → Rural
      4 = 10,000 - 20,000      → Urban
      5 = 20,000 - 50,000      → Urban
      6 = 50,000 - 100,000     → Urban
      7 = 100,000 - 500,000    → Urban
      8 = 500,000 and more     → Urban

    Threshold: <10,000 = Rural, 10,000+ = Urban
    """
    env = pd.Series(np.nan, index=series.index, dtype=object)
    valid = series.between(1, 8)
    env[valid & (series <= 3)] = "Rural"
    env[valid & (series >= 4)] = "Urban"
    return env


def derive_environment(df, wave_num):
    """Derive environment for a wave using primary + fallback strategy."""
    cfg = WAVE_CONFIG[wave_num]
    env = pd.Series(np.nan, index=df.index, dtype=object)

    # Primary variable
    primary_var = cfg["env_primary"]
    if primary_var is not None and primary_var in df.columns:
        if wave_num in (1, 2):
            # 3-category habitat variable
            env = derive_environment_habitat_3cat(df[primary_var])
        elif wave_num in (4, 5):
            # Binary urban/rural
            env = derive_environment_urban_rural(df[primary_var])

    # Fallback: size-of-town variable
    fallback_var = cfg["env_fallback"]
    if fallback_var is not None and fallback_var in df.columns:
        missing = env.isna()
        if missing.any():
            fallback = derive_environment_town_size(df[fallback_var])
            env[missing] = fallback[missing]

    return env


def extract_year(df, wave_num):
    """Extract survey year from the appropriate variable."""
    cfg = WAVE_CONFIG[wave_num]
    year_var = cfg["year_var"]

    if year_var not in df.columns:
        return pd.Series(np.nan, index=df.index)

    if cfg["year_method"] == "s021_suffix":
        # Year encoded in last 4 digits of composite ID
        return df[year_var].astype(str).str[-4:].astype(int)
    else:
        # Direct year value
        years = df[year_var].copy()
        years[years < 0] = np.nan
        return years


def get_usecols(wave_num):
    """Get the list of columns to read for a given wave."""
    cfg = WAVE_CONFIG[wave_num]
    cols = ["V2", cfg["sex_var"], cfg["age_var"], cfg["religion_var"], cfg["year_var"]]
    if cfg["env_primary"] is not None:
        cols.append(cfg["env_primary"])
    if cfg["env_fallback"] is not None:
        cols.append(cfg["env_fallback"])
    return list(set(cols))  # deduplicate


def process_wave(input_dir, wave_num):
    """Read and process a single WVS wave from its cross-national CSV."""
    cfg = WAVE_CONFIG[wave_num]
    filepath = input_dir / cfg["file"]

    if not filepath.exists():
        print(f"  WARNING: File not found: {filepath}")
        return None

    print(f"  Loading {cfg['file']}...")
    usecols = get_usecols(wave_num)
    df = pd.read_csv(filepath, sep=";", encoding="utf-8-sig", usecols=usecols)
    print(f"  Raw rows: {len(df)}")

    # Build output
    result = pd.DataFrame()
    result["participant_id"] = range(1, len(df) + 1)

    # Country
    result["country"] = df["V2"].map(V2_COUNTRY_MAP)

    # Gender
    sex_col = cfg["sex_var"]
    result["gender"] = df[sex_col].map(GENDER_MAP)

    # Age and age group
    age_col = cfg["age_var"]
    age = df[age_col].copy()
    age[age < 0] = np.nan
    result["age"] = age.values
    result["age_group"] = result["age"].apply(age_to_group)

    # Religion
    religion_col = cfg["religion_var"]
    result["religion"] = df[religion_col].map(cfg["religion_map"])

    # Environment
    result["environment"] = derive_environment(df, wave_num).values

    # Year
    result["year"] = extract_year(df, wave_num).values

    # Metadata
    result["wave"] = wave_num
    result["survey"] = f"WVS_Wave_{wave_num}"

    # Drop rows missing essential fields
    before = len(result)
    result = result.dropna(subset=["country", "gender"])
    after = len(result)
    if before != after:
        print(f"  Dropped {before - after} rows with missing country/gender")

    # Report unmapped countries
    unmapped = df[~df["V2"].isin(V2_COUNTRY_MAP)]["V2"].unique()
    if len(unmapped) > 0:
        print(f"  WARNING: Unmapped country codes: {unmapped}")

    # Statistics
    env_total = result["environment"].notna().sum()
    env_pct = env_total / len(result) * 100
    rel_total = result["religion"].notna().sum()
    rel_pct = rel_total / len(result) * 100
    age_total = result["age_group"].notna().sum()
    age_pct = age_total / len(result) * 100

    print(f"  Final rows: {len(result)}")
    print(f"  Countries: {result['country'].nunique()}")
    print(f"  Gender: {result['gender'].value_counts().to_dict()}")
    print(f"  Age groups: {age_total}/{len(result)} ({age_pct:.1f}%)")
    print(f"  Religion: {rel_total}/{len(result)} ({rel_pct:.1f}%)")
    print(f"  Environment: {env_total}/{len(result)} ({env_pct:.1f}%)")
    if env_total > 0:
        urban = (result["environment"] == "Urban").sum()
        rural = (result["environment"] == "Rural").sum()
        print(f"    Urban={urban}, Rural={rural}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Process WVS Wave 1-5 cross-national CSVs into GRI format"
    )
    parser.add_argument(
        "--waves", nargs="+", type=int, default=[1, 2, 3, 4, 5],
        help="Wave numbers to process (default: 1 2 3 4 5)"
    )
    parser.add_argument(
        "--input-dir", type=str,
        default="data/raw/survey_data/wvs/WVS_data",
        help="Directory containing WVS cross-national CSV files"
    )
    parser.add_argument(
        "--output-dir", type=str,
        default="data/processed/surveys/wvs",
        help="Output directory for processed files"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return

    for wave_num in args.waves:
        print(f"\n{'='*60}")
        print(f"Processing WVS Wave {wave_num} ({WAVE_CONFIG[wave_num]['years']})")
        print(f"{'='*60}")

        result = process_wave(input_dir, wave_num)
        if result is None:
            continue

        output_file = output_dir / f"wvs_wave{wave_num}_participants_processed.csv"
        result.to_csv(output_file, index=False)
        print(f"  Saved to {output_file}")

    print(f"\nDone. Processed files are in {output_dir}/")


if __name__ == "__main__":
    main()
