"""
Report generation utilities for Global Representativeness Index analysis.

This module provides functions for creating text reports, exporting results,
and generating summary statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, TextIO
from pathlib import Path
import json
import csv
from datetime import datetime


def generate_text_report(
    scorecard: Union[pd.DataFrame, Dict[str, Any]],
    survey_name: Optional[str] = None,
    include_analysis: bool = True,
    include_max_possible: bool = False,
    output_file: Optional[Union[str, Path, TextIO]] = None
) -> str:
    """
    Generate comprehensive text report from GRI scorecard.
    
    Parameters
    ----------
    scorecard : pd.DataFrame or dict
        GRI scorecard results
    survey_name : str, optional
        Name of the survey for the report header
    include_analysis : bool, default=True
        Whether to include detailed analysis
    include_max_possible : bool, default=False
        Whether to include max possible scores (if available)
    output_file : str, Path, or file-like, optional
        Where to save the report
        
    Returns
    -------
    str
        The generated report text
        
    Examples
    --------
    >>> report = generate_text_report(scorecard, "Global Dialogues 3")
    >>> print(report[:100])  # First 100 chars
    """
    # Convert dict to DataFrame if needed
    if isinstance(scorecard, dict):
        if 'results' in scorecard:
            df = pd.DataFrame(scorecard['results'])
        else:
            df = pd.DataFrame([scorecard])
    else:
        df = scorecard.copy()
    
    # Build report
    lines = []
    lines.append("=" * 70)
    lines.append("GLOBAL REPRESENTATIVENESS INDEX (GRI) REPORT")
    lines.append("=" * 70)
    
    # Header info
    if survey_name:
        lines.append(f"Survey: {survey_name}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Sample size info
    if 'sample_size' in df.columns:
        total_sample = df['sample_size'].iloc[0] if len(df) > 0 else 'Unknown'
        lines.append(f"Total Sample Size: {total_sample:,}" if isinstance(total_sample, int) else f"Total Sample Size: {total_sample}")
    
    lines.append("")
    
    # Overall summary
    lines.append("SUMMARY")
    lines.append("-" * 70)
    
    if 'gri_score' in df.columns:
        mean_gri = df['gri_score'].mean()
        lines.append(f"Average GRI Score: {mean_gri:.4f}")
        
        # Classification
        if mean_gri >= 0.9:
            classification = "Excellent"
        elif mean_gri >= 0.8:
            classification = "Good"
        elif mean_gri >= 0.7:
            classification = "Fair"
        else:
            classification = "Poor"
        
        lines.append(f"Overall Representation: {classification}")
    
    if 'diversity_score' in df.columns:
        mean_diversity = df['diversity_score'].mean()
        lines.append(f"Average Diversity Score: {mean_diversity:.4f}")
    
    lines.append("")
    
    # Detailed results by dimension
    lines.append("RESULTS BY DIMENSION")
    lines.append("-" * 70)
    
    for idx, row in df.iterrows():
        dimension = row.get('dimension', f'Dimension {idx+1}')
        lines.append(f"\n{dimension}:")
        
        # GRI Score
        if 'gri_score' in row:
            gri = row['gri_score']
            lines.append(f"  GRI Score: {gri:.4f}")
            
            # Add max possible if available
            if include_max_possible and 'max_possible_score' in row:
                max_score = row['max_possible_score']
                efficiency = row.get('efficiency_ratio', gri/max_score if max_score > 0 else 0)
                lines.append(f"  Maximum Possible: {max_score:.4f}")
                lines.append(f"  Efficiency: {efficiency:.1%}")
        
        # Diversity Score
        if 'diversity_score' in row:
            diversity = row['diversity_score']
            lines.append(f"  Diversity Score: {diversity:.4f}")
            
            if include_max_possible and 'max_possible_diversity' in row:
                max_div = row['max_possible_diversity']
                div_efficiency = row.get('diversity_efficiency', diversity/max_div if max_div > 0 else 0)
                lines.append(f"  Maximum Possible Diversity: {max_div:.4f}")
                lines.append(f"  Diversity Efficiency: {div_efficiency:.1%}")
        
        # Coverage info
        if 'coverage_rate' in row:
            lines.append(f"  Coverage Rate: {row['coverage_rate']:.1%}")
        
        if 'total_categories' in row:
            represented = row.get('represented_categories', 0)
            total = row['total_categories']
            lines.append(f"  Categories: {represented}/{total} represented")
    
    # Analysis section
    if include_analysis:
        lines.append("\n" + "="*70)
        lines.append("ANALYSIS")
        lines.append("="*70)
        
        # Best and worst dimensions
        if 'gri_score' in df.columns and len(df) > 1:
            best_dim = df.loc[df['gri_score'].idxmax()]
            worst_dim = df.loc[df['gri_score'].idxmin()]
            
            lines.append("\nBest Represented Dimension:")
            lines.append(f"  {best_dim['dimension']}: {best_dim['gri_score']:.4f}")
            
            lines.append("\nLeast Represented Dimension:")
            lines.append(f"  {worst_dim['dimension']}: {worst_dim['gri_score']:.4f}")
            
            # Gap analysis
            gap = best_dim['gri_score'] - worst_dim['gri_score']
            lines.append(f"\nRepresentation Gap: {gap:.4f}")
        
        # Recommendations
        lines.append("\nRECOMMENDATIONS:")
        
        if 'gri_score' in df.columns:
            low_scoring = df[df['gri_score'] < 0.8]
            if len(low_scoring) > 0:
                lines.append("  Priority dimensions for improvement:")
                for _, row in low_scoring.iterrows():
                    lines.append(f"    - {row['dimension']} (GRI: {row['gri_score']:.4f})")
            else:
                lines.append("  All dimensions show good representation (GRI >= 0.8)")
    
    lines.append("\n" + "="*70)
    
    # Join lines
    report = '\n'.join(lines)
    
    # Save if requested
    if output_file:
        if isinstance(output_file, (str, Path)):
            with open(output_file, 'w') as f:
                f.write(report)
        else:
            output_file.write(report)
    
    return report


def export_results(
    scorecard: Union[pd.DataFrame, Dict[str, Any]],
    format: str = 'csv',
    filepath: Optional[Union[str, Path]] = None,
    include_metadata: bool = True
) -> Optional[Union[str, Dict]]:
    """
    Export GRI results in various formats.
    
    Parameters
    ----------
    scorecard : pd.DataFrame or dict
        Results to export
    format : {'csv', 'json', 'excel'}, default='csv'
        Export format
    filepath : str or Path, optional
        Output file path. If None, returns the data.
    include_metadata : bool, default=True
        Whether to include metadata in export
        
    Returns
    -------
    str or dict or None
        Exported data if filepath not provided
        
    Examples
    --------
    >>> export_results(scorecard, 'json', 'results.json')
    >>> data = export_results(scorecard, 'json')  # Returns dict
    """
    # Convert to DataFrame if needed
    if isinstance(scorecard, dict):
        if 'results' in scorecard:
            df = pd.DataFrame(scorecard['results'])
            metadata = {k: v for k, v in scorecard.items() if k != 'results'}
        else:
            df = pd.DataFrame([scorecard])
            metadata = {}
    else:
        df = scorecard.copy()
        metadata = {}
    
    if format == 'csv':
        if filepath:
            df.to_csv(filepath, index=False)
            
            # Save metadata separately if requested
            if include_metadata and metadata:
                meta_path = Path(filepath).with_suffix('.meta.json')
                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
        else:
            return df.to_csv(index=False)
    
    elif format == 'json':
        # Build complete data structure
        data = {
            'timestamp': datetime.now().isoformat(),
            'results': df.to_dict('records')
        }
        
        if include_metadata:
            data.update(metadata)
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            return data
    
    elif format == 'excel':
        if not filepath:
            raise ValueError("Excel export requires a filepath")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write main results
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Write metadata if available
            if include_metadata and metadata:
                meta_df = pd.DataFrame([
                    {'Key': k, 'Value': str(v)} 
                    for k, v in metadata.items()
                ])
                meta_df.to_excel(writer, sheet_name='Metadata', index=False)
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def create_summary_statistics(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    dimension_columns: List[str],
    include_segment_stats: bool = True
) -> Dict[str, Any]:
    """
    Create comprehensive summary statistics.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data
    benchmark_df : pd.DataFrame
        Benchmark data
    dimension_columns : list of str
        Columns defining the dimension
    include_segment_stats : bool, default=True
        Whether to include per-segment statistics
        
    Returns
    -------
    dict
        Summary statistics
        
    Examples
    --------
    >>> stats = create_summary_statistics(survey, benchmark, ['country', 'gender'])
    >>> print(f"Total participants: {stats['total_participants']}")
    """
    from .calculator import calculate_gri, calculate_diversity_score
    from .analysis import calculate_segment_deviations
    
    # Basic counts
    stats = {
        'dimension': ' × '.join(dimension_columns),
        'total_participants': len(survey_df),
        'dimension_columns': dimension_columns
    }
    
    # Category counts
    for col in dimension_columns:
        if col in survey_df.columns:
            stats[f'{col}_categories'] = survey_df[col].nunique()
            stats[f'{col}_coverage'] = survey_df[col].notna().sum() / len(survey_df)
    
    # Calculate scores
    gri = calculate_gri(survey_df, benchmark_df, dimension_columns)
    diversity = calculate_diversity_score(survey_df, benchmark_df, dimension_columns)
    
    stats['gri_score'] = float(gri)
    stats['diversity_score'] = float(diversity)
    
    # Segment statistics
    if include_segment_stats:
        deviations = calculate_segment_deviations(
            survey_df, benchmark_df, dimension_columns
        )
        
        stats['segment_statistics'] = {
            'total_segments': len(deviations),
            'represented_segments': (deviations['sample_proportion'] > 0).sum(),
            'mean_absolute_deviation': float(deviations['abs_deviation'].mean()),
            'max_absolute_deviation': float(deviations['abs_deviation'].max()),
            'over_represented': (deviations['deviation'] > 0.001).sum(),
            'under_represented': (deviations['deviation'] < -0.001).sum(),
            'well_balanced': ((deviations['deviation'].abs() <= 0.001)).sum()
        }
        
        # Top deviations
        top_over = deviations[deviations['deviation'] > 0].nlargest(5, 'deviation')
        top_under = deviations[deviations['deviation'] < 0].nsmallest(5, 'deviation')
        
        stats['top_over_represented'] = []
        for _, row in top_over.iterrows():
            segment = {col: row[col] for col in dimension_columns if col in row}
            segment['deviation'] = float(row['deviation'])
            stats['top_over_represented'].append(segment)
        
        stats['top_under_represented'] = []
        for _, row in top_under.iterrows():
            segment = {col: row[col] for col in dimension_columns if col in row}
            segment['deviation'] = float(row['deviation'])
            stats['top_under_represented'].append(segment)
    
    return stats


def generate_comparison_report(
    scorecards: Dict[str, pd.DataFrame],
    output_file: Optional[Union[str, Path]] = None,
    include_trends: bool = True
) -> str:
    """
    Generate comparison report across multiple surveys.
    
    Parameters
    ----------
    scorecards : dict
        Dictionary mapping survey names to scorecard DataFrames
    output_file : str or Path, optional
        Where to save the report
    include_trends : bool, default=True
        Whether to include trend analysis
        
    Returns
    -------
    str
        The comparison report text
    """
    lines = []
    lines.append("=" * 80)
    lines.append("MULTI-SURVEY COMPARISON REPORT")
    lines.append("=" * 80)
    lines.append(f"Surveys Compared: {', '.join(scorecards.keys())}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Collect all dimensions
    all_dimensions = set()
    for scorecard in scorecards.values():
        all_dimensions.update(scorecard['dimension'].unique())
    
    # Compare by dimension
    lines.append("COMPARISON BY DIMENSION")
    lines.append("-" * 80)
    
    for dimension in sorted(all_dimensions):
        lines.append(f"\n{dimension}:")
        
        # Collect scores for this dimension
        scores = {}
        for survey_name, scorecard in scorecards.items():
            dim_data = scorecard[scorecard['dimension'] == dimension]
            if not dim_data.empty:
                scores[survey_name] = {
                    'gri': dim_data['gri_score'].iloc[0],
                    'diversity': dim_data.get('diversity_score', pd.Series()).iloc[0] 
                    if 'diversity_score' in dim_data.columns else None
                }
        
        # Display scores
        for survey, values in scores.items():
            gri_str = f"{values['gri']:.4f}"
            div_str = f", Diversity: {values['diversity']:.4f}" if values['diversity'] else ""
            lines.append(f"  {survey}: GRI: {gri_str}{div_str}")
        
        # Calculate trend if applicable
        if include_trends and len(scores) > 1:
            gri_values = [v['gri'] for v in scores.values()]
            trend = "improving" if gri_values[-1] > gri_values[0] else "declining"
            change = gri_values[-1] - gri_values[0]
            lines.append(f"  Trend: {trend} ({change:+.4f})")
    
    # Overall comparison
    lines.append("\n" + "="*80)
    lines.append("OVERALL COMPARISON")
    lines.append("="*80)
    
    for survey_name, scorecard in scorecards.items():
        mean_gri = scorecard['gri_score'].mean()
        mean_div = scorecard['diversity_score'].mean() if 'diversity_score' in scorecard else None
        
        lines.append(f"\n{survey_name}:")
        lines.append(f"  Average GRI: {mean_gri:.4f}")
        if mean_div:
            lines.append(f"  Average Diversity: {mean_div:.4f}")
        lines.append(f"  Dimensions Analyzed: {len(scorecard)}")
    
    report = '\n'.join(lines)
    
    # Save if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
    
    return report