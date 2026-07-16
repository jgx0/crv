"""Event isolation and challenge filtering (Module 2)."""
from __future__ import annotations

import re
from typing import List

import pandas as pd


CHALLENGE_KEYWORDS: List[str] = ["challenge", "overturned", "upheld", "abs"]
CHALLENGE_RE = re.compile(r"\bchallenge\b", re.IGNORECASE)
OUTCOME_RE = re.compile(r"\b(overturned|upheld|stands?)\b", re.IGNORECASE)
SUCCESS_RE = re.compile(r"\boverturned\b", re.IGNORECASE)
FAIL_RE = re.compile(r"\b(upheld|stands?)\b", re.IGNORECASE)
BATTER_RE = re.compile(r"\b(batter|hitter)\b", re.IGNORECASE)
CATCHER_RE = re.compile(r"\bcatcher\b", re.IGNORECASE)
BALL_RE = re.compile(r"\bcalled ball\b", re.IGNORECASE)
STRIKE_RE = re.compile(r"\bcalled strike\b", re.IGNORECASE)
TO_BALL_RE = re.compile(r"\bto (a )?ball\b", re.IGNORECASE)
TO_STRIKE_RE = re.compile(r"\bto (a )?strike\b", re.IGNORECASE)


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
    if TO_BALL_RE.search(description):
        return "called_strike"
    if TO_STRIKE_RE.search(description):
        return "called_ball"
    return None


def filter_challenge_events(df: pd.DataFrame) -> pd.DataFrame:
    """Extract ABS challenge events from raw Statcast data."""
    if df is None or df.empty or "des" not in df.columns:
        return pd.DataFrame()

    des_text = df["des"].astype(str)
    mask = des_text.apply(lambda s: bool(CHALLENGE_RE.search(s) and OUTCOME_RE.search(s)))
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
    if "outs" not in out.columns and "outs_when_up" in out.columns:
        out["outs"] = pd.to_numeric(out["outs_when_up"], errors="coerce").fillna(0).astype(int)
    elif "outs" in out.columns:
        out["outs"] = pd.to_numeric(out["outs"], errors="coerce").fillna(0).astype(int)

    out["parse_quality"] = "ok"
    out.loc[out["challenger_type"].isna(), "parse_quality"] = "missing_challenger"
    out.loc[out["called_pitch_type"].isna(), "parse_quality"] = "missing_called_pitch"

    return out
