#!/usr/bin/env python3
"""Run the full pipeline end-to-end on synthetic data and print a report.

    python scripts/run_synthetic.py

This is the smoke test for the *entire* system: data -> residualize -> lead-lag
graph -> kill-switch B -> curvature -> L(G)/AFRC -> cascade -> OOS IC vs baselines,
plus the propose-test-reject agent loop. Swap ``load_synthetic`` for
``load_wrds_crsp`` / ``load_csv`` once real data is available.
"""

from __future__ import annotations

from cllm.agent import run_agent
from cllm.data import load_synthetic
from cllm.diagnostics import kill_switch_a
from cllm.pipeline import PipelineConfig, run_pipeline


def main() -> None:
    print("=" * 72)
    print("KILL-SWITCH A — synthetic directed-SBM recovery")
    print("=" * 72)
    a = kill_switch_a(block_sizes=(20, 20, 20), p_in=0.45, p_out=0.02, seed=0)
    print(a)

    print("\n" + "=" * 72)
    print("END-TO-END PIPELINE on synthetic factor+lead-lag returns")
    print("=" * 72)
    bundle = load_synthetic(n_assets=60, n_periods=2500, n_sectors=5,
                            n_lead_lag_pairs=12, lead_lag_strength=0.6, seed=0)
    print(f"data: {bundle.shape[0]} periods x {bundle.shape[1]} assets, "
          f"{bundle.sectors.nunique()} sectors")

    result = run_pipeline(bundle, PipelineConfig(threshold=0.90, selection_k=15))
    for note in result.notes:
        print(f"  - {note}")

    print("\n-- Kill-switch B (triangle density) --")
    print(f"  {result.triangle}")

    print("\n-- Curvature gap (Δκ) on GICS communities --")
    g = result.gap
    print(f"  Δκ={g['gap']:.3f}  (intra={g['kappa_intra']:.2f}, inter={g['kappa_inter']:.2f}, "
          f"n_intra={g['n_intra']}, n_inter={g['n_inter']})")

    print("\n-- Validation cascade --")
    for key, val in result.cascade.items():
        print(f"  {key}: {val}")

    print("\n-- Out-of-sample directional IC by method (primary metric) --")
    print(result.ic_by_method.round(4).to_string())

    print("\n" + "=" * 72)
    print("AGENT — propose / test / reject loop")
    print("=" * 72)
    run = run_agent(bundle)
    print(f"candidates: {run.n_total}  accepted: {len(run.accepted)}  rejected: {len(run.rejected)}")
    for entry in run.accepted + run.rejected:
        tag = "ACCEPT" if entry.accepted else "REJECT"
        cfg = entry.config
        why = "" if entry.accepted else "  reasons: " + "; ".join(entry.reasons)
        print(f"  [{tag}] col={cfg.curvature_column} thr={cfg.threshold} k={cfg.selection_k}{why}")


if __name__ == "__main__":
    main()
