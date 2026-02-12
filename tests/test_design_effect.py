"""
Unit tests for the design effect module.

Tests cover:
- Perfect match → deff=1.0
- Empty survey → deff=inf
- Known manual calculation
- Uncovered population tracking
- Single stratum edge case
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gri import calculate_design_effect


def _make_survey_benchmark(sample_counts, pop_props, strata_col="stratum"):
    """Create survey and benchmark DataFrames from simple dicts.

    Args:
        sample_counts: {stratum: count} — raw participant counts
        pop_props: {stratum: proportion} — population proportions (should sum to 1)
    """
    survey_rows = []
    for k, n in sample_counts.items():
        survey_rows.extend([{strata_col: k}] * n)
    survey_df = pd.DataFrame(survey_rows) if survey_rows else pd.DataFrame(columns=[strata_col])

    bench_rows = [
        {strata_col: k, "population_proportion": v} for k, v in pop_props.items()
    ]
    benchmark_df = pd.DataFrame(bench_rows)
    return survey_df, benchmark_df


class TestDesignEffectBasic:

    def test_perfect_match(self):
        """When sample proportions equal population proportions, deff=1.0."""
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 500, "B": 300, "C": 200},
            {"A": 0.5, "B": 0.3, "C": 0.2},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == pytest.approx(1.0, abs=0.001)
        assert result["effective_n"] == pytest.approx(1000.0, abs=1.0)
        assert result["precision_retention"] == pytest.approx(1.0, abs=0.001)

    def test_empty_survey(self):
        """Empty survey → deff=inf, effective_n=0."""
        survey_df, bench_df = _make_survey_benchmark(
            {},
            {"A": 0.5, "B": 0.5},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == float("inf")
        assert result["effective_n"] == 0.0
        assert result["precision_retention"] == 0.0
        assert result["uncovered_population"] == 1.0

    def test_single_stratum(self):
        """Single stratum: deff=1.0 regardless (trivial case)."""
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 100},
            {"A": 1.0},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == pytest.approx(1.0)
        assert result["effective_n"] == pytest.approx(100.0)

    def test_known_manual_calculation(self):
        """Hand-computed design effect for a simple 2-stratum example.

        Population: A=0.5, B=0.5
        Sample: A=800, B=200 → p_A=0.8, p_B=0.2

        Renormalized (all represented, q_sum=1.0):
        deff = q_A^2/p_A + q_B^2/p_B = 0.25/0.8 + 0.25/0.2 = 0.3125 + 1.25 = 1.5625
        effective_n = 1000 / 1.5625 = 640
        precision_retention = 1/1.5625 = 0.64
        """
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 800, "B": 200},
            {"A": 0.5, "B": 0.5},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == pytest.approx(1.5625, rel=1e-4)
        assert result["effective_n"] == pytest.approx(640.0, rel=1e-3)
        assert result["precision_retention"] == pytest.approx(0.64, rel=1e-3)

    def test_uncovered_population(self):
        """Strata in benchmark but absent from sample show up as uncovered."""
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 600, "B": 400},
            {"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        # C and D are uncovered: 0.2 + 0.1 = 0.3
        assert result["uncovered_population"] == pytest.approx(0.3)
        assert result["n_represented_strata"] == 2
        assert result["n_benchmark_strata"] == 4

    def test_all_strata_uncovered(self):
        """When sample has only strata not in benchmark, deff=inf."""
        survey_df, bench_df = _make_survey_benchmark(
            {"X": 500, "Y": 500},
            {"A": 0.5, "B": 0.5},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["design_effect"] == float("inf")
        assert result["effective_n"] == 0.0


class TestDesignEffectEdgeCases:

    def test_extreme_imbalance(self):
        """Very skewed sample produces high deff."""
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 990, "B": 10},
            {"A": 0.5, "B": 0.5},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        # Very unbalanced: deff should be significantly > 1
        assert result["design_effect"] > 5.0
        assert result["effective_n"] < 200.0

    def test_result_keys_present(self):
        """All expected keys are in the result dict."""
        survey_df, bench_df = _make_survey_benchmark(
            {"A": 500, "B": 500},
            {"A": 0.5, "B": 0.5},
        )
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        expected_keys = {
            "design_effect",
            "effective_n",
            "precision_retention",
            "n_represented_strata",
            "n_benchmark_strata",
            "uncovered_population",
        }
        assert set(result.keys()) == expected_keys

    def test_many_strata_some_uncovered(self):
        """With many benchmark strata, partial coverage works correctly."""
        pop_props = {f"s{i}": 1.0 / 10 for i in range(10)}
        # Sample only covers 5 of 10
        sample_counts = {f"s{i}": 200 for i in range(5)}
        survey_df, bench_df = _make_survey_benchmark(sample_counts, pop_props)
        result = calculate_design_effect(survey_df, bench_df, ["stratum"])
        assert result["uncovered_population"] == pytest.approx(0.5)
        assert result["n_represented_strata"] == 5
        assert result["n_benchmark_strata"] == 10
