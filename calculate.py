"""cRV calculation engine (Module 5)

Provides calculate_crv(challenges_df) which computes Delta RV, penalty, and cRV.
"""
import pandas as pd

EV_C = 0.15  # baseline constant for V1 as specified in CRV Master.md


def calculate_crv(challenges_df: pd.DataFrame) -> pd.DataFrame:
    """Compute cRV per the specification.

    Steps implemented as placeholders:
      - Delta RV: RE_Challenge - RE_Reality (sign depends on challenger)
      - innings_remaining = max(0, 9 - inning)
      - Penalty applied only for failed challenges: -(innings_remaining / 9) * EV_C
      - cRV = Delta RV + Penalty

    Edge cases (inning-ending outs, base advances) must be handled by callers or via later refinements.
    """
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()

    # Delta RV depending on challenger_type
    def _delta(row):
        try:
            re_ch = float(row.get("RE_Challenge", 0))
            re_re = float(row.get("RE_Reality", 0))
        except Exception:
            return 0.0
        if row.get("challenger_type") == "batter":
            return re_ch - re_re
        elif row.get("challenger_type") == "catcher":
            return re_re - re_ch
        else:
            return 0.0

    df["delta_rv_pitch"] = df.apply(_delta, axis=1)

    # innings_remaining
    df["innings_remaining"] = df.get("inning", 0).apply(lambda x: max(0, 9 - int(x)) if pd.notnull(x) else 0)

    # Penalty only when challenge_success == False
    def _penalty(row):
        if row.get("challenge_success") in (False, 0):
            return - (row.get("innings_remaining", 0) / 9.0) * EV_C
        return 0.0

    df["penalty"] = df.apply(_penalty, axis=1)
    df["cRV"] = df["delta_rv_pitch"] + df["penalty"]

    return df
