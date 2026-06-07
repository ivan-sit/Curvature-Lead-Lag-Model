#!/usr/bin/env python3
"""Run the pipeline on the local CRSP matrix data (Cucuringu-group extract).

695 NYSE names, 2000-2020 daily close-to-close. Survivor-only balanced panel
(the WRDS point-in-time pull is the survivorship-correct upgrade). Tuned for the
large universe: sparser graph, Ollivier off (per-edge LPs are expensive at scale),
modest null iterations, capped cointegration candidates.
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from cllm.data import load_crsp_matrix
from cllm.diagnostics import kill_switch_b
from cllm.pipeline import PipelineConfig, run_pipeline

BASE = "/Users/ivansit/Desktop/Geopolitical-Alpha/US_CRSP_NYSE"
RETURNS = f"{BASE}/Matrix_Format_SubsetUniverse/pvCLCL_20000103_20201231.csv"
SP1500 = f"{BASE}/Sectors/Sectors_SP1500.csv"     # headerless: [etf, idx, ticker, sector]
SP500 = f"{BASE}/Sectors/Sectors_SP500_YahooNWikipedia.csv"


def main() -> None:
    t0 = time.time()
    bundle = load_crsp_matrix(RETURNS)  # returns only; build sectors below
    # SP1500 (broader coverage), then fall back to SP500 file, then OTHER
    s1500 = pd.read_csv(SP1500, header=None).set_index(2)[3]
    s500 = pd.read_csv(SP500).set_index("Ticker")["Sector_Wikipedia"]
    sec = s1500.reindex(bundle.returns.columns)
    sec = sec.fillna(s500.reindex(bundle.returns.columns))
    bundle.sectors = sec.fillna("OTHER")
    print(f"REAL DATA: {bundle.returns.shape[0]} days x {bundle.returns.shape[1]} stocks, "
          f"{bundle.sectors.nunique()} sectors, "
          f"{bundle.sectors.ne('OTHER').sum()} mapped")

    print("\n" + "=" * 72)
    print("KILL-SWITCH B (triangle density) on REAL data — the go/no-go for AFRC")
    print("=" * 72)
    # residualize-free quick scan across sparsification, both triangle conventions
    for mode in ("common", "cyclic"):
        print(f"\n-- triangle convention: {mode} --")
        for r in kill_switch_b(bundle.returns, sectors=bundle.sectors,
                               sparsify_thresholds=(0.90, 0.95, 0.98), triangle_mode=mode):
            print("  ", r)
    sys.stdout.flush()

    print("\n" + "=" * 72)
    print("FULL PIPELINE on REAL data")
    print("=" * 72)
    cfg = PipelineConfig(
        threshold=0.97, selection_k=20, null_iters=30,
        with_ollivier=False, max_coint_candidates=2000,
        compute_linegraph=False, seed=0,
    )
    res = run_pipeline(bundle, cfg)
    for n in res.notes:
        print("  -", n)
    print("\n-- kill-switch B (pipeline graph) --\n  ", res.triangle)
    g = res.gap
    print(f"\n-- curvature gap Δκ = {g['gap']:.3f}  intra={g['kappa_intra']:.2f} "
          f"inter={g['kappa_inter']:.2f}  (n_intra={g['n_intra']}, n_inter={g['n_inter']}) --")
    print("\n-- validation cascade --")
    for k, v in res.cascade.items():
        print(f"  {k}: {v}")
    print("\n-- OOS directional IC by method (PRIMARY metric) --")
    print(res.ic_by_method.round(4).to_string())
    print(f"\nDONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
