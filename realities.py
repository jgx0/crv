"""Generate alternate pitch realities (Module 3)."""
from __future__ import annotations

from typing import Tuple

import pandas as pd


MAX_BALLS = 3
MAX_STRIKES = 2


def _format_count(balls: int, strikes: int) -> str:
    return f"{max(0, min(MAX_BALLS, int(balls)))}-{max(0, min(MAX_STRIKES, int(strikes)))}"


def _parse_base_state(base_state: str) -> Tuple[bool, bool, bool]:
    s = (base_state or "000").ljust(3, "0")[:3]
    return s[0] == "1", s[1] == "1", s[2] == "1"


def _encode_base_state(on1: bool, on2: bool, on3: bool) -> str:
    return f"{int(on1)}{int(on2)}{int(on3)}"


def advance_bases_on_walk(base_state: str) -> Tuple[str, int]:
    """Force batter to first; only forced runners advance.

    Returns (new_base_state, runs_scored).
    """
    on1, on2, on3 = _parse_base_state(base_state)
    runs = 1 if (on1 and on2 and on3) else 0
    # Batter always takes 1B.
    new_on1 = True
    # Runner on 1B is always forced to 2B; otherwise 2B stays put.
    new_on2 = True if on1 else on2
    # Runner on 2B is forced to 3B only if 1B was occupied; else 3B stays put
    # (and scores if bases were loaded — handled via runs).
    if on1 and on2:
        new_on3 = True
    else:
        new_on3 = on3 and not runs
    return _encode_base_state(new_on1, new_on2, new_on3), runs


def _apply_call(
    balls: int,
    strikes: int,
    outs: int,
    base_state: str,
    called_pitch_type: str | None,
) -> dict:
    """Apply a called ball or strike from the pre-pitch state.

    Returns post-pitch count/base/outs plus flags for PA-ending outcomes.
    """
    result = {
        "balls": balls,
        "strikes": strikes,
        "outs": outs,
        "base_state": base_state,
        "count_state": _format_count(balls, strikes),
        "is_walk": False,
        "is_strikeout": False,
        "inning_over": False,
        "runs_on_play": 0,
        "terminal": False,
    }

    if called_pitch_type == "called_strike":
        new_strikes = strikes + 1
        if new_strikes >= 3:
            new_outs = outs + 1
            result.update(
                {
                    "balls": balls,
                    "strikes": MAX_STRIKES,
                    "outs": min(new_outs, 3),
                    "is_strikeout": True,
                    "terminal": True,
                    "inning_over": new_outs >= 3,
                    # Count resets conceptually for next PA; lookup uses 0-0.
                    "count_state": "0-0",
                }
            )
            if new_outs >= 3:
                result["base_state"] = "000"
            return result
        result.update(
            {
                "strikes": new_strikes,
                "count_state": _format_count(balls, new_strikes),
            }
        )
        return result

    if called_pitch_type == "called_ball":
        new_balls = balls + 1
        if new_balls >= 4:
            new_bases, runs = advance_bases_on_walk(base_state)
            result.update(
                {
                    "balls": MAX_BALLS,
                    "strikes": strikes,
                    "base_state": new_bases,
                    "is_walk": True,
                    "terminal": True,
                    "runs_on_play": runs,
                    "count_state": "0-0",
                }
            )
            return result
        result.update(
            {
                "balls": new_balls,
                "count_state": _format_count(new_balls, strikes),
            }
        )
        return result

    return result


def _apply_overturn(
    balls: int,
    strikes: int,
    outs: int,
    base_state: str,
    called_pitch_type: str | None,
) -> dict:
    # Overturning a called strike produces a ball; overturning a called ball produces a strike.
    if called_pitch_type == "called_strike":
        return _apply_call(balls, strikes, outs, base_state, "called_ball")
    if called_pitch_type == "called_ball":
        return _apply_call(balls, strikes, outs, base_state, "called_strike")
    return _apply_call(balls, strikes, outs, base_state, None)


def _derive_base_state(row: pd.Series) -> str:
    bases = []
    for col in ("on_1b", "on_2b", "on_3b"):
        value = row.get(col)
        bases.append("1" if pd.notnull(value) and value not in ("", 0) else "0")
    return "".join(bases)


def generate_alternate_realities(challenges_df: pd.DataFrame) -> pd.DataFrame:
    """Compute original and overturned post-pitch states from pre-pitch state."""
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    df["balls"] = pd.to_numeric(df.get("balls", 0), errors="coerce").fillna(0).astype(int)
    df["strikes"] = pd.to_numeric(df.get("strikes", 0), errors="coerce").fillna(0).astype(int)
    df["outs"] = pd.to_numeric(df.get("outs", 0), errors="coerce").fillna(0).astype(int).clip(0, 2)

    if "base_state" not in df.columns:
        df["base_state"] = df.apply(_derive_base_state, axis=1)

    # Pre-pitch anchors retained for RE288 joins on non-terminal paths.
    df["pre_pitch_base_state"] = df["base_state"]
    df["pre_pitch_outs"] = df["outs"]

    orig_count = []
    over_count = []
    orig_terminal = []
    over_terminal = []
    orig_base = []
    over_base = []
    orig_outs = []
    over_outs = []
    orig_runs = []
    over_runs = []
    orig_inning_over = []
    over_inning_over = []

    for _, row in df.iterrows():
        balls = int(row.get("balls", 0))
        strikes = int(row.get("strikes", 0))
        outs = int(row.get("outs", 0))
        base_state = str(row.get("base_state", "000"))
        called_pitch_type = row.get("called_pitch_type")
        success = bool(row.get("challenge_success", False))

        original = _apply_call(balls, strikes, outs, base_state, called_pitch_type)
        overturned = _apply_overturn(balls, strikes, outs, base_state, called_pitch_type)

        # If challenge fails, the "challenge reality" is the same as original.
        if not success:
            overturned = dict(original)

        orig_count.append(original["count_state"])
        over_count.append(overturned["count_state"])
        orig_terminal.append(bool(original["terminal"]))
        over_terminal.append(bool(overturned["terminal"]))
        orig_base.append(original["base_state"])
        over_base.append(overturned["base_state"])
        orig_outs.append(int(original["outs"]))
        over_outs.append(int(overturned["outs"]))
        orig_runs.append(int(original["runs_on_play"]))
        over_runs.append(int(overturned["runs_on_play"]))
        orig_inning_over.append(bool(original["inning_over"]))
        over_inning_over.append(bool(overturned["inning_over"]))

    df["original_count_state"] = orig_count
    df["overturned_count_state"] = over_count
    df["original_terminal"] = orig_terminal
    df["overturned_terminal"] = over_terminal
    df["original_base_state"] = orig_base
    df["overturned_base_state"] = over_base
    df["original_outs"] = orig_outs
    df["overturned_outs"] = over_outs
    df["original_runs_on_play"] = orig_runs
    df["overturned_runs_on_play"] = over_runs
    df["original_inning_over"] = orig_inning_over
    df["overturned_inning_over"] = over_inning_over

    return df
