"""cRV calculation engine (Module 5)."""
from __future__ import annotations

import pandas as pd

EV_C = 0.15

# Each team holds two challenges per game under the 2026 ABS rules: a failed
# challenge is consumed, a successful one is retained. The data confirm this --
# no team fails more than twice in a single game.
CHALLENGE_BUDGET = 2


def challenger_team(df: pd.DataFrame) -> pd.Series:
    """Attribute each challenge to the team that issued it (home/away).

    A batter challenge is made on behalf of the batting team; a catcher
    challenge on behalf of the fielding team. ``inning_topbot`` says which side
    is batting. Rows whose role was not parsed return NaN. Mirrors
    ``_challenger_side`` in analysis.py.
    """
    home = df["home_team"].astype(str)
    away = df["away_team"].astype(str)
    batting_is_home = df["inning_topbot"].astype(str).str.upper().str.strip().eq("BOT")
    role = df["challenger_type"].astype(str).str.lower()
    is_batter = role.eq("batter")
    is_catcher = role.eq("catcher")
    known = is_batter | is_catcher
    challenger_is_home = (is_batter & batting_is_home) | (is_catcher & ~batting_is_home)
    return home.where(challenger_is_home, away).where(known)


def _penalty_weight(df: pd.DataFrame) -> pd.Series:
    """Opportunity-cost weight (1/C) for a failed challenge.

    A failure destroys exactly one challenge, but the value destroyed depends
    on how many the team held just before it: losing the *last* challenge
    forfeits the full retained option value, while losing one of two forfeits
    only a share (a reserve challenge remains). We model that lost value as a
    ``1/C`` share of ``EV_c``, where ``C`` is the number of challenges held
    before the failure.

    Falls back to a flat weight of 1.0 when the team/game columns required for
    attribution are absent (the offline synthetic corpus), preserving the
    pre-scarcity behavior.
    """
    required = {
        "home_team",
        "away_team",
        "inning_topbot",
        "challenger_type",
        "game_pk",
        "challenge_success",
    }
    if not required.issubset(set(df.columns)):
        return pd.Series(1.0, index=df.index)

    work = df.copy()
    work["_team"] = challenger_team(work)
    for col in ("inning", "at_bat_number", "pitch_number"):
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
        else:
            work[col] = 0
    work = work.sort_values(["game_pk", "inning", "at_bat_number", "pitch_number"])

    failed = pd.to_numeric(work["challenge_success"], errors="coerce").fillna(0).astype(bool)
    work["_fail"] = (~failed).astype(int)
    # Failures *before* this event, in within-game order, for the issuing team.
    work["_prior_failures"] = work.groupby(["game_pk", "_team"], dropna=False)["_fail"].transform(
        lambda s: s.shift(fill_value=0).cumsum()
    )
    remaining_before = (CHALLENGE_BUDGET - work["_prior_failures"]).clip(lower=1)
    weight = (1.0 / remaining_before).fillna(1.0)
    # Re-align to the caller's row order.
    return weight.reindex(df.index)


def calculate_crv(challenges_df: pd.DataFrame) -> pd.DataFrame:
    """Compute cRV with opportunity-cost penalty on failed challenges only."""
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    df["RE_Reality"] = pd.to_numeric(df.get("RE_Reality", 0.0), errors="coerce").fillna(0.0)
    df["RE_Challenge"] = pd.to_numeric(df.get("RE_Challenge", 0.0), errors="coerce").fillna(0.0)
    df["inning"] = pd.to_numeric(df.get("inning", 9), errors="coerce").fillna(9).astype(int)

    df["delta_rv_pitch"] = 0.0

    batter_success = (df.get("challenger_type") == "batter") & (df.get("challenge_success") == True)
    catcher_success = (df.get("challenger_type") == "catcher") & (df.get("challenge_success") == True)

    df.loc[batter_success, "delta_rv_pitch"] = df.loc[batter_success, "RE_Challenge"] - df.loc[batter_success, "RE_Reality"]
    df.loc[catcher_success, "delta_rv_pitch"] = df.loc[catcher_success, "RE_Reality"] - df.loc[catcher_success, "RE_Challenge"]

    df["innings_remaining"] = (9 - df["inning"]).clip(lower=0)
    df["penalty_weight"] = _penalty_weight(df)
    failed = df.get("challenge_success") == False
    df["penalty"] = 0.0
    df.loc[failed, "penalty"] = (
        -((df.loc[failed, "innings_remaining"]) / 9.0)
        * EV_C
        * df.loc[failed, "penalty_weight"]
    )

    df["cRV"] = df["delta_rv_pitch"] + df["penalty"]
    return df
