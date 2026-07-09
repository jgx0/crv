"""RE288 matrix handling and mapping (Module 4)

Provides load_re288_matrix and map_re288 for merging RE values into challenge rows.
"""
from typing import Optional
import pandas as pd


def load_re288_matrix(path: Optional[str] = None) -> pd.DataFrame:
    """Load the RE288 lookup table.

    If path is None, returns an empty DataFrame placeholder. Expect CSV with columns:
      base_state, outs, count_state, expected_runs
    """
    if path is None:
        # placeholder empty matrix
        cols = ["base_state", "outs", "count_state", "expected_runs"]
        return pd.DataFrame(columns=cols)
    return pd.read_csv(path)


def map_re288(challenges_df: pd.DataFrame, re288_matrix: pd.DataFrame) -> pd.DataFrame:
    """Left-merge to populate RE_Reality and RE_Challenge columns.

    Assumes re288_matrix has keys: base_state, outs, count_state -> expected_runs
    """
    if challenges_df is None or challenges_df.empty:
        return pd.DataFrame()

    df = challenges_df.copy()
    if re288_matrix is None or re288_matrix.empty:
        df["RE_Reality"] = None
        df["RE_Challenge"] = None
        return df

    left_cols = ["base_state", "outs", "original_count_state"]
    right_cols = ["base_state", "outs", "count_state", "expected_runs"]

    reality = re288_matrix.rename(columns={"count_state": "original_count_state", "expected_runs": "RE_Reality"})
    df = df.merge(reality[["base_state", "outs", "original_count_state", "RE_Reality"]], on=["base_state", "outs", "original_count_state"], how="left")

    challenge = re288_matrix.rename(columns={"count_state": "overturned_count_state", "expected_runs": "RE_Challenge"})
    df = df.merge(challenge[["base_state", "outs", "overturned_count_state", "RE_Challenge"]], on=["base_state", "outs", "overturned_count_state"], how="left")

    return df
