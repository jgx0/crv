"""cRV calculation engine (Module 5)."""
from __future__ import annotations

import pandas as pd

EV_C = 0.15


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
    failed = df.get("challenge_success") == False
    df["penalty"] = 0.0
    df.loc[failed, "penalty"] = -((df.loc[failed, "innings_remaining"]) / 9.0) * EV_C

    df["cRV"] = df["delta_rv_pitch"] + df["penalty"]
    return df
