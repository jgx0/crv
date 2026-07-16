"""Event isolation and challenge filtering (Module 2)."""
from __future__ import annotations

import re
from typing import List

import pandas as pd


CHALLENGE_KEYWORDS: List[str] = ["challenge", "overturned", "upheld", "abs"]
SUCCESS_RE = re.compile(r"\boverturned\b", re.IGNORECASE)
FAIL_RE = re.compile(r"\b(upheld|stands?)\b", re.IGNORECASE)
BATTER_RE = re.compile(r"\bbatter\b", re.IGNORECASE)
CATCHER_RE = re.compile(r"\bcatcher\b", re.IGNORECASE)
BALL_RE = re.compile(r"\b(ball|called ball)\b", re.IGNORECASE)
STRIKE_RE = re.compile(r"\b(strike|called strike)\b", re.IGNORECASE)


def _infer_challenger_type(description: str) -> str | None:
    if BATTER_RE.search(description):
        return "batter"
    if CATCHER_RE.search(description):
        return "catcher"
    return None


def _infer_called_pitch_type(description: str) -> str | None:
    if STRIKE_RE.search(description):
        return "called_strike"
    if BALL_RE.search(description):
        return "called_ball"
    return None


def filter_challenge_events(df: pd.DataFrame) -> pd.DataFrame:
    """Extract ABS challenge events from raw Statcast data."""
    if df is None or df.empty or "des" not in df.columns:
        return pd.DataFrame()

    mask = df["des"].astype(str).str.contains("|".join(CHALLENGE_KEYWORDS), case=False, na=False)
    out = df.loc[mask].copy()
    if out.empty:
        return out

    des = out["des"].astype(str)
    out["challenge_success"] = des.apply(lambda s: bool(SUCCESS_RE.search(s)))
    out.loc[des.apply(lambda s: bool(FAIL_RE.search(s))), "challenge_success"] = False

    out["challenger_type"] = des.apply(_infer_challenger_type)
    out["called_pitch_type"] = des.apply(_infer_called_pitch_type)

    if "balls" in out.columns and "strikes" in out.columns:
        out["balls"] = pd.to_numeric(out["balls"], errors="coerce").fillna(0).astype(int)
        out["strikes"] = pd.to_numeric(out["strikes"], errors="coerce").fillna(0).astype(int)

    return out
