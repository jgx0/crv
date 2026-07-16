"""End-to-end experiment runner for the CRV paper workflow."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from .analysis import build_ev_sensitivity, build_leverage_summary, build_validation_summary, default_ev_grid
    from .calculate import calculate_crv
    from .events import filter_challenge_events
    from .ingestion import fetch_2026_statcast_data
    from .re288 import load_re288_matrix, map_re288
    from .realities import generate_alternate_realities
except ImportError:  # pragma: no cover - allows running as script from repo root
    from analysis import build_ev_sensitivity, build_leverage_summary, build_validation_summary, default_ev_grid
    from calculate import calculate_crv
    from events import filter_challenge_events
    from ingestion import fetch_2026_statcast_data
    from re288 import load_re288_matrix, map_re288
    from realities import generate_alternate_realities


def _synthetic_challenge_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
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
        ]
    )


def _write_simple_bar_svg(df: pd.DataFrame, value_col: str, label_col: str, out_path: Path, title: str) -> None:
    width = 900
    height = 520
    margin = 60

    rows = df.head(10).copy()
    if rows.empty:
        out_path.write_text("<svg xmlns='http://www.w3.org/2000/svg' width='900' height='200'><text x='20' y='40'>No data available.</text></svg>", encoding="utf-8")
        return

    max_val = max(rows[value_col].abs().max(), 0.001)
    bar_area = width - 2 * margin
    bar_height = 30
    gap = 12

    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<style>text{font-family:Arial,sans-serif;font-size:13px} .title{font-size:18px;font-weight:bold}</style>",
        f"<text class='title' x='{margin}' y='30'>{title}</text>",
    ]

    y = 70
    for _, row in rows.iterrows():
        value = float(row[value_col])
        label = str(row[label_col])
        bar_w = int((abs(value) / max_val) * (bar_area * 0.7))
        color = "#2a9d8f" if value >= 0 else "#e76f51"
        lines.append(f"<text x='{margin}' y='{y + 18}'>{label}</text>")
        lines.append(f"<rect x='{margin + 220}' y='{y}' width='{bar_w}' height='{bar_height}' fill='{color}' />")
        lines.append(f"<text x='{margin + 230 + bar_w}' y='{y + 20}'>{value:.3f}</text>")
        y += bar_height + gap

    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_pipeline_diagram(out_path: Path) -> None:
    svg = """<svg xmlns='http://www.w3.org/2000/svg' width='980' height='240'>
<style>text{font-family:Arial,sans-serif;font-size:14px}.h{font-size:18px;font-weight:bold}</style>
<text x='20' y='28' class='h'>CRV Pipeline</text>
<rect x='20' y='60' width='170' height='56' rx='8' fill='#dbeafe'/><text x='46' y='93'>Ingestion</text>
<rect x='210' y='60' width='170' height='56' rx='8' fill='#dcfce7'/><text x='232' y='93'>Event Filter</text>
<rect x='400' y='60' width='170' height='56' rx='8' fill='#fef3c7'/><text x='414' y='93'>State Generator</text>
<rect x='590' y='60' width='170' height='56' rx='8' fill='#ede9fe'/><text x='618' y='93'>RE288 Mapping</text>
<rect x='780' y='60' width='170' height='56' rx='8' fill='#fee2e2'/><text x='824' y='93'>cRV Engine</text>
<line x1='190' y1='88' x2='210' y2='88' stroke='black'/><line x1='380' y1='88' x2='400' y2='88' stroke='black'/><line x1='570' y1='88' x2='590' y2='88' stroke='black'/><line x1='760' y1='88' x2='780' y2='88' stroke='black'/>
<text x='20' y='170'>Outputs: challenge_events.csv, player_leaderboard.csv, figures/*.svg</text>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")


def _write_sensitivity_svg(df: pd.DataFrame, out_path: Path, title: str) -> None:
    width = 900
    height = 500
    margin = 60
    if df.empty:
        out_path.write_text(
            "<svg xmlns='http://www.w3.org/2000/svg' width='900' height='200'><text x='20' y='40'>No sensitivity data available.</text></svg>",
            encoding="utf-8",
        )
        return

    x_vals = pd.to_numeric(df["ev_c"], errors="coerce").fillna(0.0)
    y_vals = pd.to_numeric(df["sum_cRV"], errors="coerce").fillna(0.0)
    x_min, x_max = float(x_vals.min()), float(x_vals.max())
    y_min, y_max = float(y_vals.min()), float(y_vals.max())
    x_span = max(x_max - x_min, 1e-6)
    y_span = max(y_max - y_min, 1e-6)

    def sx(x: float) -> float:
        return margin + ((x - x_min) / x_span) * (width - 2 * margin)

    def sy(y: float) -> float:
        return height - margin - ((y - y_min) / y_span) * (height - 2 * margin)

    points = " ".join(f"{sx(float(x)):.2f},{sy(float(y)):.2f}" for x, y in zip(x_vals, y_vals))
    lines = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<style>text{font-family:Arial,sans-serif;font-size:13px}.title{font-size:18px;font-weight:bold}</style>",
        f"<text class='title' x='{margin}' y='30'>{title}</text>",
        f"<line x1='{margin}' y1='{height-margin}' x2='{width-margin}' y2='{height-margin}' stroke='black'/>",
        f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height-margin}' stroke='black'/>",
        f"<polyline points='{points}' fill='none' stroke='#2563eb' stroke-width='3'/>",
    ]
    for x, y in zip(x_vals, y_vals):
        lines.append(f"<circle cx='{sx(float(x)):.2f}' cy='{sy(float(y)):.2f}' r='4' fill='#2563eb'/>")
        lines.append(f"<text x='{sx(float(x)) - 8:.2f}' y='{height-margin+20:.2f}'>{float(x):.2f}</text>")
        lines.append(f"<text x='{sx(float(x)) + 6:.2f}' y='{sy(float(y)) - 8:.2f}'>{float(y):.3f}</text>")
    lines.append(f"<text x='{width/2 - 30:.2f}' y='{height-12}'>EV_c</text>")
    lines.append(f"<text x='8' y='{height/2:.2f}' transform='rotate(-90 8,{height/2:.2f})'>Total cRV</text>")
    lines.append("</svg>")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_latex_table(df: pd.DataFrame, out_path: Path, caption: str, label: str) -> None:
    if df.empty:
        out_path.write_text("% no data\n", encoding="utf-8")
        return

    cols = list(df.columns)
    if len(cols) > 1:
        fmt = "l" + "r" * (len(cols) - 2) + "l"
    else:
        fmt = "l"
    lines = [
        "\\begin{table}[h]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{fmt}}}",
        "\\toprule",
        " & ".join(cols).replace("_", "\\_") + " \\\\",
        "\\midrule",
    ]
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.3f}")
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
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    raw = fetch_2026_statcast_data(start_date=start_date, end_date=end_date)
    if raw.empty:
        raw = _synthetic_challenge_data()

    challenges = filter_challenge_events(raw)
    realities = generate_alternate_realities(challenges)
    re288 = load_re288_matrix(re288_path)
    mapped = map_re288(realities, re288)
    scored = calculate_crv(mapped)

    scored.to_csv(output_dir / "challenge_events_scored.csv", index=False)

    id_col = "player_name" if "player_name" in scored.columns else "challenger_type"
    leaderboard = (
        scored.groupby([id_col, "challenger_type"], dropna=False)
        .agg(
            total_challenges=("cRV", "count"),
            success_rate=("challenge_success", "mean"),
            cumulative_cRV=("cRV", "sum"),
        )
        .reset_index()
        .sort_values("cumulative_cRV", ascending=False)
    )
    leaderboard.to_csv(output_dir / "player_leaderboard.csv", index=False)

    challenger_summary = (
        scored.groupby("challenger_type", dropna=False)
        .agg(total_challenges=("cRV", "count"), cumulative_cRV=("cRV", "sum"))
        .reset_index()
        .sort_values("cumulative_cRV", ascending=False)
    )
    challenger_summary.to_csv(output_dir / "challenger_summary.csv", index=False)

    validation_summary = build_validation_summary(scored, n_boot=1000)
    validation_summary.to_csv(output_dir / "validation_summary.csv", index=False)

    leverage_summary = build_leverage_summary(scored)
    leverage_summary.to_csv(output_dir / "leverage_summary.csv", index=False)

    ev_sensitivity = build_ev_sensitivity(scored, ev_values=default_ev_grid())
    ev_sensitivity.to_csv(output_dir / "ev_sensitivity.csv", index=False)

    _write_simple_bar_svg(
        leaderboard,
        value_col="cumulative_cRV",
        label_col=id_col,
        out_path=figures_dir / "leaderboard_top10.svg",
        title="Top cRV Contributors",
    )
    _write_simple_bar_svg(
        challenger_summary,
        value_col="cumulative_cRV",
        label_col="challenger_type",
        out_path=figures_dir / "challenger_totals.svg",
        title="cRV by Challenger Type",
    )
    _write_pipeline_diagram(figures_dir / "pipeline_diagram.svg")
    _write_sensitivity_svg(
        ev_sensitivity,
        out_path=figures_dir / "ev_sensitivity.svg",
        title="Sensitivity of Total cRV to EV_c",
    )
    _write_latex_table(
        leaderboard.head(10),
        out_path=tables_dir / "leaderboard_top10.tex",
        caption="Top 10 player-level cumulative cRV values.",
        label="tab:leaderboard",
    )
    _write_latex_table(
        validation_summary,
        out_path=tables_dir / "validation_summary.tex",
        caption="Validation summary metrics for the current run.",
        label="tab:validation",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CRV experiments and generate paper artifacts.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for experiment outputs")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--re288-path", default=None, help="Optional CSV path for real RE288 matrix")
    args = parser.parse_args()

    run_experiment(
        output_dir=Path(args.output_dir),
        start_date=args.start_date,
        end_date=args.end_date,
        re288_path=args.re288_path,
    )


if __name__ == "__main__":
    main()
