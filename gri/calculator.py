import pandas as pd
from typing import List


def calculate_gri(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, strata_cols: List[str]) -> float:
    """
    Calculates the Global Representativeness Index (GRI).

    The GRI is a measure of how well a sample's distribution matches a benchmark
    population distribution across a set of demographic strata.
    GRI = 1 - Total Variation Distance (TVD)
    TVD = 0.5 * sum(|sample_proportion - benchmark_proportion|)

    Args:
        survey_df (pd.DataFrame): DataFrame with survey participant data. Each row
                                  should represent one participant.
        benchmark_df (pd.DataFrame): DataFrame with true population proportions.
                                     Must contain the strata_cols and a column named
                                     'population_proportion' (qi).
        strata_cols (List[str]): A list of column names that define the strata.

    Returns:
        float: The GRI score, ranging from 0.0 (complete mismatch) to 1.0 (perfect match).
    """
    # Handle empty survey case
    if len(survey_df) == 0:
        return 0.0
    
    # 1. Calculate sample proportions (s_i) for each stratum
    sample_counts = survey_df.groupby(strata_cols).size().reset_index(name='count')
    total_participants = len(survey_df)
    sample_counts['sample_proportion'] = sample_counts['count'] / total_participants
    
    # 2. Prepare the benchmark proportions (q_i)
    benchmark_props = benchmark_df[strata_cols + ['population_proportion']].copy()
    
    # 3. Merge sample and benchmark proportions
    merged = pd.merge(benchmark_props, sample_counts[strata_cols + ['sample_proportion']], 
                     on=strata_cols, how='outer')
    
    # Fill NaN values with 0 (strata present in one dataset but not the other)
    merged['sample_proportion'] = merged['sample_proportion'].fillna(0)
    merged['population_proportion'] = merged['population_proportion'].fillna(0)
    
    # 4. Calculate Total Variation Distance (TVD)
    absolute_differences = (merged['sample_proportion'] - merged['population_proportion']).abs()
    tvd = 0.5 * absolute_differences.sum()
    
    # 5. Calculate and return the GRI
    gri = 1 - tvd
    
    return gri


def calculate_diversity_score(survey_df: pd.DataFrame, benchmark_df: pd.DataFrame, 
                            strata_cols: List[str], population_threshold: float = None) -> float:
    """
    Calculates the Diversity Score (strata coverage rate).

    This score measures the percentage of relevant benchmark strata that are
    represented in the survey sample (i.e., have at least one participant).
    
    The relevance threshold X is set dynamically as X = 1/(2N) where N is the sample size,
    representing an expected count of 0.5 participants (rounding up to 1).

    Args:
        survey_df (pd.DataFrame): DataFrame with survey participant data.
        benchmark_df (pd.DataFrame): DataFrame with true population proportions.
        strata_cols (List[str]): List of column names that define the strata.
        population_threshold (float, optional): Custom threshold for relevant strata.
                                              If None, uses X = 1/(2N).

    Returns:
        float: The Diversity Score, from 0.0 to 1.0.
    """
    # Get sample size N
    N = len(survey_df)
    
    # Handle empty survey case
    if N == 0:
        return 0.0
    
    # Calculate dynamic threshold X = 1/(2N) if not provided
    if population_threshold is None:
        population_threshold = 1.0 / (2 * N)
    
    # 1. Calculate sample proportions to identify represented strata
    sample_counts = survey_df.groupby(strata_cols).size().reset_index(name='count')
    sample_proportions = sample_counts[strata_cols].copy()
    sample_proportions['sample_proportion'] = sample_counts['count'] / N
    
    # 2. Identify relevant strata from benchmark (q_i > X)
    relevant_benchmark = benchmark_df[benchmark_df['population_proportion'] > population_threshold]
    
    # 3. Calculate number of relevant strata
    num_relevant_strata = len(relevant_benchmark)
    
    # If no relevant strata, return 1.0 (perfect coverage of empty set)
    if num_relevant_strata == 0:
        return 1.0
    
    # 4. Calculate number of represented AND relevant strata
    # (strata with s_i > 0 AND q_i > X)
    represented_and_relevant = pd.merge(
        sample_proportions[sample_proportions['sample_proportion'] > 0][strata_cols],
        relevant_benchmark[strata_cols],
        on=strata_cols,
        how='inner'
    )
    num_represented_relevant = len(represented_and_relevant)
    
    # 5. Calculate diversity score
    diversity_score = num_represented_relevant / num_relevant_strata
    
    return diversity_score