"""Event isolation and challenge filtering (Module 2).

The parser targets the real Statcast ``des`` grammar for ABS challenges, which
takes the form::

    <challenger> challenged (pitch result), call on the field was <verdict>: <outcome>

Two properties of that record drive the whole module and are easy to get wrong:

1. ``description`` and ``events`` hold the call **as it stands after** the
   challenge is resolved, not the umpire's original call. The original call is
   therefore the inverse of ``description`` when the verdict is ``overturned``,
   and equal to it when the verdict is ``confirmed``/``upheld``.

2. Only pitch-result challenges are ABS challenges. Statcast uses the same
   "challenged (...)" grammar for replay review of tag plays, force plays, hit
   by pitch, and so on; those are not ABS events and must not be scored.

Verified against 2026 Statcast (July, 109,421 pitches / 528 challenge rows):
402 pitch-result challenges, verdicts confirmed/overturned, and every
pitch-result challenger is a named player -- never a team, unlike replay review.
"""
from __future__ import annotations

import re
from typing import List

import pandas as pd


# Only (pitch result) is an ABS challenge; the other parentheticals seen in the
# 2026 data -- play at 1st, tag play, force play, hit by pitch, home-plate
# collision, catcher interference, catch or drop, tag-up play -- are replay
# review and carry no ball/strike semantics.
ABS_CHALLENGE_RE = re.compile(r"challenged\s*\(pitch result\)", re.IGNORECASE)
# Non-capturing twin of VERDICT_RE, for boolean masking. `str.contains` with a
# capture group emits a UserWarning.
HAS_VERDICT_RE = re.compile(r"call on the field was \w+", re.IGNORECASE)
VERDICT_RE = re.compile(r"call on the field was (\w+)", re.IGNORECASE)
CHALLENGER_RE = re.compile(r"^(.*?)\s+challenged\s*\(", re.IGNORECASE)
# The outcome clause names the batter: "...was overturned: Cal Raleigh walks."
# The terminating alternatives are matched before the bare "." so that a
# suffixed name ("Vladimir Guerrero Jr.", "A.J. Ewing") is captured whole --
# stopping at the first period truncates it and misreads the batter as the
# catcher.
OUTCOME_PLAYER_RE = re.compile(
    r"call on the field was \w+:\s*(.+?)(?:\s+called out on strikes|\s+walks|\s*$)",
    re.IGNORECASE,
)

# "overturned" means the challenger won. "confirmed" and "upheld" both mean the
# original call stood, i.e. the challenger lost.
SUCCESS_VERDICTS = {"overturned"}
FAILURE_VERDICTS = {"confirmed", "upheld", "stands"}

# Retained for backward compatibility with earlier callers/tests.
CHALLENGE_KEYWORDS: List[str] = ["challenge", "overturned", "upheld", "confirmed"]

# Statcast's post-resolution pitch call -> the call it was flipped from.
_INVERSE_CALL = {"called_strike": "called_ball", "ball": "called_strike"}
# Statcast spells a ball "ball"; the rest of the pipeline says "called_ball".
_NORMALIZE_CALL = {"ball": "called_ball", "called_strike": "called_strike"}


def _text(series: pd.Series) -> pd.Series:
    """Null-safe string view.

    ``.astype(str)`` on an Arrow-backed column renders missing values as the
    float ``nan``, which then blows up any regex applied to it.
    """
    return series.astype("string").fillna("")


def _infer_challenger_type(des: str, challenger: str) -> str | None:
    """Batter or catcher, decided by whether the challenger is the batter.

    The batter is named in the outcome clause. A pitch-result challenge is
    always initiated by a player, so anyone who is not the batter is the
    catcher -- there is no third party with the right to challenge a pitch.
    """
    if not challenger:
        return None
    match = OUTCOME_PLAYER_RE.search(des)
    if not match:
        return None
    return "batter" if challenger.strip() == match.group(1).strip() else "catcher"


def filter_challenge_events(df: pd.DataFrame) -> pd.DataFrame:
    """Extract ABS challenge events from raw Statcast data."""
    if df is None or df.empty or "des" not in df.columns:
        return pd.DataFrame()

    des_text = _text(df["des"])
    # Match on the challenge clause alone. A row whose verdict clause is missing
    # is still a challenge that was spent, so it is kept and flagged below
    # rather than dropped -- dropping it would silently shrink the denominator.
    mask = des_text.str.contains(ABS_CHALLENGE_RE, na=False)
    out = df.loc[mask].copy().reset_index(drop=True)
    if out.empty:
        return out

    des = _text(out["des"])

    verdict = des.str.extract(VERDICT_RE, expand=False).str.lower()
    out["verdict"] = verdict
    out["challenge_success"] = verdict.isin(SUCCESS_VERDICTS)

    challenger = des.str.extract(CHALLENGER_RE, expand=False).fillna("")
    out["challenger_name"] = challenger
    out["challenger_type"] = [
        _infer_challenger_type(d, c) for d, c in zip(des, challenger)
    ]

    # `description` is the post-resolution call, so recover the umpire's
    # original call by inverting it exactly when the challenge succeeded.
    final_call = _text(out["description"]) if "description" in out.columns else pd.Series([""] * len(out))
    original = []
    for call, ok in zip(final_call, out["challenge_success"]):
        call = str(call)
        if ok:
            original.append(_INVERSE_CALL.get(call))
        else:
            original.append(_NORMALIZE_CALL.get(call))
    out["called_pitch_type"] = original
    out["final_pitch_call"] = [_NORMALIZE_CALL.get(str(c)) for c in final_call]

    if "balls" in out.columns and "strikes" in out.columns:
        out["balls"] = pd.to_numeric(out["balls"], errors="coerce").fillna(0).astype(int)
        out["strikes"] = pd.to_numeric(out["strikes"], errors="coerce").fillna(0).astype(int)
    if "outs" not in out.columns and "outs_when_up" in out.columns:
        out["outs"] = pd.to_numeric(out["outs_when_up"], errors="coerce").fillna(0).astype(int)
    elif "outs" in out.columns:
        out["outs"] = pd.to_numeric(out["outs"], errors="coerce").fillna(0).astype(int)

    # `player_name` is the pitcher in Statcast; the paper reports the party who
    # spent the challenge, so surface that as the identity column.
    out["player_name"] = out["challenger_name"].replace("", pd.NA)

    out["parse_quality"] = "ok"
    out.loc[out["verdict"].isna(), "parse_quality"] = "missing_verdict"
    out.loc[out["challenger_type"].isna(), "parse_quality"] = "missing_challenger"
    out.loc[out["called_pitch_type"].isna(), "parse_quality"] = "missing_called_pitch"

    return out
