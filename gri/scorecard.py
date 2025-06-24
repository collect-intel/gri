"""
Comprehensive GRI Scorecard Generator

This module provides functionality to generate complete scorecards including:
- Traditional GRI scores
- Diversity scores  
- Strategic Representativeness Index (SRI)
- Variance-Weighted Representativeness Score (VWRS)
- Maximum possible scores for GRI and Diversity

Supports all dimensions defined in config/dimensions.yaml with proper
handling of regional and continental mappings.
"""

import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import warnings

from .calculator import calculate_gri, calculate_diversity_score
from .variance_weighted import calculate_vwrs_from_dataframes
from .strategic_index import calculate_sri_from_dataframes
from .simulation import monte_carlo_max_scores
from .utils import load_data


class GRIScorecard:
    """Generate comprehensive representativeness scorecards."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize scorecard generator with configuration.
        
        Args:
            config_dir: Path to configuration directory containing dimensions.yaml,
                       segments.yaml, and regions.yaml. If None, uses default.
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config'
        
        self.config_dir = Path(config_dir)
        self._load_configs()
        self._prepare_mappings()
    
    def _load_configs(self):
        """Load configuration files."""
        # Load dimensions config
        with open(self.config_dir / 'dimensions.yaml', 'r') as f:
            self.dimensions_config = yaml.safe_load(f)
        
        # Load segments config
        with open(self.config_dir / 'segments.yaml', 'r') as f:
            self.segments_config = yaml.safe_load(f)
        
        # Load regions config
        with open(self.config_dir / 'regions.yaml', 'r') as f:
            self.regions_config = yaml.safe_load(f)
    
    def _prepare_mappings(self):
        """Prepare country/region mappings for efficient lookup."""
        # Create country to region mapping
        self.country_to_region = {}
        for region, countries in self.regions_config['country_to_region'].items():
            for country in countries:
                self.country_to_region[country] = region
        
        # Create region to continent mapping
        self.region_to_continent = {}
        for continent, regions in self.regions_config['region_to_continent'].items():
            for region in regions:
                self.region_to_continent[region] = continent
        
        # Create country to continent mapping
        self.country_to_continent = {}
        for country, region in self.country_to_region.items():
            if region in self.region_to_continent:
                self.country_to_continent[country] = self.region_to_continent[region]
    
    def _add_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add region and continent columns based on country."""
        df = df.copy()
        
        if 'country' in df.columns:
            # Add region column
            df['region'] = df['country'].map(self.country_to_region)
            
            # Add continent column
            df['continent'] = df['country'].map(self.country_to_continent)
            
            # Warn about unmapped countries
            unmapped = df[df['region'].isna()]['country'].unique()
            if len(unmapped) > 0:
                warnings.warn(f"Unmapped countries found: {unmapped}")
        
        return df
    
    def _load_benchmark_for_dimension(self, dimension: Dict[str, Any], base_path: Path, use_simplified: bool = False) -> Optional[pd.DataFrame]:
        """Load appropriate benchmark data for a dimension.
        
        Args:
            dimension: Dimension configuration
            base_path: Base path for data files
            use_simplified: Whether to use simplified benchmarks (for VWRS compatibility)
        """
        cols = dimension['columns']
        
        # Special handling for simplified country benchmark
        if use_simplified and cols == ['country']:
            return self._create_simplified_country_benchmark()
        
        # Map dimension columns to benchmark files
        if set(cols) == {'country', 'gender', 'age_group'}:
            return load_data(base_path / 'data/processed/benchmark_country_gender_age.csv')
        elif set(cols) == {'country', 'religion'}:
            return load_data(base_path / 'data/processed/benchmark_country_religion.csv')
        elif set(cols) == {'country', 'environment'}:
            return load_data(base_path / 'data/processed/benchmark_country_environment.csv')
        elif set(cols) == {'region', 'gender', 'age_group'}:
            return load_data(base_path / 'data/processed/benchmark_region_gender_age.csv')
        elif set(cols) == {'region', 'religion'}:
            return load_data(base_path / 'data/processed/benchmark_region_religion.csv')
        elif set(cols) == {'region', 'environment'}:
            return load_data(base_path / 'data/processed/benchmark_region_environment.csv')
        elif cols == ['country']:
            return load_data(base_path / 'data/processed/benchmark_country.csv')
        elif cols == ['region']:
            return load_data(base_path / 'data/processed/benchmark_region.csv')
        elif cols == ['continent']:
            return load_data(base_path / 'data/processed/benchmark_continent.csv')
        elif cols == ['gender']:
            return load_data(base_path / 'data/processed/benchmark_gender.csv')
        elif cols == ['age_group']:
            return load_data(base_path / 'data/processed/benchmark_age_group.csv')
        elif cols == ['religion']:
            return load_data(base_path / 'data/processed/benchmark_religion.csv')
        elif cols == ['environment']:
            return load_data(base_path / 'data/processed/benchmark_environment.csv')
        else:
            warnings.warn(f"No benchmark data found for dimension: {dimension['name']}")
            return None
    
    def _create_simplified_country_benchmark(self) -> pd.DataFrame:
        """Create simplified country benchmark matching representativeness_comparison.py."""
        # Major countries by population (simplified)
        benchmark_data = [
            {'country': 'China', 'population_proportion': 0.180},
            {'country': 'India', 'population_proportion': 0.175},
            {'country': 'United States', 'population_proportion': 0.042},
            {'country': 'Indonesia', 'population_proportion': 0.035},
            {'country': 'Pakistan', 'population_proportion': 0.028},
            {'country': 'Brazil', 'population_proportion': 0.027},
            {'country': 'Nigeria', 'population_proportion': 0.026},
            {'country': 'Bangladesh', 'population_proportion': 0.021},
            {'country': 'Russian Federation', 'population_proportion': 0.018},
            {'country': 'Mexico', 'population_proportion': 0.016},
            {'country': 'Japan', 'population_proportion': 0.016},
            {'country': 'Ethiopia', 'population_proportion': 0.015},
            {'country': 'Philippines', 'population_proportion': 0.014},
            {'country': 'Egypt', 'population_proportion': 0.013},
            {'country': 'Viet Nam', 'population_proportion': 0.012},
            {'country': 'Türkiye', 'population_proportion': 0.011},
            {'country': 'Germany', 'population_proportion': 0.010},
            {'country': 'United Kingdom', 'population_proportion': 0.008},
            {'country': 'France', 'population_proportion': 0.008},
            {'country': 'Italy', 'population_proportion': 0.007},
            {'country': 'South Africa', 'population_proportion': 0.007},
            {'country': 'Kenya', 'population_proportion': 0.007},
            {'country': 'South Korea', 'population_proportion': 0.006},
            {'country': 'Spain', 'population_proportion': 0.006},
            {'country': 'Canada', 'population_proportion': 0.005},
            {'country': 'Poland', 'population_proportion': 0.005},
            {'country': 'Australia', 'population_proportion': 0.003},
            {'country': 'Netherlands', 'population_proportion': 0.002},
            {'country': 'Belgium', 'population_proportion': 0.001},
            {'country': 'Sweden', 'population_proportion': 0.001},
            {'country': 'Denmark', 'population_proportion': 0.001},
        ]
        
        # Add all other countries as "Others"
        total_listed = sum(item['population_proportion'] for item in benchmark_data)
        benchmark_data.append({
            'country': 'Others',
            'population_proportion': 1.0 - total_listed
        })
        
        return pd.DataFrame(benchmark_data)
    
    def _load_max_scores(self, base_path: Path, sample_size: int) -> Dict[str, Dict[str, float]]:
        """Load pre-calculated maximum possible scores."""
        max_scores_file = base_path / 'analysis_output/max_possible_scores_summary.csv'
        
        max_scores = {}
        
        if max_scores_file.exists():
            max_scores_df = pd.read_csv(max_scores_file)
            
            # Find closest sample size
            sizes = max_scores_df['sample_size'].unique()
            closest_size = min(sizes, key=lambda x: abs(x - sample_size))
            
            # Extract scores for each dimension
            for _, row in max_scores_df[max_scores_df['sample_size'] == closest_size].iterrows():
                dim = row['dimension']
                max_scores[dim] = {
                    'max_gri': row['max_gri_mean'],
                    'max_diversity': row['max_diversity_mean'],
                    'sample_size_used': closest_size
                }
        
        # Add estimates for missing dimensions based on patterns
        # These are conservative estimates based on empirical observations
        if 'Country' not in max_scores:
            max_scores['Country'] = {
                'max_gri': 0.995,  # Country-only is easier than multi-dimensional
                'max_diversity': 0.99,
                'sample_size_used': sample_size
            }
        
        # Regional dimensions - easier than country-level
        for dim in ['Region × Gender × Age', 'Region × Religion', 'Region × Environment', 'Region']:
            if dim not in max_scores:
                max_scores[dim] = {
                    'max_gri': 0.98,  # Fewer strata = easier to achieve high GRI
                    'max_diversity': 0.99,
                    'sample_size_used': sample_size
                }
        
        # Continental dimension - very easy
        if 'Continent' not in max_scores:
            max_scores['Continent'] = {
                'max_gri': 0.995,  # Only 6 continents
                'max_diversity': 1.0,  # Can easily cover all continents
                'sample_size_used': sample_size
            }
        
        # Single demographic dimensions - also easier
        for dim in ['Gender', 'Age Group', 'Religion', 'Environment']:
            if dim not in max_scores:
                max_scores[dim] = {
                    'max_gri': 0.99,  # Few categories
                    'max_diversity': 1.0,  # Can cover all categories
                    'sample_size_used': sample_size
                }
        
        return max_scores
    
    def _load_variance_data(self, base_path: Path, gd_num: int) -> Optional[Dict[str, Dict[str, float]]]:
        """Load variance data for VWRS calculations."""
        variance_file = base_path / f'analysis_output/demographic_variance/GD{gd_num}_variance_lookup.json'
        
        if variance_file.exists():
            with open(variance_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def calculate_dimension_scores(
        self,
        survey_df: pd.DataFrame,
        dimension: Dict[str, Any],
        base_path: Path,
        variance_data: Optional[Dict[str, Dict[str, float]]] = None,
        max_scores: Optional[Dict[str, Dict[str, float]]] = None,
        use_simplified_benchmarks: bool = False
    ) -> Dict[str, Any]:
        """Calculate all scores for a single dimension."""
        result = {
            'dimension': dimension['name'],
            'columns': dimension['columns'],
            'description': dimension.get('description', ''),
            'n_samples': len(survey_df)
        }
        
        # Load benchmark data
        benchmark_df = self._load_benchmark_for_dimension(dimension, base_path, use_simplified_benchmarks)
        if benchmark_df is None:
            result.update({
                'gri': None,
                'diversity': None,
                'sri': None,
                'vwrs': None,
                'error': 'No benchmark data available'
            })
            return result
        
        # Check if all required columns exist
        missing_cols = [col for col in dimension['columns'] if col not in survey_df.columns]
        if missing_cols:
            result.update({
                'gri': None,
                'diversity': None,
                'sri': None,
                'vwrs': None,
                'error': f'Missing columns: {missing_cols}'
            })
            return result
        
        try:
            # Calculate GRI
            result['gri'] = calculate_gri(survey_df, benchmark_df, dimension['columns'])
            
            # Calculate Diversity Score
            result['diversity'] = calculate_diversity_score(survey_df, benchmark_df, dimension['columns'])
            
            # Calculate SRI
            sri, sri_details = calculate_sri_from_dataframes(survey_df, benchmark_df, dimension['columns'])
            result['sri'] = sri
            
            # Calculate VWRS
            # Get variance data for this dimension if available
            dim_variance = None
            if variance_data:
                # Try to find variance data for this dimension
                dim_name_in_variance = dimension['name'].replace(' × ', ' x ')
                if dim_name_in_variance in variance_data:
                    dim_variance = variance_data[dim_name_in_variance]
                elif dimension['name'] in variance_data:
                    dim_variance = variance_data[dimension['name']]
                # For single dimensions like 'Country', check if it exists directly
                elif len(dimension['columns']) == 1:
                    single_dim = dimension['columns'][0].title()
                    if single_dim in variance_data:
                        dim_variance = variance_data[single_dim]
            
            vwrs, vwrs_details = calculate_vwrs_from_dataframes(
                survey_df, benchmark_df, dimension['columns'], dim_variance
            )
            result['vwrs'] = vwrs
            
            # Add max scores if available
            if max_scores and dimension['name'] in max_scores:
                max_info = max_scores[dimension['name']]
                result['max_gri'] = max_info['max_gri']
                result['max_diversity'] = max_info['max_diversity']
                result['gri_pct_of_max'] = (result['gri'] / max_info['max_gri'] * 100) if max_info['max_gri'] > 0 else None
                result['diversity_pct_of_max'] = (result['diversity'] / max_info['max_diversity'] * 100) if max_info['max_diversity'] > 0 else None
            
        except Exception as e:
            result.update({
                'gri': None,
                'diversity': None,
                'sri': None,
                'vwrs': None,
                'error': str(e)
            })
        
        return result
    
    def generate_scorecard(
        self,
        survey_df: pd.DataFrame,
        base_path: Path,
        gd_num: Optional[int] = None,
        include_extended: bool = False,
        use_simplified_benchmarks: bool = False
    ) -> pd.DataFrame:
        """
        Generate complete scorecard for survey data.
        
        Args:
            survey_df: Survey data with participant responses
            base_path: Base path for data files
            gd_num: Global Dialogues number (for variance data)
            include_extended: Whether to include extended dimensions
            use_simplified_benchmarks: Whether to use simplified benchmarks for better VWRS comparability
            
        Returns:
            DataFrame with scores for all dimensions
        """
        # Add derived columns (region, continent)
        survey_df = self._add_derived_columns(survey_df)
        
        # Load max scores
        max_scores = self._load_max_scores(base_path, len(survey_df))
        
        # Load variance data if GD number provided
        variance_data = None
        if gd_num:
            variance_data = self._load_variance_data(base_path, gd_num)
        
        # Get dimensions to calculate
        dimensions = self.dimensions_config['standard_scorecard'].copy()
        if include_extended and 'extended_dimensions' in self.dimensions_config:
            dimensions.extend(self.dimensions_config['extended_dimensions'])
        
        # Calculate scores for each dimension
        results = []
        for dimension in dimensions:
            scores = self.calculate_dimension_scores(
                survey_df, dimension, base_path, variance_data, max_scores, use_simplified_benchmarks
            )
            results.append(scores)
        
        # Convert to DataFrame
        scorecard_df = pd.DataFrame(results)
        
        # Add overall average row
        numeric_cols = ['gri', 'diversity', 'sri', 'vwrs']
        avg_row = {'dimension': 'Overall (Average)'}
        for col in numeric_cols:
            valid_values = scorecard_df[col].dropna()
            if len(valid_values) > 0:
                avg_row[col] = valid_values.mean()
        
        scorecard_df = pd.concat([scorecard_df, pd.DataFrame([avg_row])], ignore_index=True)
        
        return scorecard_df
    
    def format_scorecard(self, scorecard_df: pd.DataFrame, format: str = 'text') -> str:
        """
        Format scorecard for display or export.
        
        Args:
            scorecard_df: Scorecard DataFrame
            format: Output format ('text', 'csv', 'markdown')
            
        Returns:
            Formatted scorecard string
        """
        if format == 'csv':
            return scorecard_df.to_csv(index=False)
        
        elif format == 'markdown':
            # Create markdown table
            lines = ['# GRI Scorecard\n']
            lines.append('| Dimension | GRI | Diversity | SRI | VWRS | GRI % Max | Div % Max |')
            lines.append('|-----------|-----|-----------|-----|------|-----------|-----------|')
            
            for _, row in scorecard_df.iterrows():
                gri = f"{row['gri']:.4f}" if pd.notna(row.get('gri')) else 'N/A'
                div = f"{row['diversity']:.4f}" if pd.notna(row.get('diversity')) else 'N/A'
                sri = f"{row['sri']:.4f}" if pd.notna(row.get('sri')) else 'N/A'
                vwrs = f"{row['vwrs']:.4f}" if pd.notna(row.get('vwrs')) else 'N/A'
                gri_pct = f"{row['gri_pct_of_max']:.1f}%" if pd.notna(row.get('gri_pct_of_max')) else 'N/A'
                div_pct = f"{row['diversity_pct_of_max']:.1f}%" if pd.notna(row.get('diversity_pct_of_max')) else 'N/A'
                
                lines.append(f"| {row['dimension']} | {gri} | {div} | {sri} | {vwrs} | {gri_pct} | {div_pct} |")
            
            return '\n'.join(lines)
        
        else:  # text format
            lines = ['GRI SCORECARD']
            lines.append('=' * 120)
            lines.append(f"{'Dimension':<30} {'GRI':>8} {'Diversity':>10} {'SRI':>8} {'VWRS':>8} {'Max GRI':>8} {'Max Div':>8} {'GRI %':>8} {'Div %':>8}")
            lines.append('-' * 120)
            
            for _, row in scorecard_df.iterrows():
                dim = row['dimension'][:30]
                gri = f"{row['gri']:.4f}" if pd.notna(row.get('gri')) else 'Error'
                div = f"{row['diversity']:.4f}" if pd.notna(row.get('diversity')) else 'Error'
                sri = f"{row['sri']:.4f}" if pd.notna(row.get('sri')) else 'Error'
                vwrs = f"{row['vwrs']:.4f}" if pd.notna(row.get('vwrs')) else 'Error'
                max_gri = f"{row['max_gri']:.4f}" if pd.notna(row.get('max_gri')) else '--'
                max_div = f"{row['max_diversity']:.4f}" if pd.notna(row.get('max_diversity')) else '--'
                gri_pct = f"{row['gri_pct_of_max']:.1f}%" if pd.notna(row.get('gri_pct_of_max')) else '--'
                div_pct = f"{row['diversity_pct_of_max']:.1f}%" if pd.notna(row.get('diversity_pct_of_max')) else '--'
                
                lines.append(f"{dim:<30} {gri:>8} {div:>10} {sri:>8} {vwrs:>8} {max_gri:>8} {max_div:>8} {gri_pct:>8} {div_pct:>8}")
                
                if pd.notna(row.get('error')):
                    lines.append(f"  → Error: {row['error']}")
            
            lines.append('=' * 120)
            return '\n'.join(lines)