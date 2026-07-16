"""Data ingestion utilities for CRV pipeline."""
from __future__ import annotations

from typing import Optional

import pandas as pd


def fetch_2026_statcast_data(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Fetch Statcast pitch-by-pitch data for 2026 using pybaseball.

    Returns an empty DataFrame when pybaseball/network access is unavailable.
    """
    try:
        import pybaseball as pb
    except Exception:
        return pd.DataFrame()

    if start_date is None:
        start_date = "2026-03-26"
    if end_date is None:
        end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    try:
        return pb.statcast(start_dt=start_date, end_dt=end_date)
    except Exception:
        return pd.DataFrame()
