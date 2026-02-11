#!/usr/bin/env python3
"""
Process Pew Global Attitudes Survey SPSS files into GRI-compatible participant format.

Reads .sav files from the Pew Research Center's Global Attitudes Project and produces
standardized participant CSVs with columns: country, gender, age_group, religion, environment.

Data Source & License
=====================
Pew Research Center Global Attitudes Survey (2002-2024).
Free download with registration at https://www.pewresearch.org/global/datasets/
Licensed for academic and non-commercial use.

Usage
=====
    # First, explore a dataset to discover variable names and value labels:
    python scripts/process_pew_global.py --explore path/to/dataset.sav

    # Then process once you've confirmed/updated variable mappings:
    python scripts/process_pew_global.py --wave spring2024 path/to/dataset.sav

Variable Naming
===============
Pew datasets do NOT have standardized variable names across waves. Each wave
includes a codebook/readme. Common demographic variable patterns:

    Country:     COUNTRY, country, REGISTRATION
    Sex/Gender:  SEX, sex, GENDER, gender, Q_GENDER
    Age:         AGE, age, Q_AGE, topcoded_respondent_age, RECODE_AGE
    Religion:    RELIG, relig, RELIGION, Q_RELIGION
    Urban/Rural: URBAN, urban, URBRUR, COMMUNITY, community_type

The --explore flag will help identify the correct variables for any wave.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
import re

try:
    import pyreadstat
except ImportError:
    print("Error: pyreadstat required. Install with: pip install pyreadstat")
    sys.exit(1)


# ============================================================================
# Variable name candidates (searched in order; first match wins)
# ============================================================================

COUNTRY_VAR_CANDIDATES = [
    "COUNTRY", "country", "Country", "REGISTRATION",
    "COUNTRY_CAT", "country_cat",
]

GENDER_VAR_CANDIDATES = [
    "SEX", "sex", "Sex", "GENDER", "gender", "Gender",
    "Q_GENDER", "QGENDER", "RESPONDENT_SEX",
]

AGE_VAR_CANDIDATES = [
    "AGE", "age", "Age", "Q_AGE", "QAGE",
    "topcoded_respondent_age", "RESPONDENT_AGE", "RECODE_AGE",
    "AGE_RECODE", "age_recode",
]

RELIGION_VAR_CANDIDATES = [
    "religion_combined",  # Pew Spring 2024 (Q18a combined religion)
    "RELIG", "relig", "RELIGION", "religion", "Religion",
    "Q_RELIGION", "QRELIG", "RELIG_RECODE",
]

ENVIRONMENT_VAR_CANDIDATES = [
    "URBAN", "urban", "URBRUR", "urbrur",
    "COMMUNITY", "community", "COMMUNITY_TYPE", "community_type",
    "URBANICITY", "urbanicity", "URBAN_RURAL",
]

WEIGHT_VAR_CANDIDATES = [
    "WEIGHT", "weight", "Weight", "WT", "wt",
    "WEIGHT_GLOBAL", "weight_global",
]


# ============================================================================
# Standard GRI value mappings
# ============================================================================

# Gender: various Pew codings → Male/Female
GENDER_MAP = {
    # Numeric codes
    1: "Male", 2: "Female",
    # Text labels
    "Male": "Male", "Female": "Female",
    "Man": "Male", "Woman": "Female",
    "male": "Male", "female": "Female",
    "M": "Male", "F": "Female",
}

# Religion: Pew categories → GRI standard 7 categories
RELIGION_MAP = {
    # Christianity variants
    "Christian": "Christianity",
    "Catholic": "Christianity",
    "Protestant": "Christianity",
    "Orthodox": "Christianity",
    "Evangelical": "Christianity",
    "Roman Catholic": "Christianity",
    "Christian (Catholic)": "Christianity",
    "Christian (Protestant)": "Christianity",
    "Christian (Orthodox)": "Christianity",
    "Catholic (Roman Catholic)": "Christianity",
    "Just a Christian": "Christianity",
    "Jehovah's Witness": "Christianity",
    "Mormon": "Christianity",
    "Seventh-day Adventist": "Christianity",
    "Pentecostal": "Christianity",
    # Islam
    "Muslim": "Islam",
    "Sunni": "Islam",
    "Shia": "Islam",
    "Muslim (Sunni)": "Islam",
    "Muslim (Shia)": "Islam",
    # Buddhism
    "Buddhist": "Buddhism",
    # Hinduism
    "Hindu": "Hinduism",
    # Judaism
    "Jewish": "Judaism",
    "Jew": "Judaism",
    # Folk religions
    "Folk religion": "Folk Religions",
    "Traditional": "Folk Religions",
    "Animist": "Folk Religions",
    # Unaffiliated
    "Unaffiliated": "I do not identify with any religious group or faith",
    "Nothing in particular": "I do not identify with any religious group or faith",
    "Atheist": "I do not identify with any religious group or faith",
    "Agnostic": "I do not identify with any religious group or faith",
    "None": "I do not identify with any religious group or faith",
    "No religion": "I do not identify with any religious group or faith",
    "Religiously unaffiliated": "I do not identify with any religious group or faith",
    # Other
    "Other": "Other religious group",
    "Something else": "Other religious group",
    "Sikh": "Other religious group",
    "Jain": "Other religious group",
    "Confucian": "Other religious group",
    "Taoist": "Other religious group",
    "Shinto": "Other religious group",
}

# Environment: various Pew codings → Urban/Rural
ENVIRONMENT_MAP = {
    # Numeric
    1: "Urban", 2: "Rural",
    # Pew Spring 2024 urbanicity labels (face-to-face countries only)
    "Urban": "Urban",
    "Semi-Urban": "Urban",
    "Suburban/Mixed": "Urban",
    "Rural": "Rural",
    # Other common patterns
    "urban": "Urban", "rural": "Rural",
    "City": "Urban", "Village": "Rural",
    "Suburb": "Urban", "Suburban": "Urban",
    "Small town": "Rural", "Large city": "Urban",
    "Town": "Urban",
}

# Values to exclude from religion (refusals, don't know, insufficient sample, etc.)
RELIGION_EXCLUDE = {
    "DK/Refused", "Refused", "Don't know", "DK",
    "No answer", "Not asked", "Missing",
    "Everyone else without sufficient sample size for analysis",
    98, 99, -1, -2, 98.0, 99.0,
}


def find_variable(columns, candidates):
    """Find the first matching variable name from candidates."""
    col_set = set(columns)
    for candidate in candidates:
        if candidate in col_set:
            return candidate
    # Try case-insensitive partial match
    col_lower = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in col_lower:
            return col_lower[candidate.lower()]
    return None


def bin_age(age):
    """Bin continuous age into GRI standard age groups."""
    if pd.isna(age) or age < 16:
        return np.nan
    age = float(age)
    if age <= 25:
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


def explore_dataset(filepath: str):
    """Explore an SPSS dataset to discover variable names and value labels."""
    print(f"Exploring {filepath}...")
    print("=" * 70)

    # Read just metadata first (much faster for large files)
    _, meta = pyreadstat.read_sav(filepath, metadataonly=True)

    print(f"\nDataset: {len(meta.column_names)} variables")
    print(f"Column labels available: {len(meta.column_labels) > 0}")
    print(f"Value labels available: {len(meta.variable_value_labels) > 0}")

    # Show all variables with their labels
    print(f"\n{'Variable':<35} {'Label':<60}")
    print("-" * 95)
    for i, col in enumerate(meta.column_names):
        label = meta.column_labels[i] if i < len(meta.column_labels) else ""
        has_values = "  [has value labels]" if col in meta.variable_value_labels else ""
        print(f"{col:<35} {str(label)[:55]:<60}{has_values}")

    # Try to auto-detect GRI-relevant variables
    print(f"\n{'='*70}")
    print("AUTO-DETECTED GRI VARIABLES:")
    print(f"{'='*70}")

    detected = {}
    for name, candidates in [
        ("Country", COUNTRY_VAR_CANDIDATES),
        ("Gender", GENDER_VAR_CANDIDATES),
        ("Age", AGE_VAR_CANDIDATES),
        ("Religion", RELIGION_VAR_CANDIDATES),
        ("Environment", ENVIRONMENT_VAR_CANDIDATES),
        ("Weight", WEIGHT_VAR_CANDIDATES),
    ]:
        var = find_variable(meta.column_names, candidates)
        if var:
            detected[name] = var
            idx = list(meta.column_names).index(var)
            label = meta.column_labels[idx] if idx < len(meta.column_labels) else ""
            print(f"  {name:15s} → {var} ({label})")
            if var in meta.variable_value_labels:
                vals = meta.variable_value_labels[var]
                print(f"    Value labels ({len(vals)} values):")
                for k, v in list(vals.items())[:20]:
                    print(f"      {k}: {v}")
                if len(vals) > 20:
                    print(f"      ... and {len(vals) - 20} more")
        else:
            print(f"  {name:15s} → NOT FOUND (candidates: {', '.join(candidates[:5])})")

    if not detected:
        print("\n  No variables auto-detected. Showing all variables with value labels:")
        for var, labels in meta.variable_value_labels.items():
            idx = list(meta.column_names).index(var)
            col_label = meta.column_labels[idx] if idx < len(meta.column_labels) else ""
            print(f"\n  {var} ({col_label}): {len(labels)} values")
            for k, v in list(labels.items())[:10]:
                print(f"    {k}: {v}")

    # Read a small sample to show data types and value distributions
    print(f"\n{'='*70}")
    print("READING SAMPLE DATA (first 1000 rows)...")
    print(f"{'='*70}")

    df_sample, _ = pyreadstat.read_sav(filepath, apply_value_formats=True, row_limit=1000)
    print(f"Sample: {len(df_sample)} rows")

    for name, var in detected.items():
        if var in df_sample.columns:
            col = df_sample[var]
            print(f"\n  {name} ({var}): dtype={col.dtype}, nunique={col.nunique()}")
            print(f"    Top values:")
            for val, count in col.value_counts().head(10).items():
                print(f"      {repr(val)}: {count}")

    return detected


def process_pew_dataset(filepath: str, output_path: str,
                        country_var: str = None, gender_var: str = None,
                        age_var: str = None, religion_var: str = None,
                        environment_var: str = None, weight_var: str = None,
                        wave_name: str = "PewGlobal") -> pd.DataFrame:
    """Process a Pew Global Attitudes SPSS file into GRI participant format.

    If variable names are not specified, attempts auto-detection.
    """
    print(f"\nProcessing {filepath}...")
    print(f"Wave: {wave_name}")
    print("=" * 70)

    # Read with value labels
    df, meta = pyreadstat.read_sav(filepath, apply_value_formats=True)
    print(f"  Loaded {len(df)} rows × {len(df.columns)} columns")

    # Also read raw numeric codes for fallback mapping
    df_raw, _ = pyreadstat.read_sav(filepath, apply_value_formats=False)

    # Auto-detect variables if not specified
    if country_var is None:
        country_var = find_variable(df.columns, COUNTRY_VAR_CANDIDATES)
    if gender_var is None:
        gender_var = find_variable(df.columns, GENDER_VAR_CANDIDATES)
    if age_var is None:
        age_var = find_variable(df.columns, AGE_VAR_CANDIDATES)
    if religion_var is None:
        religion_var = find_variable(df.columns, RELIGION_VAR_CANDIDATES)
    if environment_var is None:
        environment_var = find_variable(df.columns, ENVIRONMENT_VAR_CANDIDATES)
    if weight_var is None:
        weight_var = find_variable(df.columns, WEIGHT_VAR_CANDIDATES)

    print(f"\n  Variable mapping:")
    print(f"    Country:     {country_var or 'NOT FOUND'}")
    print(f"    Gender:      {gender_var or 'NOT FOUND'}")
    print(f"    Age:         {age_var or 'NOT FOUND'}")
    print(f"    Religion:    {religion_var or 'NOT FOUND'}")
    print(f"    Environment: {environment_var or 'NOT FOUND'}")
    print(f"    Weight:      {weight_var or 'NOT FOUND'}")

    result = pd.DataFrame()

    # Country
    if country_var:
        result["country"] = df[country_var].astype(str).str.strip()
        print(f"\n  Countries: {result['country'].nunique()}")
        print(f"    {', '.join(sorted(result['country'].unique())[:10])}...")
    else:
        print("\n  WARNING: No country variable found!")
        return None

    # Gender
    if gender_var:
        gender_col = df[gender_var].astype(object).copy()
        # Pew uses country-specific gender variables (e.g., gender_australia)
        # that override the main gender variable for specific countries.
        for col in df.columns:
            if col.startswith(f"{gender_var}_") and col != gender_var:
                supplement = df[col].astype(object)
                mask = gender_col.isna() & supplement.notna()
                if mask.any():
                    country_name = col.replace(f"{gender_var}_", "").replace("_", " ").title()
                    gender_col.loc[mask] = supplement.loc[mask]
                    print(f"  Merged {mask.sum()} gender values from {col} ({country_name})")
        result["gender"] = gender_col.map(
            lambda x: GENDER_MAP.get(x, GENDER_MAP.get(str(x).strip(), np.nan))
            if pd.notna(x) else np.nan
        )
        n_valid = result["gender"].notna().sum()
        print(f"  Gender: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")
        if n_valid < len(df) * 0.5:
            print(f"    WARNING: Low gender coverage. Unique values: {gender_col.unique()[:10]}")
    else:
        print("  WARNING: No gender variable found!")

    # Age
    if age_var:
        age_col = df[age_var]
        # Check if already categorical or continuous
        if age_col.dtype in ['float64', 'int64', 'int32', 'float32']:
            result["age_group"] = age_col.apply(bin_age)
        else:
            # Try to extract numeric age from string
            result["age_group"] = age_col.apply(
                lambda x: bin_age(float(re.search(r'\d+', str(x)).group()))
                if pd.notna(x) and re.search(r'\d+', str(x))
                else np.nan
            )
        n_valid = result["age_group"].notna().sum()
        print(f"  Age: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")
    else:
        print("  WARNING: No age variable found!")

    # Religion
    if religion_var:
        relig_col = df[religion_var]
        result["religion"] = relig_col.map(
            lambda x: RELIGION_MAP.get(x, RELIGION_MAP.get(str(x).strip(), np.nan))
            if pd.notna(x) and x not in RELIGION_EXCLUDE and str(x).strip() not in RELIGION_EXCLUDE
            else np.nan
        )
        n_valid = result["religion"].notna().sum()
        print(f"  Religion: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")

        # Report unmapped values
        all_mapped = set(RELIGION_MAP.keys()) | RELIGION_EXCLUDE
        unmapped = relig_col[~relig_col.isin(all_mapped) & relig_col.notna()]
        str_mapped = {str(k).strip() for k in all_mapped}
        unmapped = unmapped[~unmapped.astype(str).str.strip().isin(str_mapped)]
        if len(unmapped) > 0:
            print(f"    Unmapped religion values ({len(unmapped)} rows):")
            for v, c in unmapped.value_counts().head(15).items():
                print(f"      {repr(v)}: {c}")
    else:
        print("  WARNING: No religion variable found!")

    # Environment (Urban/Rural)
    if environment_var:
        env_col = df[environment_var]
        result["environment"] = env_col.map(
            lambda x: ENVIRONMENT_MAP.get(x, ENVIRONMENT_MAP.get(str(x).strip(), np.nan))
            if pd.notna(x) else np.nan
        )
        n_valid = result["environment"].notna().sum()
        print(f"  Environment: {n_valid}/{len(df)} valid ({n_valid/len(df)*100:.1f}%)")
        if n_valid < len(df) * 0.5:
            print(f"    WARNING: Low environment coverage. Unique values:")
            for v, c in env_col.value_counts().head(10).items():
                print(f"      {repr(v)}: {c}")
    else:
        print("  WARNING: No environment variable found. Dimension will be omitted.")

    # Summary
    print(f"\n  Religion distribution (GRI categories):")
    if "religion" in result.columns:
        for val, count in result["religion"].value_counts().items():
            print(f"    {val}: {count} ({count/len(result)*100:.1f}%)")

    print(f"\n  Final dataset: {len(result)} rows")
    for col in ["country", "gender", "age_group", "religion", "environment"]:
        if col in result.columns:
            n = result[col].notna().sum()
            print(f"    {col}: {n} valid ({n/len(result)*100:.1f}%)")

    # Save
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_file, index=False)
    print(f"\n  Saved {len(result)} participants to {output_file}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Process Pew Global Attitudes Survey data for GRI scoring"
    )
    parser.add_argument("input_file", help="Path to SPSS .sav file")
    parser.add_argument("--explore", action="store_true",
                        help="Explore dataset variables without processing")
    parser.add_argument("--wave", type=str, default="PewGlobal",
                        help="Wave name for output file (e.g., spring2024)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output CSV path (default: auto-generated)")
    parser.add_argument("--country-var", type=str, default=None,
                        help="Override country variable name")
    parser.add_argument("--gender-var", type=str, default=None,
                        help="Override gender variable name")
    parser.add_argument("--age-var", type=str, default=None,
                        help="Override age variable name")
    parser.add_argument("--religion-var", type=str, default=None,
                        help="Override religion variable name")
    parser.add_argument("--environment-var", type=str, default=None,
                        help="Override environment/urban-rural variable name")

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found at {input_path}")
        sys.exit(1)

    if args.explore:
        explore_dataset(str(input_path))
        return

    # Default output path
    if args.output is None:
        base_path = Path(__file__).parent.parent
        output_path = (base_path / "data/processed/surveys/pew_global_attitudes"
                       / f"pew_{args.wave}_participants_processed.csv")
    else:
        output_path = Path(args.output)

    process_pew_dataset(
        str(input_path),
        str(output_path),
        country_var=args.country_var,
        gender_var=args.gender_var,
        age_var=args.age_var,
        religion_var=args.religion_var,
        environment_var=args.environment_var,
        wave_name=args.wave,
    )


if __name__ == "__main__":
    main()
