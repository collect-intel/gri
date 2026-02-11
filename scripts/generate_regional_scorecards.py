#!/usr/bin/env python3
"""
Generate GRI scorecards for multi-country survey datasets.

Surveys claim to represent specific sets of countries, not necessarily the global
population. The GRI framework measures CLAIMED representativeness, so benchmarks
are filtered to only the countries each survey targets and proportions are
renormalized accordingly.

For example, Afrobarometer R9 covers 39 African countries — its GRI measures
how well its sample represents those 39 countries' combined population across
gender, age, religion, and urbanization dimensions.

Supported surveys:
  - Afrobarometer R9: 39 African countries
  - Latinobarómetro 2023/2024: 17 Latin American countries
  - Pew Global Attitudes Spring 2024: 35 countries across all continents

Usage:
    python scripts/generate_regional_scorecards.py
    python scripts/generate_regional_scorecards.py --surveys afrobarometer_r9
    python scripts/generate_regional_scorecards.py --surveys pew_spring2024
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from gri import GRIScorecard


# Survey definitions
SURVEYS = {
    "afrobarometer_r9": {
        "file": "afrobarometer/afrobarometer_r9_participants_processed.csv",
        "display": "Afrobarometer_R9",
        "description": "Afrobarometer Round 9 (2021-2023), 39 African countries",
    },
    "latinobarometro_2023": {
        "file": "latinobarometro/latinobarometro_2023_participants_processed.csv",
        "display": "Latinobarometro_2023",
        "description": "Latinobarómetro 2023, 17 Latin American countries",
    },
    "latinobarometro_2024": {
        "file": "latinobarometro/latinobarometro_2024_participants_processed.csv",
        "display": "Latinobarometro_2024",
        "description": "Latinobarómetro 2024, 17 Latin American countries",
    },
    "pew_spring2024": {
        "file": "pew_global_attitudes/pew_spring2024_participants_processed.csv",
        "display": "Pew_Spring2024",
        "description": "Pew Global Attitudes Spring 2024, 35 countries worldwide",
    },
}


def load_survey_data(filepath: Path, base_path: Path) -> pd.DataFrame:
    """Load processed survey data and apply standard transformations."""
    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df)} participants from {filepath.name}")

    # Apply country name standardization via segments.yaml
    config_dir = base_path / "config"
    with open(config_dir / "segments.yaml", "r") as f:
        segments = yaml.safe_load(f)

    country_mappings = segments.get("benchmark_mappings", {}).get("country", {})
    reverse_map = {}
    for standard_name, variations in country_mappings.items():
        for variation in variations:
            reverse_map[variation] = standard_name

    df["country"] = df["country"].map(lambda x: reverse_map.get(x, x))

    # Apply religion label standardization
    religion_mapping = segments.get("survey_mappings", {}).get("world_values_survey", {}).get("religion", {})
    if religion_mapping:
        rev_religion = {}
        for standard_val, variations in religion_mapping.items():
            for v in variations:
                rev_religion[v] = standard_val
        df["religion"] = df["religion"].map(lambda x: rev_religion.get(x, x))

    # Filter to Male/Female only
    if "gender" in df.columns:
        df = df[df["gender"].isin(["Male", "Female"])]

    return df


def generate_scorecard(survey_key: str, base_path: Path, output_dir: Path) -> pd.DataFrame:
    """Generate GRI scorecard for a regional survey with country-filtered benchmarks."""
    survey_info = SURVEYS[survey_key]
    filepath = base_path / "data/processed/surveys" / survey_info["file"]

    print(f"\n{'='*60}")
    print(f"Generating scorecard for {survey_info['display']}")
    print(f"  {survey_info['description']}")
    print(f"{'='*60}")

    if not filepath.exists():
        print(f"  Error: File not found at {filepath}")
        return None

    survey_df = load_survey_data(filepath, base_path)

    # Extract the list of countries this survey claims to represent
    country_filter = sorted(survey_df["country"].dropna().unique().tolist())
    print(f"  Country filter: {len(country_filter)} countries")

    # Initialize scorecard with regional benchmark filtering
    scorecard_gen = GRIScorecard(
        simplification_mode="auto",
        country_filter=country_filter,
    )

    # Generate scorecard
    print(f"  Calculating scores for {len(survey_df)} participants...")
    print(f"  (benchmarks restricted to claimed {len(country_filter)}-country population)")

    scorecard_df = scorecard_gen.generate_scorecard(
        survey_df,
        base_path,
        gd_num=None,
        include_extended=False,
    )

    # Add metadata
    scorecard_df["survey"] = survey_info["display"]
    scorecard_df["n_participants"] = len(survey_df)
    scorecard_df["n_countries_claimed"] = len(country_filter)

    # Save individual scorecard
    output_file = output_dir / f"{survey_info['display']}_scorecard.csv"
    scorecard_df.to_csv(output_file, index=False)
    print(f"  Saved {len(scorecard_df)} dimension scores to {output_file}")

    return scorecard_df


def main():
    parser = argparse.ArgumentParser(
        description="Generate GRI scorecards for regional surveys"
    )
    parser.add_argument(
        "--surveys", nargs="+", default=list(SURVEYS.keys()),
        choices=list(SURVEYS.keys()),
        help="Surveys to process (default: all)"
    )
    parser.add_argument(
        "--output", type=str, default="analysis_output/scorecards",
        help="Output directory (default: analysis_output/scorecards)"
    )
    args = parser.parse_args()

    base_path = Path(__file__).parent.parent
    output_dir = base_path / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    all_scorecards = []

    for survey_key in args.surveys:
        result = generate_scorecard(survey_key, base_path, output_dir)
        if result is not None:
            all_scorecards.append(result)

    if all_scorecards:
        combined = pd.concat(all_scorecards, ignore_index=True)

        print("\n" + "=" * 80)
        print("SUMMARY: Regional GRI scores (benchmarked against claimed population)")
        print("=" * 80)

        key_dims = [
            "Country × Gender × Age",
            "Country × Religion",
            "Country × Environment",
            "Country",
            "Gender",
            "Religion",
            "Environment",
            "Age Group",
            "Overall (Average)",
        ]
        for dim in key_dims:
            dim_data = combined[combined["dimension"] == dim]
            if not dim_data.empty:
                print(f"\n{dim}:")
                for _, row in dim_data.iterrows():
                    gri = row.get("gri", np.nan)
                    div = row.get("diversity", np.nan)
                    deff = row.get("design_effect", np.nan)
                    uncov = row.get("uncovered_population", np.nan)
                    n = row.get("n_participants", "?")
                    nc = row.get("n_countries_claimed", "?")
                    deff_str = f"Deff={deff:.1f}" if pd.notna(deff) else ""
                    uncov_str = f"Uncov={uncov:.3f}" if pd.notna(uncov) else ""
                    print(f"  {row['survey']:25s}  GRI={gri:.3f}  Div={div:.3f}  {deff_str:>10}  {uncov_str:>12}  N={n} ({nc} countries)")


if __name__ == "__main__":
    main()
