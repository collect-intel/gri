"""
Process WVS Time Series data to extract individual wave participant files.

Reads the WVS Time Series 1981-2022 CSV and extracts Wave 4 and Wave 5 data
into the same processed format as wvs_wave6_participants_processed.csv.

Environment (Urban/Rural) Coding
================================
The WVS Time Series uses harmonized variable codes that differ from the
wave-specific codebooks. The environment derivation varies by wave:

Wave 5 (primary source: E248, fallback: E255):
  - E248 is the harmonized urban/rural variable (corresponds to wave-specific V263)
    Coding: 0 = Rural, 1 = Urban
    Coverage: 90.5% of Wave 5 respondents (76,028 / 83,975)
  - For respondents missing E248, E255 (collapsed size of town, 4-point scale)
    is used as fallback: E255=1 (smallest towns) -> Rural, E255>=2 -> Urban
  - "Mixed" responses from V263 (code 3) were mapped to Urban in E248 by the
    WVS time series harmonization, following WVS convention of treating
    suburban/mixed areas as urban

Wave 4 (source: X050C):
  - The time series does NOT carry E248, E255, or E241 for Wave 4
    (all are coded -4 "Not available")
  - X050C provides a binary urban/rural classification for 7 countries:
    Egypt, Indonesia, Iran, Iraq, Morocco, Mexico, Peru
    Coding: 1 = Urban, 2 = Rural (validated against Wave 5 E248 cross-tabulation)
    Coverage: 21.9% of Wave 4 respondents (13,138 / 60,045)
  - The remaining 78% of Wave 4 respondents have no environment data
    The original V248 and V241 variables from the Wave 4 codebook were not
    harmonized into the time series format

Size of Town -> Urban/Rural derivation (for reference):
  - The WVS Wave 6 cross-national file documents the standard conversion:
    V253 Size of Town codes 1-3 (under 10,000 population) -> Rural
    V253 Size of Town codes 4-8 (10,000+ population) -> Urban
  - This is consistent with the user-specified rule:
    <10,000 population = Rural, 10,000+ = Urban
  - "Mixed" / "Suburban" environments are mapped to Urban for GRI purposes,
    following the existing GRI convention (see config/segments.yaml)

Usage:
    python scripts/process_wvs_timeseries.py [--waves 4 5]
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path

# ISO3 -> country name mapping (from existing processed wave 6/7 + additions)
ISO3_TO_COUNTRY = {
    "ALB": "Albania",
    "AND": "Andorra",
    "ARE": "United Arab Emirates",
    "ARG": "Argentina",
    "ARM": "Armenia",
    "AUS": "Australia",
    "AUT": "Austria",
    "AZE": "Azerbaijan",
    "BFA": "Burkina Faso",
    "BGD": "Bangladesh",
    "BGR": "Bulgaria",
    "BIH": "Bosnia and Herzegovina",
    "BLR": "Belarus",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHE": "Switzerland",
    "CHL": "Chile",
    "CHN": "China",
    "COL": "Colombia",
    "CYP": "Cyprus",
    "CZE": "Czechia",
    "DEU": "Germany",
    "DZA": "Algeria",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ESP": "Spain",
    "EST": "Estonia",
    "ETH": "Ethiopia",
    "FIN": "Finland",
    "FRA": "France",
    "GBR": "United Kingdom",
    "GEO": "Georgia",
    "GHA": "Ghana",
    "GRC": "Greece",
    "GTM": "Guatemala",
    "HKG": "Hong Kong",
    "HRV": "Croatia",
    "HUN": "Hungary",
    "IDN": "Indonesia",
    "IND": "India",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "ISR": "Israel",
    "ITA": "Italy",
    "JOR": "Jordan",
    "JPN": "Japan",
    "KAZ": "Kazakhstan",
    "KEN": "Kenya",
    "KGZ": "Kyrgyzstan",
    "KOR": "South Korea",
    "KWT": "Kuwait",
    "LBN": "Lebanon",
    "LBY": "Libya",
    "LTU": "Lithuania",
    "LVA": "Latvia",
    "MAR": "Morocco",
    "MDA": "Moldova",
    "MEX": "Mexico",
    "MKD": "North Macedonia",
    "MLI": "Mali",
    "MNE": "Montenegro",
    "MYS": "Malaysia",
    "NGA": "Nigeria",
    "NLD": "Netherlands",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "PAK": "Pakistan",
    "PER": "Peru",
    "PHL": "Philippines",
    "POL": "Poland",
    "PRI": "Puerto Rico",
    "PRT": "Portugal",
    "QAT": "Qatar",
    "ROU": "Romania",
    "RUS": "Russia",
    "RWA": "Rwanda",
    "SAU": "Saudi Arabia",
    "SGP": "Singapore",
    "SRB": "Serbia",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "SWE": "Sweden",
    "THA": "Thailand",
    "TTO": "Trinidad and Tobago",
    "TUN": "Tunisia",
    "TUR": "Turkey",
    "TWN": "Taiwan",
    "TZA": "Tanzania",
    "UGA": "Uganda",
    "UKR": "Ukraine",
    "URY": "Uruguay",
    "USA": "United States",
    "UZB": "Uzbekistan",
    "VEN": "Venezuela",
    "VNM": "Vietnam",
    "YEM": "Yemen",
    "ZAF": "South Africa",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

# X049 religion code -> text label (WVS codebook)
RELIGION_MAP = {
    0: "No religious denomination",
    1: "Roman Catholic",
    2: "Protestant",
    3: "Orthodox",
    4: "Jew",
    5: "Muslim",
    6: "Hindu",
    7: "Buddhist",
    8: "Other",
    -1: "No answer",
}

# X001 sex code -> text label
GENDER_MAP = {
    1: "Male",
    2: "Female",
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


def derive_environment_wave5(wave_df):
    """
    Derive Urban/Rural environment for Wave 5 respondents.

    Primary: E248 (harmonized urban/rural, 0=Rural, 1=Urban)
    Fallback: E255 (collapsed size of town, 1=smallest -> Rural, 2-4 -> Urban)

    Returns a Series with 'Urban', 'Rural', or NaN.
    """
    env = pd.Series(np.nan, index=wave_df.index, dtype=object)

    # Primary: E248 (0=Rural, 1=Urban)
    e248 = wave_df["E248"]
    env[e248 == 0] = "Rural"
    env[e248 == 1] = "Urban"

    # Fallback: E255 for rows still missing
    missing_mask = env.isna() & (wave_df["E255"] >= 0)
    env.loc[missing_mask & (wave_df["E255"] == 1)] = "Rural"
    env.loc[missing_mask & (wave_df["E255"] >= 2)] = "Urban"

    return env


def derive_environment_wave4(wave_df):
    """
    Derive Urban/Rural environment for Wave 4 respondents.

    Uses X050C (binary urban/rural, 1=Urban, 2=Rural).
    Only available for 7 countries: EGY, IDN, IRN, IRQ, MAR, MEX, PER.
    Remaining respondents get NaN.

    Returns a Series with 'Urban', 'Rural', or NaN.
    """
    env = pd.Series(np.nan, index=wave_df.index, dtype=object)

    x050c = wave_df["X050C"]
    env[x050c == 1] = "Urban"
    env[x050c == 2] = "Rural"

    return env


def process_wave(ts_df, wave_num):
    """Extract and process a single wave from the time series DataFrame."""
    wave = ts_df[ts_df["S002VS"] == wave_num].copy()
    print(f"  Raw rows for wave {wave_num}: {len(wave)}")

    # Build output DataFrame
    result = pd.DataFrame()
    result["participant_id"] = range(1, len(wave) + 1)
    result["country"] = wave["COUNTRY_ALPHA"].map(ISO3_TO_COUNTRY).values
    result["iso3_code"] = wave["COUNTRY_ALPHA"].values

    # Gender
    result["gender"] = wave["X001"].map(GENDER_MAP).values

    # Age (continuous) and age group
    result["age"] = wave["X003"].values
    result["age"] = result["age"].apply(lambda x: x if x > 0 else np.nan)
    result["age_group"] = result["age"].apply(age_to_group)

    # Religion
    religion_raw = wave["X049"].values
    result["religion"] = pd.Series(religion_raw).map(RELIGION_MAP).values

    # Environment (Urban/Rural)
    if wave_num == 5:
        result["environment"] = derive_environment_wave5(wave).values
    elif wave_num == 4:
        result["environment"] = derive_environment_wave4(wave).values
    else:
        result["environment"] = np.nan

    # Metadata
    result["wave"] = wave_num
    result["survey"] = f"WVS_Wave_{wave_num}"
    result["year"] = wave["S020"].values

    # Drop rows with missing essential fields (gender, country)
    before = len(result)
    result = result.dropna(subset=["country", "gender"])
    after = len(result)
    if before != after:
        print(f"  Dropped {before - after} rows with missing country/gender")

    # Report unmapped countries
    unmapped = wave[~wave["COUNTRY_ALPHA"].isin(ISO3_TO_COUNTRY)]["COUNTRY_ALPHA"].unique()
    if len(unmapped) > 0:
        print(f"  WARNING: Unmapped country codes: {unmapped}")

    # Environment stats
    env_total = result["environment"].notna().sum()
    env_urban = (result["environment"] == "Urban").sum()
    env_rural = (result["environment"] == "Rural").sum()
    print(f"  Final rows: {len(result)}")
    print(f"  Countries: {result['country'].nunique()}")
    print(f"  Gender: {result['gender'].value_counts().to_dict()}")
    print(f"  Religion non-null: {result['religion'].notna().sum()} / {len(result)}")
    print(f"  Environment: {env_total} / {len(result)} "
          f"({env_total/len(result)*100:.1f}%) "
          f"[Urban={env_urban}, Rural={env_rural}]")

    return result


def main():
    parser = argparse.ArgumentParser(description="Process WVS Time Series into wave-level files")
    parser.add_argument("--waves", nargs="+", type=int, default=[4, 5],
                        help="Wave numbers to extract (default: 4 5)")
    parser.add_argument("--input", type=str,
                        default="data/raw/survey_data/wvs/WVS_Time_Series_1981-2022_csv_v5_0.csv",
                        help="Path to time series CSV")
    parser.add_argument("--output-dir", type=str,
                        default="data/processed/surveys/wvs",
                        help="Output directory for processed files")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading time series from {input_path}...")
    usecols = [
        "S002VS", "COUNTRY_ALPHA", "X001", "X003", "X049", "S020",
        "E248", "E255", "X050C",
    ]
    ts = pd.read_csv(input_path, usecols=usecols)
    print(f"  Total rows: {len(ts)}")
    print(f"  Waves available: {sorted(ts['S002VS'].unique())}")
    print()

    for wave_num in args.waves:
        print(f"Processing Wave {wave_num}...")
        result = process_wave(ts, wave_num)

        output_file = output_dir / f"wvs_wave{wave_num}_participants_processed.csv"
        result.to_csv(output_file, index=False)
        print(f"  Saved to {output_file}")
        print()


if __name__ == "__main__":
    main()
