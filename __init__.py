"""crv package

Exports core pipeline functions as described in CRV Master.md
"""
from .ingestion import fetch_2026_statcast_data
from .events import filter_challenge_events
from .realities import generate_alternate_realities
from .re288 import load_re288_matrix, map_re288
from .calculate import calculate_crv

__all__ = [
    "fetch_2026_statcast_data",
    "filter_challenge_events",
    "generate_alternate_realities",
    "load_re288_matrix",
    "map_re288",
    "calculate_crv",
]
