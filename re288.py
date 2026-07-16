"""RE288 matrix handling and mapping (Module 4)."""
from __future__ import annotations

from typing import Optional

import pandas as pd


def load_re288_matrix(path: Optional[str] = None) -> pd.DataFrame:
    """Load RE288 lookup table or return a synthetic fallback matrix."""
    if path is not None:
        return pd.read_csv(path)

    rows = []
    for b1 in ("0", "1"):
        for b2 in ("0", "1"):
            for b3 in ("0", "1"):
                base_state = f"{b1}{b2}{b3}"
                runners = int(b1) + int(b2) + int(b3)
                for outs in (0, 1, 2):
                    base_component = 0.18 * runners
                    out_component = 0.32 * outs
                    for balls in range(4):
                        for strikes in range(3):
                            count_state = f"{balls}-{strikes}"
                            count_component = 0.04 * balls - 0.03 * strikes
                            expected_runs = max(0.0, round(0.56 + base_component - out_component + count_component, 3))
                            rows.append(
                                {
                                    "base_state": base_state,
                                    "outs": outs,
                                    "count_state": count_state,
                                    "expected_runs": expected_runs,
                                }
                            )
    return pd.DataFrame(rows)


def map_re288(challenges_df: pd.DataFrame, re288_matrix: pd.DataFrame) -> pd.DataFrame:
    """Map RE_Reality and RE_Challenge onto challenge events."""
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    if re288_matrix is None or re288_matrix.empty:
        df["RE_Reality"] = 0.0
        df["RE_Challenge"] = 0.0
        return df

    reality = re288_matrix.rename(
        columns={"count_state": "original_count_state", "expected_runs": "RE_Reality"}
    )
    df = df.merge(
        reality[["base_state", "outs", "original_count_state", "RE_Reality"]],
        on=["base_state", "outs", "original_count_state"],
        how="left",
    )

    challenge = re288_matrix.rename(
        columns={"count_state": "overturned_count_state", "expected_runs": "RE_Challenge"}
    )
    df = df.merge(
        challenge[["base_state", "outs", "overturned_count_state", "RE_Challenge"]],
        on=["base_state", "outs", "overturned_count_state"],
        how="left",
    )

    df["RE_Reality"] = pd.to_numeric(df["RE_Reality"], errors="coerce").fillna(0.0)
    df["RE_Challenge"] = pd.to_numeric(df["RE_Challenge"], errors="coerce").fillna(0.0)

    # Edge case: inning-ending strike-3/ball-4 states represented as terminal outcomes are fixed to 0.
    df.loc[df.get("original_terminal", False), "RE_Reality"] = 0.0
    df.loc[df.get("overturned_terminal", False), "RE_Challenge"] = 0.0

    return df
