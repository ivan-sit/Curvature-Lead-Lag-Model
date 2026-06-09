#!/usr/bin/env python3
"""Pull 30-min intraday TAQ bars for a liquid universe over a window -> parquet.

Phase-2 input: intraday is where lead-lag is strongest. We pull a bounded set of
liquid large-caps over FULL-YEAR 2019 (pre-COVID, clean), 30-min bars aggregated
server-side per trading day, and save an intraday returns panel. The wider
universe (~150 names) + full year is the power upgrade: more names => triangle-
richer lead-lag graph + larger k; more days => tighter IC confidence intervals.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from cllm.data import load_wrds_taq_intraday

# ~150 liquid large-caps (TAQ sym_root tickers), spread across all 11 GICS sectors.
UNIVERSE = [
    # Information Technology
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CSCO", "CRM", "ACN", "ADBE", "INTC",
    "AMD", "TXN", "QCOM", "IBM", "INTU", "AMAT", "MU", "ADI", "LRCX", "NXPI",
    "KLAC", "ADSK", "MCHP", "FTNT", "HPQ",
    # Communication Services
    "GOOGL", "META", "DIS", "NFLX", "CMCSA", "VZ", "T", "TMUS", "CHTR", "EA",
    "ATVI", "TTWO", "OMC",
    # Consumer Discretionary
    "AMZN", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "TGT", "GM",
    "F", "MAR", "ROST", "YUM", "DG", "ORLY", "AZO",
    # Consumer Staples
    "PG", "KO", "PEP", "WMT", "COST", "MDLZ", "CL", "MO", "PM", "KMB",
    "GIS", "KHC", "SYY", "STZ", "HSY",
    # Financials
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SPGI", "AXP", "SCHW",
    "USB", "PNC", "CB", "MMC", "CME", "ICE", "TFC", "COF",
    # Health Care
    "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "MDT", "CVS", "GILD", "ISRG", "CI", "ZTS", "SYK", "BSX",
    # Industrials
    "HON", "UPS", "BA", "CAT", "GE", "MMM", "DE", "LMT", "RTX", "UNP",
    "GD", "NOC", "EMR", "ETN", "CSX", "FDX", "NSC", "WM",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI",
    # Materials
    "LIN", "APD", "SHW", "ECL", "FCX", "NEM", "DOW", "NUE",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
    # Real Estate
    "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL",
]


OUT = "data/taq_intraday_2019.parquet"


def main() -> None:
    t0 = time.time()
    start, end = "2019-01-01", "2019-12-31"
    # exact NYSE trading days from the CRSP calendar we already pulled
    cal = pd.read_parquet("data/returns_wrds.parquet").index
    days = [d.strftime("%Y-%m-%d") for d in cal if start <= d.strftime("%Y-%m-%d") <= end]

    # "complete the panel": skip days already in the existing returns file (the
    # first pull got Jan-Aug; the array_agg query failed on high-volume fall days,
    # now fixed with DISTINCT ON). We pull only the MISSING days and merge — each
    # day's intraday returns are self-contained (within-day pct_change), so
    # concatenating returns from two pulls is exact.
    have_days: set[str] = set()
    existing = None
    if Path(OUT).exists():
        existing = pd.read_parquet(OUT)
        have_days = set(pd.DatetimeIndex(existing.index).normalize().strftime("%Y-%m-%d"))
    missing = [d for d in days if d not in have_days]
    print(f"{len(UNIVERSE)} names; {len(days)} trading days; "
          f"{len(have_days)} already have, pulling {len(missing)} missing")
    if not missing:
        print("panel already complete"); return

    new = load_wrds_taq_intraday(UNIVERSE, missing, bar_minutes=30,
                                 wrds_username="ivansit1214",
                                 checkpoint_path="data/taq_prices_2019.ckpt.parquet")
    print(f"pulled {new.shape} new in {time.time() - t0:.0f}s")
    if new.empty and existing is None:
        print("no data pulled"); sys.exit(1)

    rets = pd.concat([existing, new]).sort_index() if existing is not None else new
    rets = rets[~rets.index.duplicated(keep="last")]
    rets.to_parquet(OUT)
    print(f"SAVED {OUT}  -> {rets.shape}, span {rets.index.min()} .. {rets.index.max()}")
    print(rets.iloc[:4, :5].to_string())


if __name__ == "__main__":
    main()
