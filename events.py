"""Event isolation and challenge filtering (Module 2)

Provides filter_challenge_events(df) which extracts challenge events from raw statcast.
"""
from typing import List
import pandas as pd


CHALLENGE_KEYWORDS: List[str] = ["challenge", "overturned", "upheld", "abs"]


def filter_challenge_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame containing only rows that represent ABS/challenge events.

    Expected input: raw statcast DataFrame with a 'des' (description) column.

    Adds at least these columns (as placeholders):
      - challenger_type: 'batter'|'catcher'|None
      - challenge_success: bool or NaN

    Parsing rules are intentionally conservative; update regex parsing as needed.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    des_col = "des"
    if des_col not in df.columns:
        return pd.DataFrame()

    mask = df[des_col].str.contains("|".join(CHALLENGE_KEYWORDS), case=False, na=False)
    out = df.loc[mask].copy()

    # Basic success flag
    out["challenge_success"] = out[des_col].str.contains("overturned", case=False, na=False)

    # Heuristic for challenger type; refine with more patterns if needed
    out["challenger_type"] = out[des_col].apply(lambda s: ("batter" if "batter" in str(s).lower() else ("catcher" if "catcher" in str(s).lower() else None)))

    return out
