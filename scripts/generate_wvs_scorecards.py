#!/usr/bin/env python3
"""
Generate GRI scorecards for all WVS waves (1-7).

Reads processed WVS participant files and produces GRI scorecards using
the same pipeline as the Global Dialogues scorecards, enabling direct
comparison between WVS and GD surveys.

Usage:
    python scripts/generate_wvs_scorecards.py [--waves 1 2 3 4 5 6 7]
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings
import yaml

sys.path.append(str(Path(__file__).parent.parent))

from gri import GRIScorecard


def load_wvs_data(base_path: Path, wave: int) -> pd.DataFrame:
    """Load processed WVS participant data and standardize for GRI."""
    filepath = base_path / f"data/processed/surveys/wvs/wvs_wave{wave}_participants_processed.csv"

    if not filepath.exists():
        raise FileNotFoundError(f"WVS Wave {wave} processed data not found at {filepath}")

    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df)} participants from {filepath.name}")

    # Standardize country names to match UN benchmark naming
    # Load the segments.yaml country mappings
    config_dir = base_path / "config"
    with open(config_dir / "segments.yaml", "r") as f:
        segments = yaml.safe_load(f)

    country_mappings = segments.get("benchmark_mappings", {}).get("country", {})
    reverse_map = {}
    for standard_name, variations in country_mappings.items():
        for variation in variations:
            reverse_map[variation] = standard_name

    df["country"] = df["country"].map(lambda x: reverse_map.get(x, x))

    # Standardize environment (Suburban → Urban, should already be done)
    if "environment" in df.columns:
        df["environment"] = df["environment"].replace({"Suburban": "Urban"})

    # Standardize religion labels to match GRI benchmark categories
    # The processing script outputs: Christianity, Islam, Hinduism, Buddhism,
    # Judaism, Unaffiliated, Other
    # GRI benchmarks use longer labels from Global Dialogues format
    religion_mapping = segments.get("survey_mappings", {}).get("world_values_survey", {}).get("religion", {})
    if religion_mapping:
        rev_religion = {}
        for standard_val, variations in religion_mapping.items():
            for v in variations:
                rev_religion[v] = standard_val
        df["religion"] = df["religion"].map(lambda x: rev_religion.get(x, x))

    # Filter to Male/Female only (benchmark data only has these)
    if "gender" in df.columns:
        df = df[df["gender"].isin(["Male", "Female"])]

    return df


def generate_scorecard_for_wave(wave: int, base_path: Path) -> tuple:
    """Generate GRI scorecard for a WVS wave."""
    print(f"\n{'='*60}")
    print(f"Generating scorecard for WVS Wave {wave}")
    print(f"{'='*60}")

    try:
        survey_df = load_wvs_data(base_path, wave)
    except FileNotFoundError as e:
        print(f"  Error: {e}")
        return None

    # Initialize scorecard generator
    scorecard_gen = GRIScorecard(simplification_mode="auto")

    # Generate scorecard
    threshold = max(1.0 / len(survey_df), 0.001)
    print(f"  Calculating scores (simplification threshold: {threshold*100:.3f}%)...")

    scorecard_df = scorecard_gen.generate_scorecard(
        survey_df,
        base_path,
        gd_num=None,
        include_extended=False,
    )

    # Add metadata columns
    scorecard_df["survey"] = f"WVS_Wave_{wave}"
    scorecard_df["n_participants"] = len(survey_df)

    print(f"  Generated {len(scorecard_df)} dimension scores")

    return scorecard_df


def main():
    parser = argparse.ArgumentParser(
        description="Generate GRI scorecards for WVS waves"
    )
    parser.add_argument(
        "--waves", nargs="+", type=int, default=[1, 2, 3, 4, 5, 6, 7],
        help="Wave numbers to process (default: 1 2 3 4 5 6 7)"
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

    for wave in args.waves:
        result = generate_scorecard_for_wave(wave, base_path)
        if result is not None:
            all_scorecards.append(result)

            # Save individual scorecard
            individual_file = output_dir / f"WVS_Wave_{wave}_scorecard.csv"
            result.to_csv(individual_file, index=False)
            print(f"  Saved to {individual_file}")

    if all_scorecards:
        # Combine all scorecards
        combined = pd.concat(all_scorecards, ignore_index=True)
        combined_file = output_dir / "WVS_combined_scorecards.csv"
        combined.to_csv(combined_file, index=False)
        print(f"\nCombined scorecards saved to {combined_file}")
        print(f"Total: {len(combined)} rows across {len(all_scorecards)} waves")

        # Print summary
        print("\n" + "="*80)
        print("SUMMARY: Key GRI scores across WVS waves")
        print("="*80)
        key_dims = [
            "Country × Gender × Age",
            "Country × Religion",
            "Country × Environment",
            "Country",
            "Gender",
            "Religion",
        ]
        for dim in key_dims:
            dim_data = combined[combined["dimension"] == dim]
            if not dim_data.empty:
                print(f"\n{dim}:")
                for _, row in dim_data.iterrows():
                    gri = row.get("gri", np.nan)
                    div = row.get("diversity", np.nan)
                    n = row.get("n_participants", "?")
                    print(f"  {row['survey']:15s}  GRI={gri:.3f}  Diversity={div:.3f}  N={n}")


if __name__ == "__main__":
    main()
