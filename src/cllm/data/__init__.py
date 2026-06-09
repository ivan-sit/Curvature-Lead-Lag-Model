"""Data adapters: WRDS (real), CSV (professor-provided), and synthetic fallback.

All loaders return a uniform ``DataBundle(returns, sectors)`` so the rest of the
pipeline is source-agnostic. The whole pipeline runs on ``synthetic`` today;
``wrds`` activates once institutional access is granted.
"""

from .loaders import (
    DataBundle,
    assemble_wrds_csvs,
    load_crsp_matrix,
    load_csv,
    load_synthetic,
    load_wrds_crsp,
    load_wrds_taq_intraday,
)

__all__ = [
    "DataBundle",
    "load_synthetic",
    "load_csv",
    "load_crsp_matrix",
    "load_wrds_crsp",
    "load_wrds_taq_intraday",
    "assemble_wrds_csvs",
]
