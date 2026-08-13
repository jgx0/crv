"""Unit tests for the validation/statistical summaries.

The bootstrap CI is quoted verbatim in the paper's prose, so it has to be
reproducible across runs -- an unseeded RNG previously made the generated table
disagree with the text.
"""
from __future__ import annotations

import pandas as pd

from analysis import (
    _bootstrap_mean_ci,
    build_challenge_wpa_summary,
    build_re288_sample_summary,
    build_validation_summary,
    estimate_ev_c_empirical,
    estimate_ev_c_win,
)


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


def _ev_c_corpus() -> pd.DataFrame:
    """Two games with hand-computable EV_c factors.

    Game 1: team A challenges three times (rows 1-3); the last is a failure.
    Game 2: team X challenges twice (rows 4-5), both late successes.
    """
    return pd.DataFrame(
        {
            "game_pk": [1, 1, 1, 2, 2],
            "inning": [1, 5, 9, 7, 8],
            "inning_topbot": ["Top", "Bot", "Top", "Bot", "Top"],
            "home_team": ["H", "H", "H", "X", "X"],
            "away_team": ["A", "A", "A", "Y", "Y"],
            "challenger_type": ["batter", "catcher", "batter", "batter", "catcher"],
            "challenge_success": [True, True, False, True, True],
            "delta_rv_pitch": [0.40, 0.30, 0.00, 0.60, 0.50],
            "at_bat_number": [1, 2, 3, 1, 2],
            "pitch_number": [1, 2, 3, 1, 2],
        }
    )


def _ev_c_values(result: pd.DataFrame) -> dict:
    return {row["metric"]: row["value"] for _, row in result.iterrows()}


def test_ev_c_estimate_factors_match_hand_calculation():
    result = estimate_ev_c_empirical(_ev_c_corpus(), n_boot=100)
    v = _ev_c_values(result)
    # Non-last challenges: rows 1,2,4 (3 of 5) -> P(need)=0.6.
    assert v["P(future need)"] == 0.6
    # Successes: rows 1,2,4,5 (4 of 5) -> P(win)=0.8.
    assert v["P(win)"] == 0.8
    # Late (inning >= 7) successes: rows 4 (0.60) and 5 (0.50) -> 0.55.
    assert v["Mean late-game delta RV"] == 0.55
    # EV_c = 0.6 * 0.8 * 0.55 = 0.264.
    assert v["Empirical EV_c"] == 0.264


def test_ev_c_estimate_brackets_point_with_bootstrap_ci():
    result = estimate_ev_c_empirical(_ev_c_corpus(), n_boot=200)
    ev = result[result["metric"] == "Empirical EV_c"].iloc[0]
    assert ev["ci_lower"] <= ev["value"] <= ev["ci_upper"]


def test_ev_c_estimate_handles_empty_input():
    result = estimate_ev_c_empirical(pd.DataFrame())
    assert result.empty


def test_re288_sample_summary_reports_sparsity():
    frame = pd.DataFrame({"sample_size": [10, 250, 3000, 5000]})
    result = build_re288_sample_summary(frame)
    v = {row["metric"]: row["value"] for _, row in result.iterrows()}
    assert v["RE288 cells"] == 4
    assert v["Min pitches per cell"] == 10
    assert v["Max pitches per cell"] == 5000
    assert v["Cells under 100 pitches"] == 1
    assert v["Cells under 1000 pitches"] == 2


def test_re288_sample_summary_handles_missing_column():
    assert build_re288_sample_summary(pd.DataFrame({"expected_runs": [0.5]})).empty


def test_challenge_wpa_summary_signs_to_challenger_team():
    frame = pd.DataFrame(
        {
            "home_team": ["H", "H", "H"],
            "away_team": ["A", "A", "A"],
            "inning_topbot": ["Top", "Bot", "Bot"],
            "challenger_type": ["batter", "catcher", "batter"],
            "challenge_success": [True, True, False],
            # Home team's win probability swing on the resolved pitch.
            "delta_home_win_exp": [0.05, -0.02, 0.03],
            "inning": [1, 1, 1],
            "game_pk": [1, 1, 1],
        }
    )
    # ev_c_win=0.09 -> first-inning failure penalty = -(8/9)*0.09 = -0.08.
    result = build_challenge_wpa_summary(frame, ev_c_win=0.09)
    # Row 1: Top batter = away -> -0.05 (success, no penalty).
    # Row 2: Bot catcher = fielding (away) -> +0.02 (success, no penalty).
    # Row 3: failed home batter -> 0 swing + penalty -0.08.
    assert result["events"].sum() == 3
    by_role = dict(zip(result["challenger_type"], result["total_wpa"]))
    assert abs(by_role["batter"] - (-0.05 - 0.08)) < 1e-9
    assert abs(by_role["catcher"] - 0.02) < 1e-9


def test_ev_c_win_is_product_of_factors():
    frame = pd.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "inning": [8, 8, 9],
            "inning_topbot": ["Top", "Bot", "Top"],
            "home_team": ["H", "H", "H"],
            "away_team": ["A", "A", "A"],
            "challenger_type": ["batter", "catcher", "batter"],
            "challenge_success": [True, True, False],
            "delta_home_win_exp": [0.10, -0.20, 0.05],
            "delta_rv_pitch": [0.0, 0.0, 0.0],
            "at_bat_number": [1, 2, 3],
            "pitch_number": [1, 2, 3],
        }
    )
    result = estimate_ev_c_win(frame, n_boot=100)
    v = {row["metric"]: row["value"] for _, row in result.iterrows()}
    # Signed win swings: row 1 (away batter) -0.10, row 2 (away catcher) +0.20,
    # both late successes -> mean 0.05. P(need)=2/3, P(win)=2/3.
    assert abs(v["Mean late-game win swing"] - 0.05) < 1e-9
    assert abs(v["Win-denominated EV_c"] - v["P(future need)"] * v["P(win)"] * 0.05) < 1e-12
