#!/usr/bin/env python3
"""Run the pipeline on intraday TAQ 30-min returns (Phase-2: where lead-lag lives).

Loads data/taq_intraday_2019H2.parquet (bar timestamps x tickers), maps tickers to
GICS sectors, and runs the full pipeline with intraday lags (in 30-min bars).

Caveat: lead-lag cross-correlation is computed on the concatenated intraday series;
overnight bars are already dropped by the loader, so the only residual leakage is
the day-boundary lag-1 pairing (minor). A within-day estimator is a refinement.
"""

from __future__ import annotations

import time

import pandas as pd

from cllm.data import DataBundle
from cllm.diagnostics import kill_switch_b
from cllm.pipeline import PipelineConfig, run_pipeline

BASE = "/Users/ivansit/Desktop/Geopolitical-Alpha/US_CRSP_NYSE"


def _sector_map() -> pd.Series:
    s1500 = pd.read_csv(f"{BASE}/Sectors/Sectors_SP1500.csv", header=None).set_index(2)[3]
    s500 = pd.read_csv(f"{BASE}/Sectors/Sectors_SP500_YahooNWikipedia.csv").set_index("Ticker")["Sector_Wikipedia"]
    return s1500.combine_first(s500)


def main() -> None:
    t0 = time.time()
    rets = pd.read_parquet("data/taq_intraday_2019H2.parquet")
    rets = rets.dropna(axis=1, how="all").fillna(0.0)
    sectors = _sector_map().reindex(rets.columns).fillna("OTHER").astype(str)
    bundle = DataBundle(returns=rets, sectors=sectors)
    print(f"INTRADAY: {rets.shape[0]} bars x {rets.shape[1]} names, "
          f"{(sectors != 'OTHER').sum()} sector-mapped")

    print("\n=== KILL-SWITCH B (intraday lead-lag graph) ===")
    for r in kill_switch_b(bundle.returns, sectors=bundle.sectors, lags=(1, 2, 3),
                           sparsify_thresholds=(0.80, 0.90, 0.95), triangle_mode="common"):
        print("  ", r)

    print("\n=== FULL PIPELINE (intraday) ===")
    cfg = PipelineConfig(
        lags=(1, 2, 3), threshold=0.88, selection_k=10, null_iters=100,
        with_ollivier=True, compute_linegraph=True, seed=0,
    )
    res = run_pipeline(bundle, cfg)
    for n in res.notes:
        print("  -", n)
    print("\n-- kill-switch B (pipeline graph) --\n  ", res.triangle)
    g = res.gap
    print(f"\n-- curvature gap Δκ = {g['gap']:.3f}  intra={g['kappa_intra']:.2f} inter={g['kappa_inter']:.2f} --")
    print("\n-- validation cascade --")
    for k, v in res.cascade.items():
        print(f"  {k}: {v}")
    print("\n-- OOS directional IC by method (PRIMARY) --")
    print(res.ic_by_method.round(4).to_string())
    print(f"\nDONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
