#!/usr/bin/env python3
"""
Top Contributing Segments Analysis Script

This script analyzes which demographic segments contribute most to the GRI score
by calculating deviation metrics for each stratum.
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add the gri module to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gri.utils import load_data


def calculate_segment_deviations(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, 
                                strata_cols: list, dimension_name: str) -> pd.DataFrame:
    """
    Calculate deviation metrics for each segment in a dimension.
    
    Args:
        survey_df: Survey data
        benchmark_df: Benchmark data  
        strata_cols: Columns defining the dimension strata
        dimension_name: Name of this dimension for reporting
        
    Returns:
        DataFrame with deviation metrics for each segment
    """
    # Calculate sample proportions
    sample_counts = survey_df.groupby(strata_cols).size().reset_index(name='sample_count')
    total_sample = len(survey_df)
    sample_counts['sample_proportion'] = sample_counts['sample_count'] / total_sample
    
    # Merge with benchmark data
    comparison = benchmark_df.merge(sample_counts, on=strata_cols, how='left')
    comparison['sample_count'] = comparison['sample_count'].fillna(0)
    comparison['sample_proportion'] = comparison['sample_proportion'].fillna(0)
    
    # Calculate deviation metrics
    comparison['absolute_deviation'] = np.abs(comparison['sample_proportion'] - comparison['population_proportion'])
    comparison['signed_deviation'] = comparison['sample_proportion'] - comparison['population_proportion']
    
    # GRI contribution: This segment's contribution to the total variation distance
    # TVD = 0.5 * sum(|s_i - q_i|), so each segment contributes |s_i - q_i| / 2
    comparison['gri_contribution_points'] = (comparison['absolute_deviation'] / 2) * 100
    
    # Deviation in percentage points: how many percentage points off from expected
    comparison['deviation_percentage_points'] = comparison['signed_deviation'] * 100
    
    # Over/under representation: ((s_i / q_i) - 1) * 100%
    # Handle division by zero for q_i = 0
    comparison['representation_ratio'] = np.where(
        comparison['population_proportion'] > 0,
        comparison['sample_proportion'] / comparison['population_proportion'],
        np.inf  # Infinite over-representation if population is 0 but sample has participants
    )
    
    comparison['over_under_representation_pct'] = np.where(
        comparison['population_proportion'] > 0,
        (comparison['representation_ratio'] - 1) * 100,
        np.where(comparison['sample_count'] > 0, np.inf, 0)
    )
    
    # Add dimension name and stratum description
    comparison['dimension'] = dimension_name
    comparison['stratum_id'] = comparison[strata_cols].apply(
        lambda x: ' × '.join([f"{col}:{val}" for col, val in zip(strata_cols, x)]), axis=1
    )
    
    # Add representation category
    comparison['representation_category'] = np.where(
        comparison['sample_count'] == 0, 'Missing',
        np.where(comparison['over_under_representation_pct'] > 50, 'Highly Over-represented',
        np.where(comparison['over_under_representation_pct'] > 0, 'Over-represented',
        np.where(comparison['over_under_representation_pct'] > -50, 'Under-represented',
                'Highly Under-represented')))
    )
    
    return comparison


def analyze_top_contributing_segments(survey_file: str, top_n: int = 20, 
                                    output_dir: str = "analysis_output") -> dict:
    """
    Analyze top contributing segments across all GRI dimensions.
    
    Args:
        survey_file: Path to processed survey data CSV
        top_n: Number of top segments to return for each dimension
        output_dir: Directory to save analysis results
        
    Returns:
        Dictionary with analysis results for each dimension
    """
    # Load data
    survey_data = load_data(survey_file)
    benchmark_age_gender = load_data('data/processed/benchmark_country_gender_age.csv')
    benchmark_religion = load_data('data/processed/benchmark_country_religion.csv')
    benchmark_environment = load_data('data/processed/benchmark_country_environment.csv')
    
    # Define dimensions
    dimensions = {
        'Country × Gender × Age': {
            'benchmark': benchmark_age_gender,
            'strata_cols': ['country', 'gender', 'age_group']
        },
        'Country × Religion': {
            'benchmark': benchmark_religion,
            'strata_cols': ['country', 'religion']
        },
        'Country × Environment': {
            'benchmark': benchmark_environment,
            'strata_cols': ['country', 'environment']
        }
    }
    
    results = {}
    all_segments = []
    
    # Analyze each dimension
    for dim_name, dim_config in dimensions.items():
        print(f"\nAnalyzing {dim_name}...")
        
        segment_analysis = calculate_segment_deviations(
            survey_data, 
            dim_config['benchmark'], 
            dim_config['strata_cols'],
            dim_name
        )
        
        # Get top contributing segments (highest absolute deviation)
        top_segments = segment_analysis.nlargest(top_n, 'gri_contribution_points')
        
        results[dim_name] = {
            'full_analysis': segment_analysis,
            'top_segments': top_segments,
            'summary_stats': {
                'total_segments': len(segment_analysis),
                'represented_segments': (segment_analysis['sample_count'] > 0).sum(),
                'missing_segments': (segment_analysis['sample_count'] == 0).sum(),
                'total_gri_contribution': segment_analysis['gri_contribution_points'].sum(),
                'top_10_contribution': top_segments.head(10)['gri_contribution_points'].sum()
            }
        }
        
        print(f"  Total segments: {results[dim_name]['summary_stats']['total_segments']}")
        print(f"  Represented: {results[dim_name]['summary_stats']['represented_segments']}")
        print(f"  Missing: {results[dim_name]['summary_stats']['missing_segments']}")
        print(f"  Top 10 segments contribute {results[dim_name]['summary_stats']['top_10_contribution']:.2f} percentage points to GRI")
        
        # Add to combined analysis
        all_segments.append(segment_analysis)
    
    # Create combined top segments analysis
    combined_segments = pd.concat(all_segments, ignore_index=True)
    top_overall = combined_segments.nlargest(top_n, 'gri_contribution_points')
    
    results['Overall'] = {
        'top_segments': top_overall,
        'summary_stats': {
            'total_segments_all_dims': len(combined_segments),
            'total_gri_impact': combined_segments['gri_contribution_points'].sum()
        }
    }
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract survey name from file path for output naming
    survey_name = Path(survey_file).stem.replace('_demographics', '')
    
    # Save individual dimension analyses
    for dim_name, dim_results in results.items():
        if dim_name != 'Overall':
            dim_filename = dim_name.lower().replace(' × ', '_').replace(' ', '_')
            output_file = output_path / f"{survey_name}_{dim_filename}_segment_analysis.csv"
            dim_results['top_segments'].to_csv(output_file, index=False)
            print(f"Saved {dim_name} analysis to {output_file}")
    
    # Save combined top segments
    combined_file = output_path / f"{survey_name}_top_contributing_segments.csv"
    top_overall.to_csv(combined_file, index=False)
    print(f"Saved combined analysis to {combined_file}")
    
    # Save summary report
    summary_file = output_path / f"{survey_name}_segment_analysis_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Top Contributing Segments Analysis: {survey_name.upper()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Survey: {survey_name.upper()}\n")
        f.write(f"Total participants: {len(survey_data):,}\n")
        f.write(f"Analysis date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for dim_name, dim_results in results.items():
            if dim_name != 'Overall':
                stats = dim_results['summary_stats']
                f.write(f"{dim_name}:\n")
                f.write(f"  Total segments: {stats['total_segments']:,}\n")
                f.write(f"  Represented segments: {stats['represented_segments']:,}\n")
                f.write(f"  Missing segments: {stats['missing_segments']:,}\n")
                f.write(f"  Coverage rate: {stats['represented_segments']/stats['total_segments']*100:.1f}%\n")
                f.write(f"  Top 10 segments contribute: {stats['top_10_contribution']:.2f} pp to GRI\n\n")
        
        # Top 10 overall segments
        f.write("TOP 10 CONTRIBUTING SEGMENTS (All Dimensions):\n")
        f.write("-" * 50 + "\n")
        for i, (_, segment) in enumerate(top_overall.head(10).iterrows(), 1):
            f.write(f"{i:2d}. {segment['stratum_id']} ({segment['dimension']})\n")
            f.write(f"    GRI Impact: {segment['gri_contribution_points']:.3f} pp\n")
            f.write(f"    Deviation: {segment['deviation_percentage_points']:+.2f} pp\n")
            f.write(f"    Representation: {segment['over_under_representation_pct']:+.1f}%\n")
            f.write(f"    Category: {segment['representation_category']}\n\n")
    
    print(f"Saved summary report to {summary_file}")
    
    return results


def main():
    """Main analysis function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze top contributing segments to GRI')
    parser.add_argument('survey_file', help='Path to processed survey data CSV')
    parser.add_argument('--top-n', type=int, default=20, help='Number of top segments to analyze')
    parser.add_argument('--output-dir', default='analysis_output', help='Output directory')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.survey_file):
        print(f"Error: Survey file not found: {args.survey_file}")
        sys.exit(1)
    
    print("Top Contributing Segments Analysis")
    print("=" * 50)
    print(f"Survey file: {args.survey_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Top N segments: {args.top_n}")
    
    results = analyze_top_contributing_segments(
        args.survey_file, 
        top_n=args.top_n, 
        output_dir=args.output_dir
    )
    
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    
    # Print quick summary
    overall_top = results['Overall']['top_segments'].head(5)
    print(f"\nTop 5 Contributing Segments:")
    for i, (_, segment) in enumerate(overall_top.iterrows(), 1):
        print(f"{i}. {segment['stratum_id']} - {segment['gri_contribution_points']:.3f} pp impact")


if __name__ == "__main__":
    main()