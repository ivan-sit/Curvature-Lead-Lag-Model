#!/usr/bin/env python3
"""Pull 30-min intraday TAQ for several REGIME-DIVERSE years -> one parquet per year.

Robustness across sample periods (285J rubric): join 2019 with a crash year (2008),
a calm year (2015), and COVID (2020), so the intraday H1/H2 results can be checked
across distinct regimes instead of a single 2019 snapshot. Resumable + checkpointed
(each year ~5 h), so an interrupted multi-day pull continues where it left off.

Usage:  python scripts/pull_taq_years.py 2008 2015 2020
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

from cllm.data import load_wrds_taq_intraday

# Same ~150 liquid large-caps as the 2019 pull (names absent in a given year simply
# return no rows and are dropped for that year — noted as a coverage caveat).
UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CSCO", "CRM", "ACN", "ADBE", "INTC",
    "AMD", "TXN", "QCOM", "IBM", "INTU", "AMAT", "MU", "ADI", "LRCX", "NXPI",
    "KLAC", "ADSK", "MCHP", "FTNT", "HPQ",
    "GOOGL", "META", "DIS", "NFLX", "CMCSA", "VZ", "T", "TMUS", "CHTR", "EA",
    "ATVI", "TTWO", "OMC",
    "AMZN", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "TGT", "GM",
    "F", "MAR", "ROST", "YUM", "DG", "ORLY", "AZO",
    "PG", "KO", "PEP", "WMT", "COST", "MDLZ", "CL", "MO", "PM", "KMB",
    "GIS", "KHC", "SYY", "STZ", "HSY",
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SPGI", "AXP", "SCHW",
    "USB", "PNC", "CB", "MMC", "CME", "ICE", "TFC", "COF",
    "JNJ", "UNH", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "MDT", "CVS", "GILD", "ISRG", "CI", "ZTS", "SYK", "BSX",
    "HON", "UPS", "BA", "CAT", "GE", "MMM", "DE", "LMT", "RTX", "UNP",
    "GD", "NOC", "EMR", "ETN", "CSX", "FDX", "NSC", "WM",
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI",
    "LIN", "APD", "SHW", "ECL", "FCX", "NEM", "DOW", "NUE",
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
    "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL",
]


def main() -> None:
    years = sys.argv[1:] or ["2008", "2015", "2020"]
    cal = pd.read_parquet("data/returns_wrds.parquet").index
    for yr in years:
        out = f"data/taq_intraday_{yr}.parquet"
        if Path(out).exists():
            have = set(pd.DatetimeIndex(pd.read_parquet(out).index).normalize().strftime("%Y-%m-%d"))
        else:
            have = set()
        days = [d.strftime("%Y-%m-%d") for d in cal if d.strftime("%Y") == yr]
        todo = [d for d in days if d not in have]
        print(f"\n=== {yr}: {len(days)} trading days, {len(have)} have, pulling {len(todo)} ===",
              flush=True)
        if not todo:
            print(f"{yr} complete"); continue
        t0 = time.time()
        new = load_wrds_taq_intraday(UNIVERSE, todo, bar_minutes=30,
                                     wrds_username="ivansit1214",
                                     checkpoint_path=f"data/taq_prices_{yr}.ckpt.parquet")
        if new.empty:
            print(f"{yr}: no data"); continue
        existing = pd.read_parquet(out) if Path(out).exists() else None
        rets = pd.concat([existing, new]).sort_index() if existing is not None else new
        rets = rets[~rets.index.duplicated(keep="last")]
        rets.to_parquet(out)
        print(f"SAVED {out} -> {rets.shape} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
