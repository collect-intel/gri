#!/usr/bin/env python3
"""
Analyze GD4 survey representativeness using the GRI framework.

This script:
1. Loads GD4 survey data
2. Loads benchmark population data
3. Calculates GRI scores for multiple dimensions
4. Identifies over/under-represented segments
5. Generates visualizations and reports
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

# Add parent directory to path to import gri module
sys.path.append(str(Path(__file__).parent.parent))

from gri.calculator import calculate_gri, calculate_diversity_score
from gri.analysis import (
    calculate_segment_deviations,
    identify_top_contributors,
    check_category_alignment
)
from gri.data_loader import load_benchmark_suite
from gri.visualization import plot_segment_deviations, plot_gri_scorecard


def load_gd4_data() -> pd.DataFrame:
    """Load and prepare GD4 survey data."""
    # Load participant-level data
    gd4_path = Path("data/raw/survey_data/global-dialogues/Data/GD4/GD4_participants.csv")
    
    if not gd4_path.exists():
        raise FileNotFoundError(f"GD4 participant data not found at {gd4_path}")
    
    # Load the data (skip first empty row)
    df = pd.read_csv(gd4_path, skiprows=1)
    
    # Rename columns to standard names
    column_mapping = {
        'What country or region do you most identify with?': 'country',
        'Please select your preferred language:': 'language', 
        'How old are you?': 'age_group',
        'What is your gender?': 'gender',
        'What best describes where you live?': 'environment',
        'What religious group or faith do you most identify with?': 'religion',
        'Overall, would you say the increased use of artificial intelligence (AI) in daily life makes you feel…': 'ai_sentiment'
    }
    
    # Apply column mapping if columns exist
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df[new_col] = df[old_col]
    
    # Standardize age groups to match benchmark data
    age_mapping = {
        '<18': '0-17',
        '18-25': '18-24',
        '26-35': '25-34',
        '36-45': '35-44',
        '46-55': '45-54',
        '56-65': '55-64',
        '65+': '65+'
    }
    
    if 'age_group' in df.columns:
        df['age_group'] = df['age_group'].map(age_mapping).fillna(df['age_group'])
    
    # Standardize gender
    gender_mapping = {
        'Female': 'Female',
        'Male': 'Male',
        'Non-binary': 'Other',
        'Other / prefer not to say': 'Other'
    }
    
    if 'gender' in df.columns:
        df['gender'] = df['gender'].map(gender_mapping).fillna(df['gender'])
    
    # Standardize environment
    env_mapping = {
        'Urban': 'Urban',
        'Suburban': 'Urban',  # Group suburban with urban for benchmark matching
        'Rural': 'Rural'
    }
    
    if 'environment' in df.columns:
        df['environment'] = df['environment'].map(env_mapping).fillna(df['environment'])
    
    # Ensure we have required columns
    required_cols = ['country', 'gender', 'age_group']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing columns: {missing_cols}")
        print(f"Available columns: {df.columns.tolist()}")
    
    return df


def analyze_gd4_representativeness():
    """Main analysis function."""
    print("=== GD4 Representativeness Analysis ===\n")
    
    # Load survey data
    print("Loading GD4 survey data...")
    try:
        survey_df = load_gd4_data()
        print(f"Loaded {len(survey_df)} unique participants")
        print(f"Countries represented: {survey_df['country'].nunique()}")
        print(f"Sample size by country:")
        print(survey_df['country'].value_counts().head(10))
        print()
    except Exception as e:
        print(f"Error loading GD4 data: {e}")
        return
    
    # Load benchmark data
    print("Loading benchmark data...")
    try:
        benchmarks = load_benchmark_suite()
        print(f"✓ Loaded {len(benchmarks)} benchmark dimensions")
        for dim in benchmarks:
            print(f"  - {dim}: {len(benchmarks[dim])} segments")
    except Exception as e:
        print(f"✗ Error loading benchmarks: {e}")
        return
    
    print()
    
    # Calculate GRI scores for each dimension
    results = {}
    dimension_configs = {
        'Country × Gender × Age': ['country', 'gender', 'age_group'],
        'Country × Religion': ['country', 'religion'],
        'Country × Environment': ['country', 'environment']
    }
    
    for dimension_name, columns in dimension_configs.items():
        if dimension_name not in benchmarks:
            continue
            
        print(f"\n=== Analyzing {dimension_name} ===")
        
        # Check if all required columns exist
        missing_cols = [col for col in columns if col not in survey_df.columns]
        if missing_cols:
            print(f"✗ Missing columns in survey data: {missing_cols}")
            continue
        
        # Check category alignment
        benchmark_df = benchmarks[dimension_name]
        alignment = check_category_alignment(survey_df, benchmark_df, columns)
        
        print(f"\nCategory Alignment:")
        for col, stats in alignment.items():
            if 'missing_in' in stats:
                print(f"  {col}: MISSING in {', '.join(stats['missing_in'])}")
            else:
                print(f"  {col}: {stats['coverage']:.1%} coverage ({stats['matched']}/{stats['total_survey']} matched)")
                if stats['unmatched']:
                    print(f"    Unmatched: {list(stats['unmatched'])[:5]}{'...' if len(stats['unmatched']) > 5 else ''}")
        
        # Calculate GRI score
        try:
            gri_score = calculate_gri(survey_df, benchmark_df, columns)
            diversity_score = calculate_diversity_score(survey_df, benchmark_df, columns)
            
            print(f"\nGRI Score: {gri_score:.3f}")
            print(f"Diversity Score: {diversity_score:.3f}")
            
            # Calculate segment deviations
            deviations = calculate_segment_deviations(survey_df, benchmark_df, columns)
            
            # Identify top over/under-represented segments
            top_over = identify_top_contributors(deviations, n=10, contribution_type='over')
            top_under = identify_top_contributors(deviations, n=10, contribution_type='under')
            
            print(f"\nTop 10 Over-represented Segments:")
            for _, seg in top_over.iterrows():
                segment_desc = ' - '.join(str(seg[col]) for col in columns)
                print(f"  {segment_desc}: sample={seg['sample_proportion']:.3f}, benchmark={seg['benchmark_proportion']:.3f}, diff=+{seg['deviation']:.3f}")
            
            print(f"\nTop 10 Under-represented Segments:")
            for _, seg in top_under.iterrows():
                segment_desc = ' - '.join(str(seg[col]) for col in columns)
                print(f"  {segment_desc}: sample={seg['sample_proportion']:.3f}, benchmark={seg['benchmark_proportion']:.3f}, diff={seg['deviation']:.3f}")
            
            # Store results
            results[dimension_name] = {
                'gri_score': gri_score,
                'diversity_score': diversity_score,
                'deviations': deviations,
                'top_over': top_over,
                'top_under': top_under,
                'alignment': alignment
            }
            
        except Exception as e:
            print(f"✗ Error calculating GRI: {e}")
    
    # Create output directory
    output_dir = Path("analysis_output/GD4")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    print(f"\n\nSaving results to {output_dir}/")
    
    # Save summary scores
    summary = {
        'survey': 'GD4',
        'total_participants': len(survey_df),
        'countries': survey_df['country'].nunique(),
        'scores': {}
    }
    
    for dimension, res in results.items():
        summary['scores'][dimension] = {
            'gri': res['gri_score'],
            'diversity': res['diversity_score'],
            'top_over_represented': res['top_over']['segment_name'].tolist() if 'segment_name' in res['top_over'].columns else [],
            'top_under_represented': res['top_under']['segment_name'].tolist() if 'segment_name' in res['top_under'].columns else []
        }
    
    with open(output_dir / "gd4_representativeness_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Save detailed deviation tables
    for dimension, res in results.items():
        safe_name = dimension.replace(' × ', '_x_').replace(' ', '_').lower()
        res['deviations'].to_csv(output_dir / f"gd4_deviations_{safe_name}.csv", index=False)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    
    # Create scorecard
    if results:
        scorecard_path = output_dir / "gd4_scorecard.png"
        # Create a DataFrame with both GRI and diversity scores
        scorecard_data = []
        for dim, res in results.items():
            scorecard_data.append({
                'dimension': dim,
                'gri_score': res['gri_score'],
                'diversity_score': res['diversity_score']
            })
        scorecard_df = pd.DataFrame(scorecard_data)
        
        fig = plot_gri_scorecard(
            scorecard_df,
            title="GD4 Representativeness Scorecard"
        )
        fig.savefig(scorecard_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Saved scorecard to {scorecard_path}")
    
    # Create deviation plots for Country × Gender × Age
    if 'Country × Gender × Age' in results:
        deviations = results['Country × Gender × Age']['deviations']
        # Get top deviations for visualization
        top_deviations = deviations.nlargest(20, 'abs_deviation')
        
        deviation_plot_path = output_dir / "gd4_top_deviations.png"
        fig = plot_segment_deviations(
            top_deviations,
            title="GD4: Top 20 Segment Deviations",
            top_n=20
        )
        fig.savefig(deviation_plot_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"✓ Saved deviation plot to {deviation_plot_path}")
    
    print("\n=== Analysis Complete ===")
    print(f"Results saved to: {output_dir}/")


if __name__ == "__main__":
    analyze_gd4_representativeness()