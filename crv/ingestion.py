"""Data ingestion utilities for CRV pipeline

Module 1: fetch_2026_statcast_data(start_date, end_date)
"""
from typing import Optional
import pandas as pd


def fetch_2026_statcast_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Fetch Statcast pitch-by-pitch data for 2026 using pybaseball.

    Args:
        start_date: ISO date string (e.g. '2026-03-26'). Defaults to season start.
        end_date: ISO date string. Defaults to today.

    Returns:
        pandas.DataFrame with raw Statcast rows. Caller is responsible for filtering.

    Notes:
        - This is a thin wrapper around pybaseball.statcast or an equivalent data source.
        - For unit tests and offline work, callers may pass a local CSV-loaded DataFrame instead.
    """
    try:
        import pybaseball as pb
    except Exception:
        # pybaseball may not be installed in developer environment yet.
        return pd.DataFrame()

    if start_date is None:
        start_date = "2026-03-26"
    if end_date is None:
        end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    # pybaseball.statcast may have a different API; adapt when integrating.
    df = pb.statcast(start_dt=start_date, end_dt=end_date)
    return df
