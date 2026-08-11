"""Unit tests for the validation/statistical summaries.

The bootstrap CI is quoted verbatim in the paper's prose, so it has to be
reproducible across runs -- an unseeded RNG previously made the generated table
disagree with the text.
"""
from __future__ import annotations

import pandas as pd

from analysis import _bootstrap_mean_ci, build_validation_summary


def _corpus() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "cRV": [1.32, 0.53, 0.23, 0.0, 0.0, -0.033, -0.117, 0.11, 0.05, -0.02],
            "challenge_success": [1, 1, 1, 1, 0, 0, 0, 1, 1, 0],
        }
    )


def test_bootstrap_ci_is_reproducible():
    values = _corpus()["cRV"]
    first = _bootstrap_mean_ci(values, n_boot=500)
    second = _bootstrap_mean_ci(values, n_boot=500)
    assert first == second


def test_bootstrap_ci_brackets_the_sample_mean():
    values = _corpus()["cRV"]
    low, high = _bootstrap_mean_ci(values, n_boot=500)
    assert low <= values.mean() <= high


def test_bootstrap_ci_respects_explicit_seed():
    values = _corpus()["cRV"]
    assert _bootstrap_mean_ci(values, n_boot=500, seed=1) != _bootstrap_mean_ci(
        values, n_boot=500, seed=2
    )


def test_single_observation_ci_collapses_to_the_point():
    low, high = _bootstrap_mean_ci(pd.Series([0.4]), n_boot=100)
    assert (low, high) == (0.4, 0.4)


def test_empty_series_yields_zero_bounds():
    assert _bootstrap_mean_ci(pd.Series([], dtype=float)) == (0.0, 0.0)


def test_validation_summary_is_reproducible_end_to_end():
    corpus = _corpus()
    first = build_validation_summary(corpus, n_boot=500)
    second = build_validation_summary(corpus, n_boot=500)
    pd.testing.assert_frame_equal(first, second)


def test_validation_summary_reports_prose_ready_metric_labels():
    # The Metric column is printed directly into the LaTeX table, so it must
    # carry prose labels rather than raw snake_case identifiers.
    summary = build_validation_summary(_corpus(), n_boot=200)
    assert list(summary["metric"]) == ["Total events", "Success rate", "Mean cRV"]
