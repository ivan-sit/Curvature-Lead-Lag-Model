#!/usr/bin/env python3
"""Run the pipeline on the survivorship-correct WRDS daily data (2000-2024).

Loads the parquet pulled by load_wrds_crsp (data/returns_wrds.parquet +
data/sectors_wrds.parquet). 1069 names over 24 years -> use sparse settings.
"""

from __future__ import annotations

import time

import pandas as pd

from cllm.data import DataBundle
from cllm.diagnostics import kill_switch_b
from cllm.pipeline import PipelineConfig, run_pipeline


def main() -> None:
    t0 = time.time()
    returns = pd.read_parquet("data/returns_wrds.parquet")
    sectors = pd.read_parquet("data/sectors_wrds.parquet")["gsector"]
    returns = returns.dropna(axis=1, how="all").fillna(0.0)
    # unmapped GICS -> "OTHER" so market+sector residualization runs; as str labels
    sectors = sectors.reindex(returns.columns).fillna("OTHER").astype(str)
    bundle = DataBundle(returns=returns, sectors=sectors)
    print(f"WRDS DATA: {returns.shape[0]} days x {returns.shape[1]} names, "
          f"{bundle.sectors.notna().sum()} GICS-mapped, {bundle.sectors.nunique()} sectors")

    print("\n=== KILL-SWITCH B (triangle density) — survivorship-correct data ===")
    for r in kill_switch_b(bundle.returns, sectors=bundle.sectors,
                           sparsify_thresholds=(0.95, 0.98, 0.99), triangle_mode="common"):
        print("  ", r)

    print("\n=== FULL PIPELINE (WRDS daily) ===")
    cfg = PipelineConfig(
        threshold=0.985, selection_k=25, null_iters=30,
        with_ollivier=False, max_coint_candidates=2000,
        compute_linegraph=False, seed=0,
    )
    res = run_pipeline(bundle, cfg)
    for n in res.notes:
        print("  -", n)
    print("\n-- kill-switch B (pipeline graph) --\n  ", res.triangle)
    g = res.gap
    print(f"\n-- curvature gap Δκ = {g['gap']:.3f}  intra={g['kappa_intra']:.2f} "
          f"inter={g['kappa_inter']:.2f} --")
    print("\n-- validation cascade --")
    for k, v in res.cascade.items():
        print(f"  {k}: {v}")
    print("\n-- OOS directional IC by method (PRIMARY) --")
    print(res.ic_by_method.round(4).to_string())
    print(f"\nDONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
