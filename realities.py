"""Generate alternate pitch realities (Module 3)."""
from __future__ import annotations

from typing import Tuple

import pandas as pd


MAX_BALLS = 3
MAX_STRIKES = 2


def _format_count(balls: int, strikes: int) -> str:
    return f"{max(0, min(MAX_BALLS, int(balls)))}-{max(0, min(MAX_STRIKES, int(strikes)))}"


def _apply_call(balls: int, strikes: int, called_pitch_type: str | None) -> Tuple[int, int, bool]:
    if called_pitch_type == "called_strike":
        new_strikes = strikes + 1
        if new_strikes >= 3:
            return balls, MAX_STRIKES, True
        return balls, new_strikes, False
    if called_pitch_type == "called_ball":
        new_balls = balls + 1
        if new_balls >= 4:
            return MAX_BALLS, strikes, True
        return new_balls, strikes, False
    return balls, strikes, False


def _apply_overturn(balls: int, strikes: int, called_pitch_type: str | None) -> Tuple[int, int, bool]:
    # Overturning a called strike produces a ball; overturning a called ball produces a strike.
    if called_pitch_type == "called_strike":
        return _apply_call(balls, strikes, "called_ball")
    if called_pitch_type == "called_ball":
        return _apply_call(balls, strikes, "called_strike")
    return balls, strikes, False


def _derive_base_state(row: pd.Series) -> str:
    bases = []
    for col in ("on_1b", "on_2b", "on_3b"):
        value = row.get(col)
        bases.append("1" if pd.notnull(value) and value not in ("", 0) else "0")
    return "".join(bases)


def generate_alternate_realities(challenges_df: pd.DataFrame) -> pd.DataFrame:
    """Compute original and overturned count states from pre-pitch state and challenge outcome."""
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    df["balls"] = pd.to_numeric(df.get("balls", 0), errors="coerce").fillna(0).astype(int)
    df["strikes"] = pd.to_numeric(df.get("strikes", 0), errors="coerce").fillna(0).astype(int)

    if "base_state" not in df.columns:
        df["base_state"] = df.apply(_derive_base_state, axis=1)

    orig_count = []
    over_count = []
    orig_terminal = []
    over_terminal = []

    for _, row in df.iterrows():
        balls = int(row.get("balls", 0))
        strikes = int(row.get("strikes", 0))
        called_pitch_type = row.get("called_pitch_type")
        success = bool(row.get("challenge_success", False))

        ob, os, oterm = _apply_call(balls, strikes, called_pitch_type)
        rb, rs, rterm = _apply_overturn(balls, strikes, called_pitch_type)

        if success:
            overturned_state = _format_count(rb, rs)
            overturned_terminal = rterm
        else:
            overturned_state = _format_count(ob, os)
            overturned_terminal = oterm

        orig_count.append(_format_count(ob, os))
        over_count.append(overturned_state)
        orig_terminal.append(oterm)
        over_terminal.append(overturned_terminal)

    df["original_count_state"] = orig_count
    df["overturned_count_state"] = over_count
    df["original_terminal"] = orig_terminal
    df["overturned_terminal"] = over_terminal

    return df
