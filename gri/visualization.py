"""
Visualization functions for Global Representativeness Index analysis.

This module provides standard plotting functions for GRI scorecards,
sample distributions, and deviation analyses.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
import seaborn as sns
from pathlib import Path

# Set default style
plt.style.use('seaborn-v0_8-darkgrid')


def plot_gri_scorecard(
    scores: Union[pd.DataFrame, Dict[str, float]],
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 8),
    include_max_possible: bool = False,
    max_scores: Optional[Dict[str, float]] = None,
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Create a bar chart visualization of GRI scores across dimensions.
    
    Parameters
    ----------
    scores : pd.DataFrame or dict
        GRI scores by dimension. If DataFrame, expects 'dimension' and 'gri_score' columns.
        If dict, maps dimension names to scores.
    title : str, optional
        Plot title. Defaults to "Global Representativeness Index Scorecard"
    figsize : tuple of float, default=(12, 8)
        Figure size (width, height)
    include_max_possible : bool, default=False
        Whether to show maximum possible scores
    max_scores : dict, optional
        Maximum possible scores by dimension (required if include_max_possible=True)
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
        
    Examples
    --------
    >>> scores = {'Country': 0.85, 'Gender': 0.92, 'Age Group': 0.78}
    >>> fig = plot_gri_scorecard(scores, title="GD3 GRI Scores")
    >>> plt.show()
    """
    # Convert dict to DataFrame if needed
    if isinstance(scores, dict):
        scores_df = pd.DataFrame([
            {'dimension': k, 'gri_score': v} for k, v in scores.items()
        ])
    else:
        scores_df = scores.copy()
    
    # Sort by score
    scores_df = scores_df.sort_values('gri_score', ascending=True)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create bars
    y_positions = np.arange(len(scores_df))
    bars = ax.barh(y_positions, scores_df['gri_score'], color='steelblue', alpha=0.8)
    
    # Add value labels on bars
    for i, (idx, row) in enumerate(scores_df.iterrows()):
        score = row['gri_score']
        ax.text(score + 0.01, i, f'{score:.3f}', va='center', fontsize=10)
    
    # Add max possible scores if requested
    if include_max_possible and max_scores:
        max_values = [max_scores.get(dim, 1.0) for dim in scores_df['dimension']]
        ax.barh(y_positions, max_values, color='none', edgecolor='red', 
                linewidth=2, linestyle='--', alpha=0.7)
        
        # Add efficiency percentages
        for i, (score, max_score, dim) in enumerate(zip(scores_df['gri_score'], 
                                                        max_values, 
                                                        scores_df['dimension'])):
            if max_score > 0:
                efficiency = score / max_score * 100
                ax.text(max_score + 0.01, i, f'({efficiency:.0f}%)', 
                       va='center', fontsize=9, color='red', alpha=0.7)
    
    # Customize plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels(scores_df['dimension'])
    ax.set_xlabel('GRI Score', fontsize=12)
    ax.set_xlim(0, 1.05)
    ax.set_title(title or 'Global Representativeness Index Scorecard', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add grid
    ax.grid(axis='x', alpha=0.3)
    
    # Add reference line at 0.8
    ax.axvline(x=0.8, color='green', linestyle=':', alpha=0.5, 
              label='Good representation (0.8)')
    
    # Add legend if max scores shown
    if include_max_possible and max_scores:
        ax.legend(['Current Score', 'Maximum Possible', 'Good Threshold'], 
                 loc='lower right')
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_sample_distribution(
    survey_df: pd.DataFrame,
    dimension: Union[str, List[str]],
    benchmark_df: Optional[pd.DataFrame] = None,
    figsize: Tuple[float, float] = (12, 8),
    top_n: int = 20,
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Plot distribution of survey sample compared to benchmark.
    
    Parameters
    ----------
    survey_df : pd.DataFrame
        Survey data
    dimension : str or list of str
        Column(s) to plot distribution for
    benchmark_df : pd.DataFrame, optional
        Benchmark data for comparison
    figsize : tuple of float, default=(12, 8)
        Figure size
    top_n : int, default=20
        Number of top categories to show (for many-category dimensions)
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    if isinstance(dimension, str):
        dimension = [dimension]
    
    # Aggregate survey data
    if len(dimension) == 1:
        survey_counts = survey_df[dimension[0]].value_counts()
        survey_props = survey_counts / len(survey_df)
    else:
        # Multiple dimensions - create combined categories
        combined = survey_df[dimension].apply(lambda row: ' - '.join(row.astype(str)), axis=1)
        survey_counts = combined.value_counts()
        survey_props = survey_counts / len(survey_df)
    
    # Limit to top N if many categories
    if len(survey_props) > top_n:
        survey_props = survey_props.head(top_n)
        title_suffix = f" (Top {top_n})"
    else:
        title_suffix = ""
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot survey distribution
    x_pos = np.arange(len(survey_props))
    bars = ax.bar(x_pos, survey_props.values, alpha=0.7, label='Survey Sample')
    
    # Add benchmark if provided
    if benchmark_df is not None:
        if len(dimension) == 1:
            benchmark_data = benchmark_df.groupby(dimension[0])['population_proportion'].sum()
        else:
            benchmark_data = benchmark_df.groupby(dimension)['population_proportion'].sum()
        
        # Align with survey categories
        benchmark_values = []
        for cat in survey_props.index:
            if isinstance(cat, str) and ' - ' in cat and len(dimension) > 1:
                # Split combined category
                parts = cat.split(' - ')
                key = tuple(parts) if len(parts) == len(dimension) else cat
            else:
                key = cat
            
            benchmark_values.append(benchmark_data.get(key, 0))
        
        # Plot benchmark
        ax.bar(x_pos, benchmark_values, alpha=0.5, label='Benchmark', color='red')
    
    # Customize plot
    ax.set_xticks(x_pos)
    ax.set_xticklabels(survey_props.index, rotation=45, ha='right')
    ax.set_ylabel('Proportion', fontsize=12)
    ax.set_title(f'Distribution: {" × ".join(dimension)}{title_suffix}', 
                fontsize=14, fontweight='bold')
    
    if benchmark_df is not None:
        ax.legend()
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_diversity_coverage(
    diversity_scores: Union[pd.DataFrame, Dict[str, float]],
    figsize: Tuple[float, float] = (10, 10),
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Create a pie chart showing diversity score coverage.
    
    Parameters
    ----------
    diversity_scores : pd.DataFrame or dict
        Diversity scores by dimension
    figsize : tuple of float, default=(10, 10)
        Figure size
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    # Convert to dict if DataFrame
    if isinstance(diversity_scores, pd.DataFrame):
        scores_dict = diversity_scores.set_index('dimension')['diversity_score'].to_dict()
    else:
        scores_dict = diversity_scores
    
    # Calculate coverage percentages
    labels = []
    sizes = []
    colors = []
    
    for dim, score in scores_dict.items():
        labels.append(f"{dim}\n({score:.1%} coverage)")
        sizes.append(score)
        
        # Color based on score
        if score >= 0.9:
            colors.append('green')
        elif score >= 0.7:
            colors.append('yellow')
        else:
            colors.append('red')
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=figsize)
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, 
                                       autopct='%1.1f%%', startangle=90)
    
    # Customize
    ax.set_title('Diversity Score Coverage by Dimension', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Equal aspect ratio ensures circular pie
    ax.axis('equal')
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_segment_deviations(
    deviations: pd.DataFrame,
    top_n: int = 20,
    figsize: Tuple[float, float] = (12, 10),
    title: Optional[str] = None,
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Plot top segment deviations from benchmark.
    
    Parameters
    ----------
    deviations : pd.DataFrame
        Output from calculate_segment_deviations
    top_n : int, default=20
        Number of top deviations to show
    figsize : tuple of float, default=(12, 10)
        Figure size
    title : str, optional
        Plot title
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    # Get top deviations
    top_devs = deviations.nlargest(top_n, 'abs_deviation')
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Prepare data
    y_positions = np.arange(len(top_devs))
    
    # Color based on over/under representation
    colors = ['red' if x > 0 else 'blue' for x in top_devs['deviation']]
    
    # Create horizontal bars
    bars = ax.barh(y_positions, top_devs['deviation'], color=colors, alpha=0.7)
    
    # Add segment labels
    labels = []
    for _, row in top_devs.iterrows():
        # Create label from non-metric columns
        label_parts = []
        for col in top_devs.columns:
            if col not in ['sample_proportion', 'benchmark_proportion', 'deviation', 
                          'abs_deviation', 'normalized_deviation', 'tvd_contribution',
                          'representation', 'cumulative_tvd', 'segment_name']:
                if pd.notna(row[col]):
                    label_parts.append(str(row[col]))
        labels.append(' - '.join(label_parts) if label_parts else 'Unknown')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    
    # Add value labels
    for i, (idx, row) in enumerate(top_devs.iterrows()):
        deviation = row['deviation']
        sample_pct = row['sample_proportion'] * 100
        bench_pct = row['benchmark_proportion'] * 100
        
        # Position text based on bar direction
        x_pos = deviation + (0.001 if deviation > 0 else -0.001)
        ha = 'left' if deviation > 0 else 'right'
        
        ax.text(x_pos, i, f'{deviation:.3f}\n({sample_pct:.1f}% vs {bench_pct:.1f}%)', 
               va='center', ha=ha, fontsize=8)
    
    # Customize plot
    ax.set_xlabel('Deviation from Benchmark', fontsize=12)
    ax.set_title(title or f'Top {top_n} Segment Deviations', 
                fontsize=14, fontweight='bold', pad=20)
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='red', alpha=0.7, label='Over-represented'),
        Patch(facecolor='blue', alpha=0.7, label='Under-represented')
    ]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_cumulative_impact(
    deviations: pd.DataFrame,
    n_segments: int = 30,
    figsize: Tuple[float, float] = (10, 6),
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Plot cumulative impact of fixing top deviation segments.
    
    Parameters
    ----------
    deviations : pd.DataFrame
        Output from calculate_segment_deviations
    n_segments : int, default=30
        Number of segments to include
    figsize : tuple of float, default=(10, 6)
        Figure size
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    # Get top segments
    top_segments = deviations.nlargest(n_segments, 'abs_deviation').copy()
    
    # Calculate cumulative impact
    top_segments['cumulative_tvd'] = top_segments['tvd_contribution'].cumsum()
    top_segments['segment_number'] = range(1, len(top_segments) + 1)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot cumulative impact
    ax.plot(top_segments['segment_number'], top_segments['cumulative_tvd'], 
           marker='o', linewidth=2, markersize=6)
    
    # Add shaded regions for impact levels
    ax.axhspan(0, 0.05, alpha=0.2, color='green', label='Low impact')
    ax.axhspan(0.05, 0.10, alpha=0.2, color='yellow', label='Medium impact')
    ax.axhspan(0.10, 1.0, alpha=0.2, color='red', label='High impact')
    
    # Customize plot
    ax.set_xlabel('Number of Segments Fixed', fontsize=12)
    ax.set_ylabel('Cumulative TVD Reduction', fontsize=12)
    ax.set_title('Cumulative Impact of Fixing Top Deviation Segments', 
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    
    # Add annotations for key thresholds
    for threshold in [0.05, 0.10, 0.15]:
        segments_needed = (top_segments['cumulative_tvd'] >= threshold).sum()
        if segments_needed > 0:
            ax.annotate(f'{threshold:.0%} improvement: {segments_needed} segments', 
                       xy=(segments_needed, threshold), 
                       xytext=(segments_needed + 2, threshold + 0.01),
                       arrowprops=dict(arrowstyle='->', color='black', alpha=0.5))
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def create_comparison_plot(
    scorecards: Dict[str, pd.DataFrame],
    dimension: str,
    metric: str = 'gri_score',
    figsize: Tuple[float, float] = (10, 6),
    save_path: Optional[Union[str, Path]] = None
) -> plt.Figure:
    """
    Create comparison plot across multiple surveys.
    
    Parameters
    ----------
    scorecards : dict
        Dictionary mapping survey names to scorecard DataFrames
    dimension : str
        Dimension to compare
    metric : str, default='gri_score'
        Metric to compare ('gri_score' or 'diversity_score')
    figsize : tuple of float, default=(10, 6)
        Figure size
    save_path : str or Path, optional
        Path to save the figure
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object
    """
    # Extract data for dimension
    survey_names = []
    values = []
    
    for survey_name, scorecard in scorecards.items():
        dim_data = scorecard[scorecard['dimension'] == dimension]
        if not dim_data.empty:
            survey_names.append(survey_name)
            values.append(dim_data[metric].iloc[0])
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create bar plot
    x_pos = np.arange(len(survey_names))
    bars = ax.bar(x_pos, values, color='skyblue', alpha=0.8)
    
    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{value:.3f}', ha='center', va='bottom')
    
    # Customize plot
    ax.set_xticks(x_pos)
    ax.set_xticklabels(survey_names)
    ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.set_title(f'{dimension} - {metric.replace("_", " ").title()} Comparison', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add reference line
    ax.axhline(y=0.8, color='green', linestyle=':', alpha=0.5)
    
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig