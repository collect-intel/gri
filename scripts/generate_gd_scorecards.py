#!/usr/bin/env python3
"""
Generate comprehensive GRI scorecards for Global Dialogues surveys.

This script produces scorecards with GRI, Diversity, SRI, VWRS scores
and maximum possible scores for all dimensions defined in config/dimensions.yaml.

Usage:
    python generate_gd_scorecards.py [--gd GD_NUM] [--format FORMAT] [--output OUTPUT_DIR]
    
    --gd: GD number (1, 2, or 3). If not specified, generates for all GDs.
    --format: Output format (csv, text, markdown). Default: csv
    --output: Output directory. Default: analysis_output/scorecards/
"""

import argparse
import pandas as pd
from pathlib import Path
import sys
import warnings

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from gri import GRIScorecard


def load_gd_data(base_path: Path, gd_num: int) -> pd.DataFrame:
    """Load GD survey data and standardize columns."""
    file_path = base_path / f'data/raw/survey_data/global-dialogues/Data/GD{gd_num}/GD{gd_num}_participants.csv'
    
    if not file_path.exists():
        raise FileNotFoundError(f"GD{gd_num} data not found at {file_path}. Please ensure the data file exists or check if you meant a different GD number.")
    
    df = pd.read_csv(file_path)
    
    # Standardize column names
    column_mapping = {
        'What country or region do you most identify with?': 'country',
        'What is your gender?': 'gender',
        'How old are you?': 'age_group',
        'What best describes where you live?': 'environment',
        'What religious group or faith do you most identify with?': 'religion'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Standardize environment values (merge Suburban into Urban)
    if 'environment' in df.columns:
        df['environment'] = df['environment'].replace({'Suburban': 'Urban'})
    
    # Filter out non-standard gender values for GRI calculation
    # (as benchmark data only has Male/Female)
    if 'gender' in df.columns:
        df = df[df['gender'].isin(['Male', 'Female'])]
    
    return df


def generate_scorecard_for_gd(gd_num: int, base_path: Path, format: str = 'csv',
                            simplification_mode: str = 'auto') -> str:
    """Generate scorecard for a specific GD survey.
    
    Args:
        gd_num: GD survey number
        base_path: Base path for project
        format: Output format
        simplification_mode: How to handle high-cardinality benchmarks
                           'none' - Use full benchmarks
                           'auto' - Formulaic simplification (default)
                           'legacy' - Use hard-coded 31 countries
    """
    print(f"\nGenerating scorecard for GD{gd_num}...")
    
    # Load survey data
    try:
        survey_df = load_gd_data(base_path, gd_num)
        print(f"  Loaded {len(survey_df)} participants")
    except FileNotFoundError as e:
        print(f"  Error: {e}")
        return None
    
    # Initialize scorecard generator
    scorecard_gen = GRIScorecard(simplification_mode=simplification_mode)
    
    # Generate scorecard
    print("  Calculating scores for all dimensions...")
    if simplification_mode == 'legacy':
        print("  Using legacy simplified benchmarks (31 major countries)")
    elif simplification_mode == 'auto':
        threshold = max(1.0 / len(survey_df), 0.001)
        print(f"  Using formulaic simplification (threshold: {threshold*100:.3f}%)")
    
    scorecard_df = scorecard_gen.generate_scorecard(
        survey_df,
        base_path,
        gd_num=gd_num,
        include_extended=False  # Only standard dimensions
    )
    
    # Format output
    formatted = scorecard_gen.format_scorecard(scorecard_df, format=format)
    
    # Add metadata header for text/markdown formats
    if format in ['text', 'markdown']:
        header = f"Global Dialogues {gd_num} (GD{gd_num}) Scorecard\n"
        header += f"Sample size: {len(survey_df)} participants\n"
        header += "=" * 80 + "\n\n"
        formatted = header + formatted
    
    return formatted, scorecard_df


def main():
    parser = argparse.ArgumentParser(
        description='Generate GRI scorecards for Global Dialogues surveys'
    )
    parser.add_argument(
        '--gd', 
        type=int, 
        help='GD number. If not specified, generates for all available GDs.'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'text', 'markdown'],
        default='csv',
        help='Output format (default: csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='analysis_output/scorecards',
        help='Output directory (default: analysis_output/scorecards)'
    )
    parser.add_argument(
        '--mode',
        choices=['none', 'auto', 'legacy'],
        default='auto',
        help='Simplification mode: none (full), auto (formulaic), legacy (31 countries)'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    base_path = Path(__file__).parent.parent
    output_dir = base_path / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine which GDs to process
    if args.gd:
        gd_nums = [args.gd]
    else:
        # Find all available GD data files
        gd_data_dir = base_path / 'data/raw/survey_data/global-dialogues/Data'
        available_gds = []
        if gd_data_dir.exists():
            for gd_dir in sorted(gd_data_dir.glob('GD*')):
                if gd_dir.is_dir():
                    try:
                        gd_num = int(gd_dir.name[2:])  # Extract number from "GD1", "GD2", etc.
                        # Check if participant file exists
                        participant_file = gd_dir / f'GD{gd_num}_participants.csv'
                        if participant_file.exists():
                            available_gds.append(gd_num)
                    except ValueError:
                        continue
        
        if not available_gds:
            print("No GD data files found!")
            return
            
        gd_nums = available_gds
        print(f"Found GD data for: {', '.join(f'GD{n}' for n in gd_nums)}")
    
    # Process each GD
    for gd_num in gd_nums:
        result = generate_scorecard_for_gd(gd_num, base_path, args.format, 
                                         simplification_mode=args.mode)
        
        if result is None:
            continue
            
        formatted_output, scorecard_df = result
        
        # Determine file extension
        ext = {
            'csv': '.csv',
            'text': '.txt',
            'markdown': '.md'
        }[args.format]
        
        # Save output
        output_file = output_dir / f'GD{gd_num}_scorecard{ext}'
        with open(output_file, 'w') as f:
            f.write(formatted_output)
        
        print(f"  Saved to: {output_file}")
        
        # Also save raw DataFrame as CSV for further analysis
        if args.format != 'csv':
            csv_file = output_dir / f'GD{gd_num}_scorecard.csv'
            scorecard_df.to_csv(csv_file, index=False)
            print(f"  Also saved raw data to: {csv_file}")
    
    print("\nScorecard generation complete!")


if __name__ == "__main__":
    main()