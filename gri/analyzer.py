"""
High-level API for Global Representativeness Index analysis.

This module provides the GRIAnalysis class which offers a streamlined
interface for performing GRI calculations and generating reports.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .data_loader import load_benchmark_suite, load_gd_survey, validate_survey_data
from .calculator_config import calculate_gri_scorecard, standardize_survey_data
from .analysis import (
    calculate_segment_deviations, 
    identify_top_contributors,
    generate_alignment_report
)
from .visualization import (
    plot_gri_scorecard,
    plot_segment_deviations,
    plot_cumulative_impact
)
from .simulation import monte_carlo_max_scores
from .reports import generate_text_report, export_results
from .config import GRIConfig


class GRIAnalysis:
    """
    High-level interface for GRI analysis.
    
    This class provides a streamlined API for loading data, calculating scores,
    generating visualizations, and creating reports.
    
    Examples
    --------
    >>> # From survey file
    >>> analysis = GRIAnalysis.from_survey_file('data/gd3_participants.csv')
    >>> scorecard = analysis.calculate_scorecard()
    >>> analysis.plot_scorecard()
    
    >>> # From DataFrame
    >>> analysis = GRIAnalysis(survey_df)
    >>> analysis.print_summary()
    """
    
    def __init__(
        self,
        survey_data: pd.DataFrame,
        benchmarks: Optional[Dict[str, pd.DataFrame]] = None,
        config: Optional[GRIConfig] = None,
        survey_name: Optional[str] = None
    ):
        """
        Initialize GRI analysis.
        
        Parameters
        ----------
        survey_data : pd.DataFrame
            Survey data with demographic columns
        benchmarks : dict, optional
            Pre-loaded benchmark DataFrames. If None, loads default benchmarks.
        config : GRIConfig, optional
            Configuration object. If None, uses default configuration.
        survey_name : str, optional
            Name of the survey for reporting
        """
        self.survey_data = survey_data
        self.config = config or GRIConfig()
        self.survey_name = survey_name or "Survey"
        
        # Load benchmarks if not provided
        if benchmarks is None:
            try:
                self.benchmarks = load_benchmark_suite()
            except Exception as e:
                raise ValueError(
                    f"Failed to load benchmark data. Make sure benchmark files exist in 'data/processed/'. "
                    f"Run 'python scripts/process_data.py' to generate them. Error: {e}"
                )
        else:
            self.benchmarks = benchmarks
        
        # Validate survey data
        is_valid, issues = validate_survey_data(survey_data)
        if not is_valid:
            raise ValueError(f"Invalid survey data: {', '.join(issues)}")
        
        # Cache for results
        self._scorecard = None
        self._alignment_report = None
        self._max_scores = {}
    
    @classmethod
    def from_survey_file(
        cls,
        filepath: Union[str, Path],
        survey_type: str = 'gd',
        **kwargs
    ) -> 'GRIAnalysis':
        """
        Create GRIAnalysis from a survey file.
        
        Parameters
        ----------
        filepath : str or Path
            Path to survey file
        survey_type : str, default='gd'
            Type of survey ('gd' for Global Dialogues, 'wvs' for World Values Survey)
        **kwargs
            Additional arguments passed to constructor
            
        Returns
        -------
        GRIAnalysis
            Initialized analysis object
        """
        if survey_type == 'gd':
            survey_data = load_gd_survey(filepath)
            survey_name = kwargs.pop('survey_name', Path(filepath).stem)
        elif survey_type == 'wvs':
            raise NotImplementedError("WVS loading will be implemented in Phase 4")
        else:
            raise ValueError(f"Unknown survey type: {survey_type}")
        
        return cls(survey_data, survey_name=survey_name, **kwargs)
    
    def calculate_scorecard(
        self,
        dimensions: Union[str, List[str]] = 'all',
        include_max_possible: bool = False,
        n_simulations: int = 1000,
        random_seed: Optional[int] = 42
    ) -> pd.DataFrame:
        """
        Calculate GRI scorecard for specified dimensions.
        
        Parameters
        ----------
        dimensions : str or list of str, default='all'
            Dimensions to calculate. Use 'all' for all available dimensions.
        include_max_possible : bool, default=False
            Whether to calculate maximum possible scores
        n_simulations : int, default=1000
            Number of simulations for max score calculation
        random_seed : int, optional
            Random seed for reproducibility
            
        Returns
        -------
        pd.DataFrame
            Scorecard with GRI and diversity scores
        """
        # Calculate base scorecard
        scorecard = calculate_gri_scorecard(
            self.survey_data,
            self.benchmarks,
            dimensions=dimensions
        )
        
        # Add max possible scores if requested
        if include_max_possible:
            sample_size = len(self.survey_data)
            
            for idx, row in scorecard.iterrows():
                dimension = row['dimension']
                dim_cols = row.get('dimension_columns', [])
                
                # Get appropriate benchmark
                benchmark_key = self._get_benchmark_key(dimension)
                if benchmark_key in self.benchmarks:
                    benchmark_df = self.benchmarks[benchmark_key]
                    
                    # Calculate max scores
                    if dimension not in self._max_scores:
                        max_results = monte_carlo_max_scores(
                            benchmark_df,
                            sample_size,
                            dim_cols,
                            n_simulations,
                            random_seed
                        )
                        self._max_scores[dimension] = max_results
                    else:
                        max_results = self._max_scores[dimension]
                    
                    # Add to scorecard
                    scorecard.at[idx, 'max_possible_score'] = max_results['max_gri']['mean']
                    scorecard.at[idx, 'max_possible_diversity'] = max_results['max_diversity']['mean']
                    scorecard.at[idx, 'efficiency_ratio'] = (
                        row['gri_score'] / max_results['max_gri']['mean']
                    )
                    scorecard.at[idx, 'diversity_efficiency'] = (
                        row['diversity_score'] / max_results['max_diversity']['mean']
                    )
        
        self._scorecard = scorecard
        return scorecard
    
    def plot_scorecard(
        self,
        save_to: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> None:
        """
        Plot GRI scorecard visualization.
        
        Parameters
        ----------
        save_to : str or Path, optional
            Path to save the plot
        **kwargs
            Additional arguments passed to plot_gri_scorecard
        """
        if self._scorecard is None:
            self.calculate_scorecard()
        
        include_max = 'max_possible_score' in self._scorecard.columns
        max_scores = None
        
        if include_max:
            max_scores = {
                row['dimension']: row['max_possible_score']
                for _, row in self._scorecard.iterrows()
            }
        
        plot_gri_scorecard(
            self._scorecard,
            title=f"{self.survey_name} - GRI Scorecard",
            include_max_possible=include_max,
            max_scores=max_scores,
            save_path=save_to,
            **kwargs
        )
    
    def plot_top_deviations(
        self,
        dimension: str,
        n: int = 20,
        save_to: Optional[Union[str, Path]] = None
    ) -> None:
        """
        Plot top segment deviations for a dimension.
        
        Parameters
        ----------
        dimension : str
            Dimension to analyze
        n : int, default=20
            Number of top deviations to show
        save_to : str or Path, optional
            Path to save the plot
        """
        # Get dimension columns
        dim_cols = self._get_dimension_columns(dimension)
        benchmark_key = self._get_benchmark_key(dimension)
        
        if benchmark_key not in self.benchmarks:
            raise ValueError(f"No benchmark data for dimension: {dimension}")
        
        # Calculate deviations
        deviations = calculate_segment_deviations(
            self.survey_data,
            self.benchmarks[benchmark_key],
            dim_cols
        )
        
        # Plot
        plot_segment_deviations(
            deviations,
            top_n=n,
            title=f"{self.survey_name} - {dimension} Deviations",
            save_path=save_to
        )
    
    def get_top_segments(
        self,
        dimension: str,
        n: int = 10,
        segment_type: str = 'both'
    ) -> pd.DataFrame:
        """
        Get top over/under-represented segments.
        
        Parameters
        ----------
        dimension : str
            Dimension to analyze
        n : int, default=10
            Number of segments to return
        segment_type : {'over', 'under', 'both'}, default='both'
            Type of segments to return
            
        Returns
        -------
        pd.DataFrame
            Top segments with deviation metrics
        """
        dim_cols = self._get_dimension_columns(dimension)
        benchmark_key = self._get_benchmark_key(dimension)
        
        deviations = calculate_segment_deviations(
            self.survey_data,
            self.benchmarks[benchmark_key],
            dim_cols
        )
        
        return identify_top_contributors(deviations, n, segment_type)
    
    def generate_report(
        self,
        output_file: Optional[Union[str, Path]] = None,
        include_analysis: bool = True,
        include_max_possible: bool = None
    ) -> str:
        """
        Generate comprehensive text report.
        
        Parameters
        ----------
        output_file : str or Path, optional
            Where to save the report
        include_analysis : bool, default=True
            Whether to include detailed analysis
        include_max_possible : bool, optional
            Whether to include max scores. If None, includes if available.
            
        Returns
        -------
        str
            The report text
        """
        if self._scorecard is None:
            self.calculate_scorecard()
        
        if include_max_possible is None:
            include_max_possible = 'max_possible_score' in self._scorecard.columns
        
        return generate_text_report(
            self._scorecard,
            self.survey_name,
            include_analysis,
            include_max_possible,
            output_file
        )
    
    def export_results(
        self,
        format: str = 'csv',
        filepath: Optional[Union[str, Path]] = None
    ) -> Optional[Union[str, Dict]]:
        """
        Export results in various formats.
        
        Parameters
        ----------
        format : {'csv', 'json', 'excel'}, default='csv'
            Export format
        filepath : str or Path, optional
            Output path. If None, returns the data.
            
        Returns
        -------
        str or dict or None
            Exported data if filepath not provided
        """
        if self._scorecard is None:
            self.calculate_scorecard()
        
        return export_results(self._scorecard, format, filepath)
    
    def check_alignment(self) -> Dict[str, Dict]:
        """
        Check alignment between survey and benchmark data.
        
        Returns
        -------
        dict
            Alignment report for all dimensions
        """
        if self._alignment_report is None:
            self._alignment_report = generate_alignment_report(
                self.survey_data,
                self.benchmarks
            )
        
        return self._alignment_report
    
    def print_summary(self) -> None:
        """Print a quick summary of the analysis."""
        if self._scorecard is None:
            self.calculate_scorecard()
        
        print(f"\nGRI Analysis Summary: {self.survey_name}")
        print("=" * 50)
        print(f"Total Participants: {len(self.survey_data):,}")
        print(f"Dimensions Analyzed: {len(self._scorecard)}")
        
        mean_gri = self._scorecard['gri_score'].mean()
        print(f"\nAverage GRI Score: {mean_gri:.4f}")
        
        if 'diversity_score' in self._scorecard.columns:
            mean_div = self._scorecard['diversity_score'].mean()
            print(f"Average Diversity Score: {mean_div:.4f}")
        
        print("\nTop 3 Dimensions:")
        top_3 = self._scorecard.nlargest(3, 'gri_score')
        for _, row in top_3.iterrows():
            print(f"  {row['dimension']}: {row['gri_score']:.4f}")
        
        print("\nBottom 3 Dimensions:")
        bottom_3 = self._scorecard.nsmallest(3, 'gri_score')
        for _, row in bottom_3.iterrows():
            print(f"  {row['dimension']}: {row['gri_score']:.4f}")
    
    def _get_dimension_columns(self, dimension: str) -> List[str]:
        """Get column list for a dimension name."""
        dimension_map = {
            'Country × Gender × Age': ['country', 'gender', 'age_group'],
            'Country × Religion': ['country', 'religion'],
            'Country × Environment': ['country', 'environment'],
            'Country': ['country'],
            'Gender': ['gender'],
            'Age Group': ['age_group'],
            'Religion': ['religion'],
            'Environment': ['environment'],
            'Region × Gender × Age': ['region', 'gender', 'age_group'],
            'Region × Religion': ['region', 'religion'],
            'Region × Environment': ['region', 'environment'],
            'Region': ['region'],
            'Continent': ['continent']
        }
        
        return dimension_map.get(dimension, [])
    
    def _get_benchmark_key(self, dimension: str) -> str:
        """Get benchmark dictionary key for a dimension."""
        # Direct mapping for most dimensions
        direct_map = {
            'Country × Gender × Age': 'Country × Gender × Age',
            'Country × Religion': 'Country × Religion',
            'Country × Environment': 'Country × Environment',
            'Age Group': 'Age Group',
            'Gender': 'Gender',
            'Religion': 'Religion',
            'Environment': 'Environment',
            'Country': 'Country',
            'Region': 'Region',
            'Continent': 'Continent',
            'Region × Gender × Age': 'Region × Gender × Age',
            'Region × Religion': 'Region × Religion',
            'Region × Environment': 'Region × Environment'
        }
        
        return direct_map.get(dimension, dimension)