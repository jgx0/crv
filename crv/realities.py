"""Generate alternate pitch realities (Module 3)

Provides generate_alternate_realities(challenges_df) which computes original and overturned count states.
"""
import pandas as pd


def _normalize_count_state(count_str: str) -> str:
    """Ensure count_state strings like '0-0' or '3-2' are normalized."""
    if not isinstance(count_str, str):
        return ""
    return count_str.strip()


def generate_alternate_realities(challenges_df: pd.DataFrame) -> pd.DataFrame:
    """For each challenge event, determine original_count_state and overturned_count_state.

    This function implements the ABS-only rule: challenges only affect ball/strike counts.
    The implementation here is a conservative placeholder; integrate full pitch logic later.
    """
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    # Expect a column 'count' or 'count_state' that looks like 'B-S' or '0-0'. Try common names.
    src_cols = [c for c in ("count_state", "count", "original_count_state") if c in df.columns]
    if not src_cols:
        # Nothing to base derivation on; return with placeholders
        df["original_count_state"] = None
        df["overturned_count_state"] = None
        return df

    src = src_cols[0]
    df["original_count_state"] = df[src].astype(str).apply(_normalize_count_state)

    # Naive overturned logic: if original is '0-0' and batter wins, overturned becomes '1-0'
    def _overturned(row):
        orig = row["original_count_state"]
        # simplistic rule: increment balls by 1 when overturned and challenger is batter
        try:
            b, s = orig.split("-")
            b_i = int(b); s_i = int(s)
        except Exception:
            return None
        if row.get("challenger_type") == "batter":
            return f"{min(3, b_i+1)}-{s_i}"
        elif row.get("challenger_type") == "catcher":
            # catcher overturn typically removes a ball -> becomes a strike (naive)
            return f"{b_i}-{min(2, s_i+1)}"
        else:
            return None

    df["overturned_count_state"] = df.apply(_overturned, axis=1)
    return df
