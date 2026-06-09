#!/usr/bin/env python3
"""Run the pipeline on intraday TAQ 30-min returns (Phase-2: where lead-lag lives).

Loads data/taq_intraday_2019.parquet (bar timestamps x tickers), maps tickers to
GICS sectors, and runs the full pipeline with intraday lags (in 30-min bars).

Power upgrade vs. the H2-only first cut: ~150 names (triangle-richer graph, larger
k) over full-year 2019 (tighter IC CIs), and a **within-day lead-lag estimator**
(cfg.within_day=True) so lag pairs never straddle an overnight gap — the last
source of day-boundary leakage is now removed.
"""

from __future__ import annotations

import time

import pandas as pd

from cllm.data import DataBundle
from cllm.diagnostics import kill_switch_b
from cllm.pipeline import PipelineConfig, run_pipeline


def _sector_map() -> pd.Series:
    # 100% Wharton: ticker -> GICS sector from Compustat (data/ticker_sectors_wrds.parquet)
    return pd.read_parquet("data/ticker_sectors_wrds.parquet")["gsector"].astype(str)


def main() -> None:
    t0 = time.time()
    rets = pd.read_parquet("data/taq_intraday_2019.parquet")
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
        lags=(1, 2, 3), threshold=0.90, selection_k=20, null_iters=100,
        with_ollivier=True, compute_linegraph=False, within_day=True,
        afrc_max_removals=300, seed=0,
    )
    res = run_pipeline(bundle, cfg)
    for n in res.notes:
        print("  -", n)
    print("\n-- kill-switch B (pipeline graph) --\n  ", res.triangle)
    g = res.gap
    print(f"\n-- curvature gap Δκ (GICS) = {g['gap']:.3f}  intra={g['kappa_intra']:.2f} inter={g['kappa_inter']:.2f} --")
    gd = res.gap_datadriven
    print(f"-- curvature gap Δκ (data-driven) = {gd['gap']:.3f}  "
          f"intra={gd['kappa_intra']:.2f} inter={gd['kappa_inter']:.2f} --")
    print("\n-- validation cascade --")
    for k, v in res.cascade.items():
        print(f"  {k}: {v}")
    print("\n-- OOS directional IC by method (PRIMARY) --")
    print(res.ic_by_method.round(4).to_string())
    print(f"\nDONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
