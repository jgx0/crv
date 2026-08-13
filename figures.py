"""Publication figures for the CRV paper.

Renders vector PDF (and SVG) figures from the pipeline's CSV outputs.

Design system parameters (validated reference palette):
  - cRV is a *signed* quantity, so player/role charts use a DIVERGING encoding:
    blue (positive) vs red (negative) with zero as the neutral baseline. Bar
    direction relative to the zero rule is the secondary encoding, so sign
    survives grayscale print and CVD.
  - The EV_c sensitivity chart is a single series -> categorical slot 1, no
    legend box (the title names it).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.path import Path as MplPath
from matplotlib.patches import FancyBboxPatch, PathPatch

# --- Design tokens (light mode, reference palette) -------------------------
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

POSITIVE = "#2a78d6"  # diverging pole: value added
NEGATIVE = "#e34948"  # diverging pole: value destroyed

# px -> pt (figures are authored in px per the mark specs; PDF units are pt)
PX = 0.75
BAR_MAX_PX = 24.0
ROUND_PX = 4.0
LINE_PX = 2.0
RING_PX = 2.0
MARKER_PX = 8.0

FONT_STACK = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
TITLE_WEIGHT = "bold"  # DejaVu has no semibold face; asking for it just warns.


def _style_axes(ax, *, xgrid: bool = True, ygrid: bool = False) -> None:
    """Recessive hairline chrome; no chartjunk."""
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=TEXT_MUTED, labelsize=8, length=0)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(TEXT_SECONDARY)
    if xgrid:
        ax.xaxis.grid(True, color=GRIDLINE, linewidth=1 * PX, linestyle="-", zorder=0)
    if ygrid:
        ax.yaxis.grid(True, color=GRIDLINE, linewidth=1 * PX, linestyle="-", zorder=0)
    ax.set_axisbelow(True)


def _data_per_px_x(ax) -> float:
    """Data units per pixel along x, for px-denominated corner radii."""
    fig = ax.figure
    bbox = ax.get_window_extent(renderer=fig.canvas.get_renderer())
    x0, x1 = ax.get_xlim()
    width_px = max(bbox.width, 1.0)
    return (x1 - x0) / width_px


def _rounded_hbar_path(value: float, y_center: float, height: float, radius: float) -> MplPath:
    """Horizontal bar: square at the zero baseline, rounded at the data end."""
    y0 = y_center - height / 2.0
    y1 = y_center + height / 2.0
    r = max(0.0, min(radius, abs(value) / 2.0, height / 2.0))
    sign = 1.0 if value >= 0 else -1.0
    tip = value
    shoulder = value - sign * r  # where the rounded end begins

    verts = [
        (0.0, y0),
        (shoulder, y0),
        (tip, y0),
        (tip, y0 + r),
        (tip, y1 - r),
        (tip, y1),
        (shoulder, y1),
        (0.0, y1),
        (0.0, y0),
    ]
    codes = [
        MplPath.MOVETO,
        MplPath.LINETO,
        MplPath.CURVE3,
        MplPath.CURVE3,
        MplPath.LINETO,
        MplPath.CURVE3,
        MplPath.CURVE3,
        MplPath.LINETO,
        MplPath.CLOSEPOLY,
    ]
    return MplPath(verts, codes)


def _draw_signed_hbars(ax, labels, values, *, bar_px: float = BAR_MAX_PX) -> None:
    """Diverging horizontal bars anchored to a zero rule."""
    n = len(values)
    ax.set_ylim(-0.5, n - 0.5)

    span = max(max(values, default=0.0), 0.0) - min(min(values, default=0.0), 0.0)
    span = span if span > 0 else 1.0
    pad = span * 0.18
    lo = min(min(values, default=0.0), 0.0) - pad
    hi = max(max(values, default=0.0), 0.0) + pad
    ax.set_xlim(lo, hi)

    ax.set_yticks(range(n))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()

    # Bar thickness: capped, never filling the slot (leftover band is air).
    fig = ax.figure
    bbox = ax.get_window_extent(renderer=fig.canvas.get_renderer())
    px_per_slot = bbox.height / max(n, 1)
    bar_px_eff = min(bar_px, px_per_slot * 0.62)
    height = bar_px_eff / px_per_slot  # in data (slot) units

    radius = ROUND_PX * _data_per_px_x(ax)

    for i, value in enumerate(values):
        color = POSITIVE if value >= 0 else NEGATIVE
        patch = PathPatch(
            _rounded_hbar_path(float(value), i, height, radius),
            facecolor=color,
            edgecolor="none",
            zorder=3,
        )
        ax.add_patch(patch)

        # Bars -> value at the tip, offset outward so text never sits on the fill.
        offset = (hi - lo) * 0.012
        ha = "left" if value >= 0 else "right"
        ax.text(
            value + (offset if value >= 0 else -offset),
            i,
            f"{value:+.3f}",
            va="center",
            ha=ha,
            fontsize=8,
            color=TEXT_SECONDARY,
            zorder=4,
        )

    # Zero rule: the diverging midpoint.
    ax.axvline(0.0, color=BASELINE, linewidth=1 * PX, zorder=2)


# JQAS requires figures as separate EPS/TIF/JPG files. EPS is the vector
# target (line art, 1200 dpi recommended); TIF is the raster fallback at
# 600 dpi, comfortably above the 300 dpi halftone floor.
SUBMISSION_FORMATS = ("eps", "tif")
WORKING_FORMATS = ("pdf", "svg")
TIF_DPI = 600

# Journal captions carry the figure title, so the artwork ships untitled.
# Set CRV_FIGURE_TITLES=1 to bake titles in for local reading.
EMBED_TITLES = os.environ.get("CRV_FIGURE_TITLES", "") == "1"

# The player leaderboard shows the top challengers by cumulative cRV. A full
# season has hundreds; plotting all of them makes an unreadable, gigantic
# figure. Overridable via CRV_LEADERBOARD_TOP_N for exploration.
LEADERBOARD_TOP_N = int(os.environ.get("CRV_LEADERBOARD_TOP_N", "15"))


def _set_title(ax, text: str) -> None:
    """Title the axes only when building for local reading, not for journal.

    JQAS wants each figure's descriptive title in the legend on a separate
    page, so a baked-in title would duplicate it in print.
    """
    if not EMBED_TITLES:
        return
    ax.set_title(
        text,
        fontsize=11,
        color=TEXT_PRIMARY,
        loc="left",
        pad=14,
        fontweight=TITLE_WEIGHT,
    )


def _finish(fig, out_stem: Path) -> None:
    for ext in WORKING_FORMATS + SUBMISSION_FORMATS:
        kwargs = dict(facecolor=SURFACE, bbox_inches="tight", pad_inches=0.06)
        if ext == "tif":
            # Flatten the alpha channel onto the surface and LZW-compress:
            # journal artwork systems reject RGBA/uncompressed TIFFs, and the
            # raw 600 dpi files run ~35 MB each. Matplotlib 3.11 writes the
            # alpha channel automatically once the figure surface has one.
            kwargs["dpi"] = TIF_DPI
            kwargs["pil_kwargs"] = dict(
                compression="tiff_lzw",
            )
        fig.savefig(out_stem.with_suffix(f".{ext}"), **kwargs)

    # Post-process the TIFFs (flatten RGBA -> RGB; matplotlib cannot do it
    # inline, so it is done here once per figure, after every format writes).
    if out_stem.with_suffix(".tif").exists():
        from PIL import Image

        # These TIFFs are our own artwork, not untrusted input, so PIL's
        # decompression-bomb guard is a false positive here -- a tall 600 dpi
        # figure legitimately exceeds the default ~179 Mpixel limit. Disable it
        # for this trusted, in-process read/write.
        prev_limit = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None
        try:
            tif = out_stem.with_suffix(".tif")
            im = Image.open(tif)
            if im.mode == "RGBA":
                flat = Image.new("RGB", im.size, SURFACE)
                flat.paste(im, mask=im.getchannel("A"))
                flat.save(tif, format="TIFF", compression="tiff_lzw", dpi=(TIF_DPI, TIF_DPI))
            im.close()
        finally:
            Image.MAX_IMAGE_PIXELS = prev_limit

    plt.close(fig)


def plot_player_leaderboard(df: pd.DataFrame, out_stem: Path, top_n: int = LEADERBOARD_TOP_N) -> None:
    d = df.copy()
    d["player_name"] = d["player_name"].fillna("unknown").astype(str)
    d = d.sort_values("cumulative_cRV", ascending=False)

    # A full-season pull has hundreds of challengers; a bar per player would be
    # an unreadable multi-hundred-inch canvas (and trips PIL's decompression-
    # bomb guard at 600 dpi). Show the top N by cumulative cRV -- the stem is
    # literally "leaderboard_top10", so this is what the figure always meant.
    total_players = len(d)
    shown = d.head(top_n)

    fig, ax = plt.subplots(figsize=(7.0, 0.42 * len(shown) + 1.35))
    _style_axes(ax, xgrid=True)
    fig.canvas.draw()

    _draw_signed_hbars(ax, list(shown["player_name"]), [float(v) for v in shown["cumulative_cRV"]])

    _set_title(ax, "Cumulative Challenge Run Value by player")
    xlabel = "Cumulative cRV (runs)"
    if total_players > len(shown):
        xlabel += f"    (top {len(shown)} of {total_players} challengers)"
    ax.set_xlabel(xlabel, fontsize=9, color=TEXT_SECONDARY, labelpad=8)
    _finish(fig, out_stem)


def plot_challenger_summary(df: pd.DataFrame, out_stem: Path) -> None:
    d = df.copy()
    d["challenger_type"] = d["challenger_type"].fillna("unknown").astype(str)
    d = d.sort_values("cumulative_cRV", ascending=False)

    fig, ax = plt.subplots(figsize=(6.2, 0.52 * len(d) + 1.4))
    _style_axes(ax, xgrid=True)
    fig.canvas.draw()

    _draw_signed_hbars(ax, list(d["challenger_type"]), [float(v) for v in d["cumulative_cRV"]])

    _set_title(ax, "Cumulative cRV by challenger role")
    ax.set_xlabel("Cumulative cRV (runs)", fontsize=9, color=TEXT_SECONDARY, labelpad=8)
    _finish(fig, out_stem)


def plot_challenge_wpa(df: pd.DataFrame, out_stem: Path) -> None:
    """Win-denominated challenger-role totals, the WPA twin of the cRV chart."""
    d = df.copy()
    d["challenger_type"] = d["challenger_type"].fillna("unknown").astype(str)
    d = d.sort_values("total_wpa", ascending=False)

    fig, ax = plt.subplots(figsize=(6.2, 0.52 * len(d) + 1.4))
    _style_axes(ax, xgrid=True)
    fig.canvas.draw()

    _draw_signed_hbars(ax, list(d["challenger_type"]), [float(v) for v in d["total_wpa"]])

    _set_title(ax, "Cumulative challenge win probability (cWPA) by role")
    ax.set_xlabel("Total cWPA (win probability)", fontsize=9, color=TEXT_SECONDARY, labelpad=8)
    _finish(fig, out_stem)


def plot_ev_sensitivity(df: pd.DataFrame, out_stem: Path) -> None:
    d = df.copy().sort_values("ev_c")
    x = [float(v) for v in d["ev_c"]]
    y = [float(v) for v in d["sum_cRV"]]

    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    _style_axes(ax, xgrid=False, ygrid=True)

    ax.plot(
        x,
        y,
        color=POSITIVE,
        linewidth=LINE_PX * PX,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=3,
    )
    # Markers carry a surface ring so they stay legible where they overlap.
    ax.plot(
        x,
        y,
        linestyle="none",
        marker="o",
        markersize=MARKER_PX * PX,
        markerfacecolor=POSITIVE,
        markeredgecolor=SURFACE,
        markeredgewidth=RING_PX * PX,
        zorder=4,
    )

    # Label selectively: the two endpoints, not every point.
    for idx, ha, dy in ((0, "left", 1), (len(x) - 1, "right", 1)):
        ax.annotate(
            f"{y[idx]:.2f}",
            xy=(x[idx], y[idx]),
            xytext=(0, 9 * dy),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=TEXT_SECONDARY,
            zorder=5,
        )

    _set_title(ax, "Total cRV is linear in the retained-challenge value $EV_c$")
    ax.set_xlabel("$EV_c$ (runs per retained challenge)", fontsize=9, color=TEXT_SECONDARY, labelpad=8)
    ax.set_ylabel("Total cRV (runs)", fontsize=9, color=TEXT_SECONDARY, labelpad=8)
    ax.margins(x=0.08, y=0.20)
    _finish(fig, out_stem)


def plot_pipeline_diagram(out_stem: Path) -> None:
    """Schematic of the five-module pipeline.

    This is a diagram, not a chart: the boxes encode no quantity, so they wear
    chrome tokens (hairline ring on surface), never categorical hues. Colored
    boxes here would imply five series that do not exist.
    """
    stages = [
        ("Ingestion", "ingestion.py"),
        ("Event isolation", "events.py"),
        ("Alternate realities", "realities.py"),
        ("RE288 mapping", "re288.py"),
        ("Scoring", "calculate.py"),
    ]

    fig, ax = plt.subplots(figsize=(7.9, 1.85))
    ax.set_facecolor(SURFACE)
    ax.set_xlim(0, len(stages))
    ax.set_ylim(0, 1)
    ax.axis("off")

    box_w, box_h = 0.9, 0.42
    y0 = 0.30
    for i, (name, module) in enumerate(stages):
        x0 = i + (1 - box_w) / 2
        ax.add_patch(
            FancyBboxPatch(
                (x0, y0),
                box_w,
                box_h,
                boxstyle="round,pad=0,rounding_size=0.06",
                facecolor=SURFACE,
                edgecolor=BASELINE,
                linewidth=1 * PX,
                zorder=3,
            )
        )
        ax.text(
            i + 0.5,
            y0 + box_h * 0.62,
            name,
            ha="center",
            va="center",
            fontsize=9,
            color=TEXT_PRIMARY,
            zorder=4,
        )
        ax.text(
            i + 0.5,
            y0 + box_h * 0.24,
            module,
            ha="center",
            va="center",
            fontsize=7.5,
            color=TEXT_MUTED,
            family="monospace",
            zorder=4,
        )
        if i < len(stages) - 1:
            ax.annotate(
                "",
                xy=(i + 1 + (1 - box_w) / 2, y0 + box_h / 2),
                xytext=(x0 + box_w, y0 + box_h / 2),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=TEXT_MUTED,
                    linewidth=1 * PX,
                    shrinkA=0,
                    shrinkB=0,
                ),
                zorder=2,
            )

    if EMBED_TITLES:
        ax.text(
            (1 - box_w) / 2,
            0.10,
            "Each stage writes an inspectable CSV, so any event traces from raw text to score.",
            ha="left",
            va="center",
            fontsize=8,
            color=TEXT_SECONDARY,
        )
    _finish(fig, out_stem)


# Figure order as cited in the manuscript. JQAS asks that figures be cited in
# numerical order and uploaded as separate files, so the submission bundle is
# named by number rather than by content.
FIGURE_ORDER = (
    ("pipeline_diagram", "Figure1"),
    ("leaderboard_top10", "Figure2"),
    ("challenger_totals", "Figure3"),
    ("ev_sensitivity", "Figure4"),
    ("challenge_wpa", "Figure5"),
)


def _stage_submission_figures(figures_dir: Path) -> list[str]:
    """Copy the EPS/TIF artwork into a flat, numbered submission bundle."""
    submission_dir = figures_dir / "submission"
    submission_dir.mkdir(parents=True, exist_ok=True)
    staged: list[str] = []

    for stem, number in FIGURE_ORDER:
        for ext in SUBMISSION_FORMATS:
            src = figures_dir / f"{stem}.{ext}"
            if not src.exists():
                continue
            dest = submission_dir / f"{number}.{ext}"
            shutil.copyfile(src, dest)
            staged.append(dest.name)
    return staged


def build_all_figures(output_dir: Path) -> list[str]:
    """Render every paper figure from the pipeline's CSV outputs."""
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FONT_STACK,
            "figure.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }
    )

    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    jobs = (
        ("player_leaderboard.csv", plot_player_leaderboard, "leaderboard_top10"),
        ("challenger_summary.csv", plot_challenger_summary, "challenger_totals"),
        ("ev_sensitivity.csv", plot_ev_sensitivity, "ev_sensitivity"),
        ("challenge_wpa_summary.csv", plot_challenge_wpa, "challenge_wpa"),
    )
    for filename, plot_fn, stem in jobs:
        src = output_dir / filename
        if not src.exists():
            continue
        df = pd.read_csv(src)
        if df.empty:
            continue
        plot_fn(df, figures_dir / stem)
        written.append(stem)

    plot_pipeline_diagram(figures_dir / "pipeline_diagram")
    written.append("pipeline_diagram")

    _stage_submission_figures(figures_dir)

    return written


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Render CRV paper figures.")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    written = build_all_figures(Path(args.output_dir))
    print(f"Rendered {len(written)} figures: {', '.join(written) if written else 'none'}")


if __name__ == "__main__":
    main()
