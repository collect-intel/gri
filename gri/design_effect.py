"""
Design Effect and Effective Sample Size

Quantifies the inferential cost of distributional mismatch between a survey
sample and its target population. When post-stratification weights are applied
to correct for demographic imbalance, the variance of weighted estimates is
inflated relative to a simple random sample. The design effect measures this
inflation; the effective sample size translates it into an equivalent SRS size.

Unlike GRI (which treats overrepresentation and underrepresentation symmetrically),
the design effect is asymmetric: underrepresentation is far more costly because
the reweighting ratio q_i/p_i amplifies noise from few respondents, while
overrepresentation merely downweights excess data (wasteful but not
precision-destroying).

Key formulas:
    deff = Σ (q_i² / p_i)          (over represented strata)
    N_eff = N / deff
    precision_retention = 1 / deff  (fraction of sample budget contributing to precision)

where p_i = sample proportion, q_i = population proportion for stratum i.

See docs/precision_cost_of_low_representativeness.md for full rationale.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple


def calculate_design_effect(
    survey_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    strata_cols: List[str],
) -> Dict[str, float]:
    """
    Calculate the design effect from post-stratification weighting.

    The design effect measures how much noisier weighted population estimates
    are compared to a simple random sample of the same size. A design effect
    of 3.0 means the weighted estimates have the precision of an SRS one-third
    the size.

    This is computed only over represented strata (where p_i > 0). Strata with
    q_i > 0 but p_i = 0 are uncorrectable by reweighting; the fraction of
    population mass in such strata is reported as `uncovered_population`.

    Args:
        survey_df: DataFrame with survey participant data. Each row is one
                   participant.
        benchmark_df: DataFrame with population proportions. Must contain the
                      strata_cols and a 'population_proportion' column.
        strata_cols: Column names defining the strata.

    Returns:
        Dict with:
            design_effect: deff = Σ q_i² / p_i (over represented strata,
                           renormalized). Returns float('inf') if no strata
                           are represented.
            effective_n: N / deff. The equivalent SRS sample size.
            precision_retention: 1 / deff. Fraction of sample budget
                                 contributing to precision (0 to 1).
            n_represented_strata: Number of benchmark strata with p_i > 0.
            n_benchmark_strata: Total benchmark strata with q_i > 0.
            uncovered_population: Sum of q_i for strata where p_i = 0.
                                  Population mass invisible to reweighting.
    """
    N = len(survey_df)

    if N == 0:
        return {
            'design_effect': float('inf'),
            'effective_n': 0.0,
            'precision_retention': 0.0,
            'n_represented_strata': 0,
            'n_benchmark_strata': 0,
            'uncovered_population': 1.0,
        }

    # Compute sample proportions
    sample_counts = survey_df.groupby(strata_cols).size().reset_index(name='count')
    sample_counts['sample_proportion'] = sample_counts['count'] / N

    # Prepare benchmark proportions
    benchmark_props = benchmark_df[strata_cols + ['population_proportion']].copy()

    # Merge
    merged = pd.merge(
        benchmark_props,
        sample_counts[strata_cols + ['sample_proportion']],
        on=strata_cols,
        how='outer',
    )
    merged['sample_proportion'] = merged['sample_proportion'].fillna(0.0)
    merged['population_proportion'] = merged['population_proportion'].fillna(0.0)

    # Only consider strata that exist in the benchmark (q_i > 0)
    benchmark_strata = merged[merged['population_proportion'] > 0].copy()
    n_benchmark_strata = len(benchmark_strata)

    # Split into represented (p_i > 0) and unrepresented (p_i = 0)
    represented = benchmark_strata[benchmark_strata['sample_proportion'] > 0]
    n_represented = len(represented)
    uncovered_pop = benchmark_strata.loc[
        benchmark_strata['sample_proportion'] == 0, 'population_proportion'
    ].sum()

    if n_represented == 0:
        return {
            'design_effect': float('inf'),
            'effective_n': 0.0,
            'precision_retention': 0.0,
            'n_represented_strata': 0,
            'n_benchmark_strata': n_benchmark_strata,
            'uncovered_population': uncovered_pop,
        }

    # Renormalize q over represented strata so they sum to 1.
    # This gives the design effect for estimating population quantities
    # conditional on the covered population — the only population we can
    # make inferences about via reweighting.
    q = represented['population_proportion'].values
    p = represented['sample_proportion'].values
    q_sum = q.sum()

    if q_sum > 0:
        q_norm = q / q_sum
    else:
        q_norm = q

    # deff = Σ (q_norm_i² / p_i)  ×  (Σ p_i)
    # The (Σ p_i) factor accounts for the fact that p is normalized over ALL
    # strata (including survey-only strata not in benchmark), while q_norm is
    # normalized over represented benchmark strata only.
    #
    # Simplification: since survey-only strata (p > 0, q = 0) contribute
    # nothing to weighted estimates and their weight is 0, the effective
    # computation is just over the represented benchmark strata.
    # With proper weight normalization: w_i = q_norm_i / (p_i / p_represented_sum)
    # where p_represented_sum = Σ p_i over represented strata.
    p_sum = p.sum()
    p_norm = p / p_sum

    # deff = Σ q_norm_i² / p_norm_i
    deff = np.sum(q_norm ** 2 / p_norm)

    effective_n = N * p_sum / deff  # scale by p_sum since only represented respondents contribute
    precision_retention = 1.0 / deff

    return {
        'design_effect': float(deff),
        'effective_n': float(effective_n),
        'precision_retention': float(precision_retention),
        'n_represented_strata': int(n_represented),
        'n_benchmark_strata': int(n_benchmark_strata),
        'uncovered_population': float(uncovered_pop),
    }
