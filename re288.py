"""RE288 matrix handling and mapping (Module 4)."""
from __future__ import annotations

from typing import Optional

import pandas as pd


def _synthetic_re288_matrix() -> pd.DataFrame:
    """Create synthetic fallback RE288 values when empirical data is unavailable."""
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


def estimate_empirical_re288_matrix(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """Estimate RE288 directly from play-by-play by averaging remaining runs in each state."""
    if pbp_df is None or pbp_df.empty:
        return pd.DataFrame()
    required = {"game_pk", "inning", "inning_topbot", "balls", "strikes", "outs_when_up", "bat_score"}
    if not required.issubset(set(pbp_df.columns)):
        return pd.DataFrame()

    df = pbp_df.copy()
    df["balls"] = pd.to_numeric(df["balls"], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=3)
    df["strikes"] = pd.to_numeric(df["strikes"], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=2)
    df["outs"] = pd.to_numeric(df["outs_when_up"], errors="coerce").fillna(0).astype(int).clip(lower=0, upper=2)
    df["bat_score"] = pd.to_numeric(df["bat_score"], errors="coerce").fillna(0.0)
    if "post_bat_score" in df.columns:
        df["post_bat_score"] = pd.to_numeric(df["post_bat_score"], errors="coerce").fillna(df["bat_score"])
    else:
        df["post_bat_score"] = df["bat_score"]

    for base_col in ("on_1b", "on_2b", "on_3b"):
        if base_col not in df.columns:
            df[base_col] = None

    df["base_state"] = (
        df["on_1b"].notna().astype(int).astype(str)
        + df["on_2b"].notna().astype(int).astype(str)
        + df["on_3b"].notna().astype(int).astype(str)
    )
    df["count_state"] = df["balls"].astype(str) + "-" + df["strikes"].astype(str)

    group_cols = ["game_pk", "inning", "inning_topbot"]
    df["half_inning_final_score"] = df.groupby(group_cols)["post_bat_score"].transform("max")
    df["runs_remaining"] = (df["half_inning_final_score"] - df["bat_score"]).clip(lower=0.0)

    out = (
        df.groupby(["base_state", "outs", "count_state"], dropna=False)["runs_remaining"]
        .agg(expected_runs="mean", sample_size="count")
        .reset_index()
    )
    out["expected_runs"] = pd.to_numeric(out["expected_runs"], errors="coerce").fillna(0.0).round(3)
    out["sample_size"] = pd.to_numeric(out["sample_size"], errors="coerce").fillna(0).astype(int)
    return out


def load_re288_matrix(path: Optional[str] = None, pbp_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Load RE288 lookup table from CSV, estimate empirically, or use synthetic fallback."""
    if path is not None:
        return pd.read_csv(path)
    if pbp_df is not None and not pbp_df.empty:
        empirical = estimate_empirical_re288_matrix(pbp_df)
        if not empirical.empty:
            return empirical
    return _synthetic_re288_matrix()


def _lookup_re(
    matrix: pd.DataFrame,
    base_state: str,
    outs: int,
    count_state: str,
) -> float:
    """Look up expected runs for a single base-out-count state."""
    if outs >= 3:
        return 0.0
    match = matrix[
        (matrix["base_state"] == base_state)
        & (matrix["outs"] == outs)
        & (matrix["count_state"] == count_state)
    ]
    if match.empty:
        return 0.0
    return float(match.iloc[0]["expected_runs"])


def _state_run_value(
    matrix: pd.DataFrame,
    *,
    base_state: str,
    outs: int,
    count_state: str,
    inning_over: bool,
    runs_on_play: int,
) -> float:
    """Total value of a post-pitch state: immediate runs + remaining RE."""
    if inning_over or outs >= 3:
        return float(runs_on_play)
    return float(runs_on_play) + _lookup_re(matrix, base_state, outs, count_state)


def map_re288(challenges_df: pd.DataFrame, re288_matrix: pd.DataFrame) -> pd.DataFrame:
    """Map RE_Reality and RE_Challenge onto challenge events.

    Non-terminal count changes keep pre-pitch bases/outs and use the post-call count.
    Terminal walks use post-walk bases, same outs, 0-0 count, plus runs scored on the play.
    Terminal strikeouts use same bases, outs+1 (or 0 if inning ends), 0-0 count.
    """
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    if re288_matrix is None or re288_matrix.empty:
        df["RE_Reality"] = 0.0
        df["RE_Challenge"] = 0.0
        return df

    matrix = re288_matrix.copy()
    matrix["outs"] = pd.to_numeric(matrix["outs"], errors="coerce").fillna(0).astype(int)
    matrix["expected_runs"] = pd.to_numeric(matrix["expected_runs"], errors="coerce").fillna(0.0)

    # Ensure required post-state columns exist for older synthetic paths.
    for col, default in (
        ("original_base_state", "base_state"),
        ("overturned_base_state", "base_state"),
        ("original_outs", "outs"),
        ("overturned_outs", "outs"),
        ("original_runs_on_play", 0),
        ("overturned_runs_on_play", 0),
        ("original_inning_over", False),
        ("overturned_inning_over", False),
        ("original_terminal", False),
        ("overturned_terminal", False),
    ):
        if col not in df.columns:
            if isinstance(default, str) and default in df.columns:
                df[col] = df[default]
            else:
                df[col] = default

    re_reality = []
    re_challenge = []
    for _, row in df.iterrows():
        re_reality.append(
            _state_run_value(
                matrix,
                base_state=str(row.get("original_base_state", row.get("base_state", "000"))),
                outs=int(row.get("original_outs", row.get("outs", 0))),
                count_state=str(row.get("original_count_state", "0-0")),
                inning_over=bool(row.get("original_inning_over", False)),
                runs_on_play=int(row.get("original_runs_on_play", 0) or 0),
            )
        )
        re_challenge.append(
            _state_run_value(
                matrix,
                base_state=str(row.get("overturned_base_state", row.get("base_state", "000"))),
                outs=int(row.get("overturned_outs", row.get("outs", 0))),
                count_state=str(row.get("overturned_count_state", "0-0")),
                inning_over=bool(row.get("overturned_inning_over", False)),
                runs_on_play=int(row.get("overturned_runs_on_play", 0) or 0),
            )
        )

    df["RE_Reality"] = re_reality
    df["RE_Challenge"] = re_challenge
    return df
