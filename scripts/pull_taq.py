#!/usr/bin/env python3
"""Pull 30-min intraday TAQ bars for a liquid universe over a window -> parquet.

Phase-2 input: intraday is where lead-lag is strongest. We pull a bounded set of
liquid large-caps over H2-2019 (pre-COVID, clean), 30-min bars aggregated
server-side per trading day, and save an intraday returns panel.
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from cllm.data import load_wrds_taq_intraday

# ~50 liquid large-caps (TAQ sym_root tickers), spread across sectors.
UNIVERSE = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "JPM", "BAC", "WFC", "C",
    "GS", "MS", "XOM", "CVX", "COP", "SLB", "JNJ", "PFE", "MRK", "ABBV",
    "UNH", "LLY", "HD", "LOW", "MCD", "SBUX", "NKE", "DIS", "CMCSA", "VZ",
    "T", "KO", "PEP", "PG", "WMT", "COST", "CAT", "DE", "BA", "HON",
    "GE", "MMM", "UPS", "INTC", "CSCO", "ORCL", "IBM", "QCOM", "TXN", "CRM",
]


def main() -> None:
    t0 = time.time()
    start, end = "2019-07-01", "2019-12-31"
    # exact NYSE trading days from the CRSP calendar we already pulled
    cal = pd.read_parquet("data/returns_wrds.parquet").index
    days = [d.strftime("%Y-%m-%d") for d in cal if start <= d.strftime("%Y-%m-%d") <= end]
    print(f"pulling {len(UNIVERSE)} names x {len(days)} trading days ({start}..{end})")

    rets = load_wrds_taq_intraday(UNIVERSE, days, bar_minutes=30, wrds_username="ivansit1214")
    print(f"intraday returns panel: {rets.shape} in {time.time() - t0:.0f}s")
    if rets.empty:
        print("no data pulled"); sys.exit(1)
    rets.to_parquet("data/taq_intraday_2019H2.parquet")
    print("SAVED data/taq_intraday_2019H2.parquet")
    print(rets.iloc[:4, :5].to_string())


if __name__ == "__main__":
    main()
