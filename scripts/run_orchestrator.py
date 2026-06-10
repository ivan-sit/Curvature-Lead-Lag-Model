#!/usr/bin/env python3
"""Run the agentic propose -> test -> reject orchestrator and log every decision.

Demonstrates CLAUDE.md §6 Agent 6: a proposer sweeps the residualization ladder ×
threshold × triangle-convention × curvature object; an adversarial validator runs
the structural cascade and accepts/rejects each, logging reasons. A correct loop
rejects plain Forman (degree baseline) and accepts the weighted-augmented object.

Runs on the intraday 2019 panel if present, else synthetic.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from cllm.data import DataBundle, load_synthetic
from cllm.orchestrator import AcceptRules, Orchestrator


def _bundle() -> tuple[DataBundle, str]:
    p = Path("data/taq_intraday_2019.parquet")
    if p.exists():
        rets = pd.read_parquet(p).dropna(axis=1, how="all").fillna(0.0)
        sec = pd.read_parquet("data/ticker_sectors_wrds.parquet")["gsector"].astype(str)
        sec = sec.reindex(rets.columns).fillna("OTHER")
        return DataBundle(returns=rets.reset_index(drop=True), sectors=sec), "intraday 2019"
    d = load_synthetic(n_assets=40, n_periods=1500, n_lead_lag_pairs=6, seed=0)
    return d, "synthetic"


def main() -> None:
    bundle, src = _bundle()
    print(f"orchestrator on {src}: {bundle.returns.shape}")
    orch = Orchestrator(rules=AcceptRules(), lags=(1, 2, 3), selection_k=20, null_iters=0, seed=0)
    result = orch.run(bundle)
    print(f"\nproposed {result['n_candidates']} · accepted {result['n_accepted']} · "
          f"rejected {result['n_rejected']}\n")
    for d in result["decisions"]:
        v = "ACCEPT" if d.accepted else "reject"
        m = d.metrics
        print(f"  [{v}] {d.config['residualize']:13} thr={d.config['threshold']} "
              f"{d.config['curvature']:11} "
              f"spear={m.get('spearman', float('nan')):.2f} jacc={m.get('jaccard', float('nan')):.2f} "
              f"R2deg={m.get('r2_on_degree', float('nan')):.2f}"
              + ("" if d.accepted else f"  <- {'; '.join(d.reasons)}"))

    Path("logs").mkdir(exist_ok=True)
    out = Path("logs/orchestrator_findings.md")
    out.write_text(orch.findings_markdown(result))
    print(f"\nlog -> {out}")


if __name__ == "__main__":
    main()
