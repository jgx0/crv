"""Validation/statistical summaries for CRV experiments."""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

try:
    from .calculate import EV_C
except ImportError:  # pragma: no cover
    from calculate import EV_C

# Bootstrap resampling seed. Fixed so the reported confidence intervals are
# reproducible: the paper cites the CI bounds in prose, and an unseeded RNG
# made the table disagree with the text on every re-run.
BOOTSTRAP_SEED = 20260810


def _bootstrap_mean_ci(
    values: pd.Series, n_boot: int = 1000, alpha: float = 0.05, seed: int = BOOTSTRAP_SEED
) -> tuple[float, float]:
    sample = pd.to_numeric(values, errors="coerce").dropna()
    if sample.empty:
        return 0.0, 0.0
    if len(sample) == 1:
        value = float(sample.iloc[0])
        return value, value

    rng = np.random.default_rng(seed)
    arr = sample.to_numpy(dtype=float)
    draws = rng.choice(arr, size=(n_boot, len(arr)), replace=True).mean(axis=1)
    lower = float(np.quantile(draws, alpha / 2))
    upper = float(np.quantile(draws, 1 - alpha / 2))
    return lower, upper


def build_validation_summary(scored_df: pd.DataFrame, n_boot: int = 1000) -> pd.DataFrame:
    """Compute basic validation metrics and uncertainty summaries."""
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(
            [
                {
                    "metric": "Total events",
                    "value": 0.0,
                    "ci_lower": 0.0,
                    "ci_upper": 0.0,
                    "notes": "No rows available",
                }
            ]
        )

    total_events = float(len(scored_df))
    success_rate = float(pd.to_numeric(scored_df["challenge_success"], errors="coerce").fillna(0).mean())
    mean_crv = float(pd.to_numeric(scored_df["cRV"], errors="coerce").fillna(0.0).mean())
    ci_low, ci_high = _bootstrap_mean_ci(scored_df["cRV"], n_boot=n_boot)

    return pd.DataFrame(
        [
            {"metric": "Total events", "value": total_events, "ci_lower": total_events, "ci_upper": total_events, "notes": "Count of challenge events"},
            {"metric": "Success rate", "value": success_rate, "ci_lower": 0.0, "ci_upper": 1.0, "notes": "Share of successful challenges"},
            {"metric": "Mean cRV", "value": mean_crv, "ci_lower": ci_low, "ci_upper": ci_high, "notes": "Bootstrap CI for mean cRV"},
        ]
    )


def build_leverage_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize cRV by inning-derived leverage buckets."""
    if scored_df is None or scored_df.empty:
        return pd.DataFrame(columns=["leverage_bucket", "events", "mean_cRV", "sum_cRV"])

    df = scored_df.copy()
    df["inning"] = pd.to_numeric(df.get("inning", 9), errors="coerce").fillna(9).astype(int)
    df["leverage_bucket"] = pd.cut(
        df["inning"],
        bins=[0, 3, 6, 9, 99],
        labels=["early(1-3)", "mid(4-6)", "late(7-9)", "extra(10+)"],
        include_lowest=True,
        right=True,
    )

    return (
        df.groupby("leverage_bucket", dropna=False)
        .agg(events=("cRV", "count"), mean_cRV=("cRV", "mean"), sum_cRV=("cRV", "sum"))
        .reset_index()
    )


def build_ev_sensitivity(base_scored_df: pd.DataFrame, ev_values: Iterable[float]) -> pd.DataFrame:
    """Recalculate aggregate cRV under a range of EV_c assumptions."""
    if base_scored_df is None or base_scored_df.empty:
        return pd.DataFrame(columns=["ev_c", "mean_cRV", "sum_cRV"])

    rows = []
    for ev in ev_values:
        modified = base_scored_df.copy()
        failed = modified.get("challenge_success") == False
        modified["penalty"] = 0.0
        modified.loc[failed, "penalty"] = -((modified.loc[failed, "innings_remaining"]) / 9.0) * float(ev)
        modified["cRV"] = modified["delta_rv_pitch"] + modified["penalty"]
        rows.append(
            {
                "ev_c": float(ev),
                "mean_cRV": float(modified["cRV"].mean()),
                "sum_cRV": float(modified["cRV"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("ev_c")


def default_ev_grid() -> list[float]:
    """Provide a compact default EV_c sensitivity grid."""
    return [round(v, 2) for v in [0.05, 0.10, EV_C, 0.20, 0.25, 0.30]]
