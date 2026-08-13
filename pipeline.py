"""End-to-end experiment runner for the CRV paper workflow."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from .analysis import (
        build_challenge_wpa_summary,
        build_crv_success_correlation,
        build_ev_sensitivity,
        build_leverage_summary,
        build_re288_sample_summary,
        build_split_half_reliability,
        build_validation_summary,
        default_ev_grid,
        estimate_ev_c_empirical,
        estimate_ev_c_win,
    )
    from .calculate import calculate_crv
    from .events import filter_challenge_events
    from .ingestion import fetch_2026_statcast_data
    from .re288 import load_re288_matrix, map_re288
    from .realities import generate_alternate_realities
except ImportError:  # pragma: no cover - allows running as script from repo root
    from analysis import (
        build_challenge_wpa_summary,
        build_crv_success_correlation,
        build_ev_sensitivity,
        build_leverage_summary,
        build_re288_sample_summary,
        build_split_half_reliability,
        build_validation_summary,
        default_ev_grid,
        estimate_ev_c_empirical,
        estimate_ev_c_win,
    )
    from calculate import calculate_crv
    from events import filter_challenge_events
    from ingestion import fetch_2026_statcast_data
    from re288 import load_re288_matrix, map_re288
    from realities import generate_alternate_realities


def _synthetic_challenge_data() -> pd.DataFrame:
    """Richer offline corpus covering non-terminal, walk, and strikeout paths."""
    return pd.DataFrame(
        [
            # Early low-leverage batter success on 0-0 strike -> ball
            {
                "game_date": "2026-04-01",
                "inning": 1,
                "inning_topbot": "Top",
                "des": "Batter challenge overturned called strike",
                "balls": 0,
                "strikes": 0,
                "outs": 0,
                "on_1b": None,
                "on_2b": None,
                "on_3b": None,
                "player_name": "Sample Batter A",
            },
            # Mid-game catcher fail on called ball
            {
                "game_date": "2026-04-01",
                "inning": 7,
                "inning_topbot": "Bot",
                "des": "Catcher challenge upheld called ball",
                "balls": 2,
                "strikes": 1,
                "outs": 1,
                "on_1b": 101,
                "on_2b": None,
                "on_3b": None,
                "player_name": "Sample Catcher B",
            },
            # 9th-inning catcher success converting ball-4 walk into strike-3 K (2 outs, runners on)
            {
                "game_date": "2026-04-02",
                "inning": 9,
                "inning_topbot": "Top",
                "des": "Catcher challenge overturned called ball",
                "balls": 3,
                "strikes": 2,
                "outs": 2,
                "on_1b": 101,
                "on_2b": 202,
                "on_3b": None,
                "player_name": "Sample Catcher C",
            },
            # Early failed batter challenge
            {
                "game_date": "2026-04-02",
                "inning": 2,
                "inning_topbot": "Bot",
                "des": "Batter abs challenge upheld called strike",
                "balls": 1,
                "strikes": 1,
                "outs": 0,
                "on_1b": None,
                "on_2b": 202,
                "on_3b": None,
                "player_name": "Sample Batter D",
            },
            # Batter success converting called strike-3 into ball-4 walk, bases loaded
            {
                "game_date": "2026-04-05",
                "inning": 4,
                "inning_topbot": "Top",
                "des": "Batter challenge overturned called strike",
                "balls": 3,
                "strikes": 2,
                "outs": 1,
                "on_1b": 101,
                "on_2b": 202,
                "on_3b": 303,
                "player_name": "Sample Batter E",
            },
            # Extra-inning failed challenge (penalty should be zero)
            {
                "game_date": "2026-04-06",
                "inning": 11,
                "inning_topbot": "Top",
                "des": "Catcher challenge upheld called strike",
                "balls": 1,
                "strikes": 2,
                "outs": 1,
                "on_1b": None,
                "on_2b": None,
                "on_3b": None,
                "player_name": "Sample Catcher F",
            },
            # Catcher success turning a would-be walk into a strike (non-terminal)
            {
                "game_date": "2026-04-07",
                "inning": 8,
                "inning_topbot": "Bot",
                "des": "Catcher challenge overturned called ball",
                "balls": 2,
                "strikes": 1,
                "outs": 0,
                "on_1b": 101,
                "on_2b": None,
                "on_3b": 303,
                "player_name": "Sample Catcher C",
            },
            # Batter success avoiding K looking with runner on 3rd, 2 outs
            {
                "game_date": "2026-04-08",
                "inning": 6,
                "inning_topbot": "Top",
                "des": "Batter challenge overturned called strike",
                "balls": 2,
                "strikes": 2,
                "outs": 2,
                "on_1b": None,
                "on_2b": None,
                "on_3b": 303,
                "player_name": "Sample Batter A",
            },
            # Ambiguous description quality check (still has challenge + outcome)
            {
                "game_date": "2026-04-09",
                "inning": 5,
                "inning_topbot": "Bot",
                "des": "Challenge overturned to a ball",
                "balls": 0,
                "strikes": 1,
                "outs": 0,
                "on_1b": None,
                "on_2b": None,
                "on_3b": None,
                "player_name": "Sample Unknown G",
            },
            # Late-game batter fail on 3-2
            {
                "game_date": "2026-04-10",
                "inning": 9,
                "inning_topbot": "Bot",
                "des": "Batter challenge upheld called strike",
                "balls": 3,
                "strikes": 1,
                "outs": 2,
                "on_1b": 101,
                "on_2b": None,
                "on_3b": None,
                "player_name": "Sample Batter D",
            },
        ]
    )


# Prose headers for the LaTeX tables. Emitting the raw snake_case dataframe
# column names instead sets an unbreakable \_-laden header row that overflows
# the JQAS text block (the leaderboard ran 58pt over), and reads like a debug
# dump rather than a journal table.
_TABLE_HEADERS = {
    "player_name": "Player",
    "challenger_type": "Role",
    "total_challenges": "Challenges",
    "success_rate": "Success rate",
    "cumulative_cRV": "Cumulative $cRV$",
    "mean_cRV": "Mean $cRV$",
    "sum_cRV": "Total $cRV$",
    "ev_c": "$EV_c$",
    "leverage_bucket": "Leverage bucket",
    "events": "Events",
    "metric": "Metric",
    "value": "Value",
    "ci_lower": "CI lower",
    "ci_upper": "CI upper",
    "notes": "Notes",
    "parse_quality": "Parse quality",
    "total_wpa": "Total cWPA",
    "mean_wpa": "Mean cWPA",
}


def _header_label(col: str) -> str:
    """Journal-style column heading; falls back to the de-underscored name."""
    return _TABLE_HEADERS.get(col, col.replace("_", " ").capitalize())


def _metric_value(metric_df: pd.DataFrame, metric: str) -> float:
    """Extract the ``value`` for a named metric row, defaulting to 0.0."""
    if metric_df is None or metric_df.empty or "metric" not in metric_df.columns:
        return 0.0
    rows = metric_df[metric_df["metric"] == metric]
    return float(rows.iloc[0]["value"]) if not rows.empty else 0.0


def _write_latex_table(df: pd.DataFrame, out_path: Path, caption: str, label: str) -> None:
    if df.empty:
        out_path.write_text("% no data\n", encoding="utf-8")
        return

    cols = list(df.columns)
    # Numbers right-align so decimal points stack; text stays flush left.
    fmt = "".join("r" if pd.api.types.is_numeric_dtype(df[c]) else "l" for c in cols)
    lines = [
        "\\begin{table}[h]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        # \small buys ~15% width. The widest table (the 6-column leaderboard)
        # still ran 11pt over the JQAS text block at 12pt body size even with
        # prose headers, and journal tables conventionally set smaller than body.
        "\\small",
        f"\\begin{{tabular}}{{{fmt}}}",
        "\\toprule",
        " & ".join(_header_label(c) for c in cols) + " \\\\",
        "\\midrule",
    ]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                vals.append("unknown")
            elif isinstance(v, float):
                # Wrap numerics in math mode so negatives get a real minus sign
                # rather than a text hyphen -- the leaderboard is full of
                # negative cRV values and "-0.117" sets noticeably wrong.
                # Integer-valued floats (counts like 1914.0) print without a
                # trailing ".000". -0.000 is a rounding artifact of a tiny
                # negative; print it as 0.000 so the table does not assert a
                # negative that isn't there.
                if v.is_integer():
                    s = str(int(v))
                else:
                    s = f"{v:.3f}"
                    if s == "-0.000":
                        s = "0.000"
                vals.append(f"${s}$")
            elif str(v).lower() == "nan":
                vals.append("unknown")
            else:
                vals.append(str(v))
        lines.append(" & ".join(vals).replace("_", "\\_") + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}"])
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment(
    output_dir: Path,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    re288_path: Optional[str] = None,
    force_synthetic: bool = False,
) -> dict:
    """Run the full CRV pipeline and write paper artifacts.

    Returns a small metadata dict describing the data source used.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    data_source = "statcast"
    if force_synthetic:
        raw = pd.DataFrame()
    else:
        raw = fetch_2026_statcast_data(start_date=start_date, end_date=end_date)

    if raw is None or raw.empty:
        raw = _synthetic_challenge_data()
        data_source = "synthetic"

    challenges = filter_challenge_events(raw)
    if challenges.empty and data_source == "statcast":
        # Statcast returned rows but none looked like challenges — still fall back for offline demos.
        raw = _synthetic_challenge_data()
        data_source = "synthetic_fallback"
        challenges = filter_challenge_events(raw)

    realities = generate_alternate_realities(challenges)
    # Prefer empirical RE288 from the same pbp pull when available.
    re288 = load_re288_matrix(path=re288_path, pbp_df=raw if data_source == "statcast" else None)
    re288_source = "csv" if re288_path else ("empirical" if data_source == "statcast" else "synthetic")
    # If empirical estimation failed silently, mark synthetic.
    if re288_path is None and data_source == "statcast":
        if "sample_size" not in re288.columns:
            re288_source = "synthetic"

    mapped = map_re288(realities, re288)
    scored = calculate_crv(mapped)

    scored.to_csv(output_dir / "challenge_events_scored.csv", index=False)
    re288.to_csv(output_dir / "re288_matrix.csv", index=False)

    meta = pd.DataFrame(
        [
            {"key": "data_source", "value": data_source},
            {"key": "re288_source", "value": re288_source},
            {"key": "n_events", "value": str(len(scored))},
            {"key": "n_re288_states", "value": str(len(re288))},
        ]
    )
    meta.to_csv(output_dir / "run_metadata.csv", index=False)

    id_col = "player_name" if "player_name" in scored.columns else "challenger_type"
    leaderboard = (
        scored.groupby([id_col, "challenger_type"], dropna=False)
        .agg(
            total_challenges=("cRV", "count"),
            success_rate=("challenge_success", "mean"),
            cumulative_cRV=("cRV", "sum"),
            mean_cRV=("cRV", "mean"),
        )
        .reset_index()
        .sort_values("cumulative_cRV", ascending=False)
    )
    leaderboard.to_csv(output_dir / "player_leaderboard.csv", index=False)

    challenger_summary = (
        scored.groupby("challenger_type", dropna=False)
        .agg(total_challenges=("cRV", "count"), cumulative_cRV=("cRV", "sum"), mean_cRV=("cRV", "mean"))
        .reset_index()
        .sort_values("cumulative_cRV", ascending=False)
    )
    challenger_summary.to_csv(output_dir / "challenger_summary.csv", index=False)

    validation_summary = build_validation_summary(scored, n_boot=1000)
    validation_summary.to_csv(output_dir / "validation_summary.csv", index=False)

    leverage_summary = build_leverage_summary(scored)
    leverage_summary.to_csv(output_dir / "leverage_summary.csv", index=False)

    # Estimate EV_c (run- and win-denominated) before the sensitivity sweep, so
    # the grid can be extended down to include the empirical run value.
    ev_c_estimate = estimate_ev_c_empirical(scored)
    ev_c_estimate.to_csv(output_dir / "ev_c_estimate.csv", index=False)

    ev_c_win_estimate = estimate_ev_c_win(scored)
    ev_c_win_estimate.to_csv(output_dir / "ev_c_win_estimate.csv", index=False)

    empirical_ev_c = _metric_value(ev_c_estimate, "Empirical EV_c")

    ev_sensitivity = build_ev_sensitivity(scored, ev_values=default_ev_grid(empirical_ev_c))
    ev_sensitivity.to_csv(output_dir / "ev_sensitivity.csv", index=False)

    re288_sample_summary = build_re288_sample_summary(re288)
    re288_sample_summary.to_csv(output_dir / "re288_sample_summary.csv", index=False)

    challenge_wpa_summary = build_challenge_wpa_summary(scored)
    challenge_wpa_summary.to_csv(output_dir / "challenge_wpa_summary.csv", index=False)

    crv_success_corr = build_crv_success_correlation(scored)
    crv_success_corr.to_csv(output_dir / "crv_success_correlation.csv", index=False)

    split_half_reliability = build_split_half_reliability(scored)
    split_half_reliability.to_csv(output_dir / "split_half_reliability.csv", index=False)

    # Parse-quality summary for event isolation validation
    if "parse_quality" in scored.columns:
        parse_summary = (
            scored.groupby("parse_quality", dropna=False)
            .size()
            .reset_index(name="events")
            .sort_values("events", ascending=False)
        )
        parse_summary.to_csv(output_dir / "parse_quality_summary.csv", index=False)
    else:
        parse_summary = pd.DataFrame(columns=["parse_quality", "events"])

    # Figures are rendered by figures.py (vector PDF + SVG) from the CSVs
    # written above, so the paper's \includegraphics targets resolve.
    try:
        from figures import build_all_figures

        build_all_figures(output_dir)
    except ImportError:  # matplotlib absent -> tables and CSVs still ship
        pass

    _write_latex_table(
        leaderboard.head(10),
        out_path=tables_dir / "leaderboard_top10.tex",
        caption="Top player-level cumulative cRV values.",
        label="tab:leaderboard",
    )
    _write_latex_table(
        validation_summary,
        out_path=tables_dir / "validation_summary.tex",
        caption="Validation summary metrics for the current run.",
        label="tab:validation",
    )
    _write_latex_table(
        leverage_summary,
        out_path=tables_dir / "leverage_summary.tex",
        caption="cRV by inning leverage bucket.",
        label="tab:leverage",
    )
    _write_latex_table(
        ev_sensitivity,
        out_path=tables_dir / "ev_sensitivity.tex",
        caption="Sensitivity of aggregate cRV to the baseline challenge value $EV_c$.",
        label="tab:evsens",
    )
    _write_latex_table(
        challenger_summary,
        out_path=tables_dir / "challenger_summary.tex",
        caption="Aggregate cRV by challenger role.",
        label="tab:challenger",
    )
    _write_latex_table(
        ev_c_estimate,
        out_path=tables_dir / "ev_c_estimate.tex",
        caption="Empirical estimate of the retained-challenge value $EV_c$.",
        label="tab:evc",
    )
    _write_latex_table(
        ev_c_win_estimate,
        out_path=tables_dir / "ev_c_win_estimate.tex",
        caption="Empirical estimate of the win-denominated retained-challenge value.",
        label="tab:evcwin",
    )
    _write_latex_table(
        re288_sample_summary,
        out_path=tables_dir / "re288_sample_summary.tex",
        caption="Per-cell sample sizes of the empirical RE288 surface.",
        label="tab:re288samples",
    )
    _write_latex_table(
        challenge_wpa_summary,
        out_path=tables_dir / "challenge_wpa_summary.tex",
        caption="Realized win-probability swing of successful overturns by role.",
        label="tab:cwpa",
    )
    _write_latex_table(
        pd.concat([crv_success_corr, split_half_reliability], ignore_index=True),
        out_path=tables_dir / "metric_information.tex",
        caption="Information and reliability of player-level cRV.",
        label="tab:info",
    )

    empirical_ev_c = _metric_value(ev_c_estimate, "Empirical EV_c")
    empirical_ev_c_win = _metric_value(ev_c_win_estimate, "Win-denominated EV_c")

    return {
        "data_source": data_source,
        "re288_source": re288_source,
        "n_events": len(scored),
        "n_re288_states": len(re288),
        "empirical_ev_c": empirical_ev_c,
        "empirical_ev_c_win": empirical_ev_c_win,
        "output_dir": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CRV experiments and generate paper artifacts.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for experiment outputs")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--re288-path", default=None, help="Optional CSV path for real RE288 matrix")
    parser.add_argument(
        "--force-synthetic",
        action="store_true",
        help="Skip Statcast fetch and use the built-in synthetic challenge corpus",
    )
    args = parser.parse_args()

    meta = run_experiment(
        output_dir=Path(args.output_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        re288_path=args.re288_path,
        force_synthetic=args.force_synthetic,
    )
    print(
        f"CRV run complete | source={meta['data_source']} "
        f"re288={meta['re288_source']} events={meta['n_events']} "
        f"empirical_ev_c={meta['empirical_ev_c']:.4f} "
        f"ev_c_win={meta['empirical_ev_c_win']:.5f} "
        f"-> {meta['output_dir']}"
    )


if __name__ == "__main__":
    main()
