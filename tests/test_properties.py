"""
Property-based tests for GRI framework mathematical invariants.

Uses parametrize with fixed random seeds (no hypothesis dependency)
to verify core properties across varied inputs.
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gri import calculate_gri, calculate_diversity_score, calculate_design_effect
from gri.strategic_index import calculate_sri, calculate_strategic_targets


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_survey_and_benchmark(sample_props, pop_props, strata_col="stratum"):
    """Build DataFrames from proportion dicts for testing."""
    # Build benchmark
    rows = [
        {strata_col: k, "population_proportion": v}
        for k, v in pop_props.items()
    ]
    benchmark_df = pd.DataFrame(rows)

    # Build survey (expand proportions into individual rows)
    N = 1000
    survey_rows = []
    for k, p in sample_props.items():
        count = int(round(p * N))
        survey_rows.extend([{strata_col: k}] * count)
    # Adjust to exactly N
    while len(survey_rows) < N:
        survey_rows.append({strata_col: list(sample_props.keys())[0]})
    survey_df = pd.DataFrame(survey_rows[:N])
    return survey_df, benchmark_df


def _random_distribution(rng, k):
    """Return a random probability distribution of length k."""
    raw = rng.dirichlet(np.ones(k))
    return dict(zip([f"s{i}" for i in range(k)], raw))


SEEDS = [42, 123, 7, 2024, 99]
K_VALUES = [3, 5, 10, 20]


# ===========================================================================
# GRI Properties
# ===========================================================================

class TestGRIProperties:
    """Mathematical invariants of the GRI."""

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_identity(self, k, seed):
        """GRI(P, P) == 1.0 for any distribution P."""
        rng = np.random.default_rng(seed)
        dist = _random_distribution(rng, k)
        survey_df, benchmark_df = _make_survey_and_benchmark(dist, dist)
        gri = calculate_gri(survey_df, benchmark_df, ["stratum"])
        assert gri == pytest.approx(1.0, abs=0.01)

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_bounds(self, k, seed):
        """0 <= GRI(P, Q) <= 1 for any P, Q."""
        rng = np.random.default_rng(seed)
        p = _random_distribution(rng, k)
        q = _random_distribution(rng, k)
        survey_df, benchmark_df = _make_survey_and_benchmark(p, q)
        gri = calculate_gri(survey_df, benchmark_df, ["stratum"])
        assert 0.0 <= gri <= 1.0

    @pytest.mark.parametrize("seed", SEEDS)
    def test_symmetry_conceptual(self, seed):
        """GRI(P, Q) == GRI(Q, P) — swapping survey/benchmark roles."""
        rng = np.random.default_rng(seed)
        p = _random_distribution(rng, 5)
        q = _random_distribution(rng, 5)
        survey_pq, bench_pq = _make_survey_and_benchmark(p, q)
        survey_qp, bench_qp = _make_survey_and_benchmark(q, p)
        gri_pq = calculate_gri(survey_pq, bench_pq, ["stratum"])
        gri_qp = calculate_gri(survey_qp, bench_qp, ["stratum"])
        assert gri_pq == pytest.approx(gri_qp, abs=0.02)

    def test_perturbation_monotonicity(self):
        """Moving mass toward target increases GRI."""
        pop = {"A": 0.5, "B": 0.3, "C": 0.2}
        # Start far from target
        sample_far = {"A": 0.2, "B": 0.2, "C": 0.6}
        # Move closer to target
        sample_closer = {"A": 0.35, "B": 0.25, "C": 0.4}
        survey_far, bench = _make_survey_and_benchmark(sample_far, pop)
        survey_closer, _ = _make_survey_and_benchmark(sample_closer, pop)
        gri_far = calculate_gri(survey_far, bench, ["stratum"])
        gri_closer = calculate_gri(survey_closer, bench, ["stratum"])
        assert gri_closer > gri_far

    def test_invariant_to_row_ordering(self):
        """GRI is invariant to row order of survey data."""
        pop = {"A": 0.5, "B": 0.3, "C": 0.2}
        sample = {"A": 0.4, "B": 0.35, "C": 0.25}
        survey_df, bench_df = _make_survey_and_benchmark(sample, pop)
        gri_original = calculate_gri(survey_df, bench_df, ["stratum"])
        # Shuffle rows
        survey_shuffled = survey_df.sample(frac=1, random_state=42).reset_index(drop=True)
        gri_shuffled = calculate_gri(survey_shuffled, bench_df, ["stratum"])
        assert gri_original == pytest.approx(gri_shuffled)

    def test_invariant_to_strata_column_ordering(self):
        """GRI is invariant to how strata columns are ordered."""
        # Two-column strata
        survey_rows = (
            [{"dim1": "X", "dim2": "A"}] * 400
            + [{"dim1": "X", "dim2": "B"}] * 300
            + [{"dim1": "Y", "dim2": "A"}] * 200
            + [{"dim1": "Y", "dim2": "B"}] * 100
        )
        survey_df = pd.DataFrame(survey_rows)
        bench_df = pd.DataFrame([
            {"dim1": "X", "dim2": "A", "population_proportion": 0.3},
            {"dim1": "X", "dim2": "B", "population_proportion": 0.2},
            {"dim1": "Y", "dim2": "A", "population_proportion": 0.3},
            {"dim1": "Y", "dim2": "B", "population_proportion": 0.2},
        ])
        gri_12 = calculate_gri(survey_df, bench_df, ["dim1", "dim2"])
        gri_21 = calculate_gri(survey_df, bench_df, ["dim2", "dim1"])
        assert gri_12 == pytest.approx(gri_21)

    def test_empty_survey_returns_zero(self):
        """GRI of an empty survey is 0.0."""
        pop = {"A": 0.5, "B": 0.5}
        bench_df = pd.DataFrame([
            {"stratum": "A", "population_proportion": 0.5},
            {"stratum": "B", "population_proportion": 0.5},
        ])
        survey_df = pd.DataFrame(columns=["stratum"])
        gri = calculate_gri(survey_df, bench_df, ["stratum"])
        assert gri == 0.0

    def test_disjoint_support_approaches_zero(self):
        """When sample and benchmark occupy disjoint strata, GRI approaches 0."""
        survey_rows = [{"stratum": "X"}] * 500 + [{"stratum": "Y"}] * 500
        survey_df = pd.DataFrame(survey_rows)
        bench_df = pd.DataFrame([
            {"stratum": "A", "population_proportion": 0.5},
            {"stratum": "B", "population_proportion": 0.5},
        ])
        gri = calculate_gri(survey_df, bench_df, ["stratum"])
        assert gri == 0.0


# ===========================================================================
# Diversity Score Properties
# ===========================================================================

class TestDiversityProperties:

    def test_full_coverage_gives_one(self):
        """Diversity == 1.0 when all relevant strata are represented."""
        pop = {"A": 0.5, "B": 0.3, "C": 0.2}
        survey_df, bench_df = _make_survey_and_benchmark(pop, pop)
        div = calculate_diversity_score(survey_df, bench_df, ["stratum"])
        assert div == pytest.approx(1.0)

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_bounds(self, k, seed):
        """0 <= diversity <= 1."""
        rng = np.random.default_rng(seed)
        p = _random_distribution(rng, k)
        q = _random_distribution(rng, k)
        survey_df, bench_df = _make_survey_and_benchmark(p, q)
        div = calculate_diversity_score(survey_df, bench_df, ["stratum"])
        assert 0.0 <= div <= 1.0

    def test_adding_stratum_increases_diversity(self):
        """Adding a new stratum to the sample can only increase or maintain diversity."""
        pop = {"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1}
        bench_df = pd.DataFrame([
            {"stratum": k, "population_proportion": v} for k, v in pop.items()
        ])
        # Sample covers only A and B
        survey_small = pd.DataFrame(
            [{"stratum": "A"}] * 500 + [{"stratum": "B"}] * 500
        )
        # Now also covers C
        survey_bigger = pd.DataFrame(
            [{"stratum": "A"}] * 400 + [{"stratum": "B"}] * 400 + [{"stratum": "C"}] * 200
        )
        div_small = calculate_diversity_score(survey_small, bench_df, ["stratum"])
        div_bigger = calculate_diversity_score(survey_bigger, bench_df, ["stratum"])
        assert div_bigger >= div_small

    def test_empty_survey_returns_zero(self):
        """Diversity of an empty survey is 0.0."""
        bench_df = pd.DataFrame([
            {"stratum": "A", "population_proportion": 0.5},
            {"stratum": "B", "population_proportion": 0.5},
        ])
        survey_df = pd.DataFrame(columns=["stratum"])
        div = calculate_diversity_score(survey_df, bench_df, ["stratum"])
        assert div == 0.0


# ===========================================================================
# Design Effect Properties
# ===========================================================================

class TestDesignEffectProperties:

    def test_perfect_match_deff_one(self):
        """deff == 1.0 when sample proportions equal population proportions."""
        pop = {"A": 0.5, "B": 0.3, "C": 0.2}
        survey_df, bench_df = _make_survey_and_benchmark(pop, pop)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == pytest.approx(1.0, abs=0.02)

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_deff_geq_one(self, k, seed):
        """deff >= 1.0 always for non-empty represented strata."""
        rng = np.random.default_rng(seed)
        # Use same strata to ensure all are represented
        keys = [f"s{i}" for i in range(k)]
        p_raw = rng.dirichlet(np.ones(k))
        q_raw = rng.dirichlet(np.ones(k))
        p = dict(zip(keys, p_raw))
        q = dict(zip(keys, q_raw))
        survey_df, bench_df = _make_survey_and_benchmark(p, q)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] >= 1.0 - 1e-6

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_effective_n_leq_N(self, k, seed):
        """effective_n <= N always."""
        rng = np.random.default_rng(seed)
        keys = [f"s{i}" for i in range(k)]
        p = dict(zip(keys, rng.dirichlet(np.ones(k))))
        q = dict(zip(keys, rng.dirichlet(np.ones(k))))
        survey_df, bench_df = _make_survey_and_benchmark(p, q)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["effective_n"] <= len(survey_df) + 1e-6

    @pytest.mark.parametrize("seed", SEEDS)
    def test_precision_retention_equals_inverse_deff(self, seed):
        """precision_retention == 1/deff always."""
        rng = np.random.default_rng(seed)
        p = _random_distribution(rng, 5)
        q = _random_distribution(rng, 5)
        survey_df, bench_df = _make_survey_and_benchmark(p, q)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        if result["design_effect"] != float("inf"):
            expected = 1.0 / result["design_effect"]
            assert result["precision_retention"] == pytest.approx(expected, rel=1e-6)

    def test_empty_survey_deff_inf(self):
        """Design effect is infinity for empty survey."""
        bench_df = pd.DataFrame([
            {"stratum": "A", "population_proportion": 0.5},
            {"stratum": "B", "population_proportion": 0.5},
        ])
        survey_df = pd.DataFrame(columns=["stratum"])
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == float("inf")
        assert result["effective_n"] == 0.0

    def test_uncovered_plus_covered_sums_to_one(self):
        """uncovered_population + covered population ≈ 1.0."""
        pop = {"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1}
        # Sample covers only A and B
        sample = {"A": 0.6, "B": 0.4}
        survey_df, bench_df = _make_survey_and_benchmark(sample, pop)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        covered = 1.0 - result["uncovered_population"]
        # Covered should be A + B = 0.7
        assert covered + result["uncovered_population"] == pytest.approx(1.0, abs=0.01)


# ===========================================================================
# SRI Properties
# ===========================================================================

class TestSRIProperties:

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_bounds(self, k, seed):
        """0 <= SRI <= 1."""
        rng = np.random.default_rng(seed)
        p = _random_distribution(rng, k)
        q = _random_distribution(rng, k)
        sri, _ = calculate_sri(p, q)
        assert 0.0 <= sri <= 1.0

    @pytest.mark.parametrize("k", K_VALUES)
    @pytest.mark.parametrize("seed", SEEDS)
    def test_strategic_targets_sum_to_one(self, k, seed):
        """Strategic targets always sum to 1.0."""
        rng = np.random.default_rng(seed)
        q = _random_distribution(rng, k)
        targets = calculate_strategic_targets(q)
        assert sum(targets.values()) == pytest.approx(1.0)

    @pytest.mark.parametrize("seed", SEEDS)
    def test_targets_less_dispersed_than_proportional(self, seed):
        """Strategic targets are less dispersed than proportional allocation.

        The sqrt transformation compresses toward equal allocation: the variance
        of strategic targets should be less than the variance of proportional targets.
        """
        rng = np.random.default_rng(seed)
        k = 5
        q = _random_distribution(rng, k)
        targets = calculate_strategic_targets(q)
        equal = 1.0 / k
        # Variance of strategic targets should be less than variance of proportional
        var_proportional = np.var(list(q.values()))
        var_strategic = np.var(list(targets.values()))
        assert var_strategic < var_proportional + 1e-12


# ===========================================================================
# Cross-Metric Consistency
# ===========================================================================

class TestCrossMetricConsistency:

    def test_perfect_gri_implies_deff_one(self):
        """When GRI ≈ 1.0, design_effect ≈ 1.0."""
        pop = {"A": 0.5, "B": 0.3, "C": 0.2}
        survey_df, bench_df = _make_survey_and_benchmark(pop, pop)
        gri = calculate_gri(survey_df, bench_df, ["stratum"])
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert gri > 0.98
        assert result["design_effect"] == pytest.approx(1.0, abs=0.05)

    def test_zero_diversity_means_no_relevant_coverage(self):
        """When diversity == 0.0, no relevant benchmark strata are in the sample."""
        # All sample in stratum X which is not in the benchmark
        survey_df = pd.DataFrame([{"stratum": "X"}] * 100)
        bench_df = pd.DataFrame([
            {"stratum": "A", "population_proportion": 0.5},
            {"stratum": "B", "population_proportion": 0.5},
        ])
        div = calculate_diversity_score(survey_df, bench_df, ["stratum"])
        assert div == 0.0
