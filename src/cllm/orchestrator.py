r"""Agentic propose -> test -> reject orchestrator (CLAUDE.md §6 Agent 6).

This is the course's "agentic" layer, built to the pattern the 285J lectures call
for (Lec 17 *Auto Quant Research*: a **two-layer** system; Lec 1-3 / Lec 23: an
**adversarial validator** because proposals are uncertified — "test, don't trust"):

* **Decision layer** (human-set goals): the candidate grid and the accept/reject
  rules (:class:`AcceptRules`). These encode *what counts as a real structural
  signal* and are the load-bearing scientific choices.
* **Execution layer** (autonomous): for every proposed candidate signal, build the
  residualized lead-lag graph, compute its curvature, run the structural cascade,
  and **accept or reject** it against the rules — logging every decision with
  reasons. No proposal is trusted until the deterministic cascade validates it.

The proposal grid sweeps the **residualization method** (market / market+sector /
PCA — the residualization *ladder* the lectures recommend as a robustness axis),
the sparsification threshold, the triangle convention, and the curvature object.
A correctly-working loop should *reject* plain Forman (a pure degree baseline:
R² on degree ≈ 1, no higher-order signal) and *accept* the weighted-augmented
object — i.e. the critic genuinely discriminates rather than rubber-stamping.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .curvature import compute_all_objects
from .data import DataBundle
from .network import build_lead_lag_graph
from .residualize import residualize
from .validation import (
    config_model_zscores,
    residual_orthogonalization,
    spearman_curvature_vs_corr,
    topk_jaccard,
)

__all__ = ["AcceptRules", "Candidate", "Decision", "Orchestrator", "default_grid"]


# --------------------------------------------------------------------------- #
# Decision layer: candidate space + accept/reject rules
# --------------------------------------------------------------------------- #
@dataclass
class AcceptRules:
    """The critic's thresholds — a proposal is ACCEPTED only if all pass."""
    max_spearman: float = 0.8      # reject if curvature ~ |correlation|
    max_jaccard: float = 0.5       # reject if its picks ~ correlation's picks
    max_r2_on_degree: float = 0.95  # reject if ~ degree (no higher-order signal)
    min_null_frac: float = 0.0     # optional: require config-null significance
    min_edges: int = 20            # reject degenerate graphs


def default_grid() -> dict:
    """Decision-layer candidate space (Cartesian product is the proposal set)."""
    return {
        "residualize": ["market", "market_sector", "pca"],  # the residualization ladder
        "threshold": [0.90, 0.95],
        "triangle_mode": ["common"],
        "curvature": ["F_plain", "F_augmented"],  # degree baseline vs main object
    }


@dataclass
class Candidate:
    cid: str
    config: dict


@dataclass
class Decision:
    cid: str
    config: dict
    accepted: bool
    reasons: list  # which rules failed (empty if accepted)
    metrics: dict


def propose(grid: dict | None = None) -> list[Candidate]:
    """Enumerate the candidate signals (the proposer)."""
    grid = grid or default_grid()
    keys = list(grid)
    out = []
    for i, combo in enumerate(itertools.product(*(grid[k] for k in keys))):
        cfg = dict(zip(keys, combo))
        out.append(Candidate(cid=f"cand{i:03d}", config=cfg))
    return out


# --------------------------------------------------------------------------- #
# Execution layer: build -> measure -> judge
# --------------------------------------------------------------------------- #
def _residualize(returns: pd.DataFrame, sectors, method: str) -> pd.DataFrame:
    if method == "market_sector" and sectors is not None:
        return residualize(returns, sectors=sectors, method="market_sector")
    if method == "pca":
        return residualize(returns, method="pca", n_pca=3)
    return residualize(returns, method="market")


class Orchestrator:
    """Run the propose -> test -> reject loop over a DataBundle."""

    def __init__(self, rules: AcceptRules | None = None, grid: dict | None = None,
                 lags=(1, 2, 3, 5), selection_k: int = 20, null_iters: int = 0,
                 seed: int = 0):
        self.rules = rules or AcceptRules()
        self.grid = grid or default_grid()
        self.lags = lags
        self.k = selection_k
        self.null_iters = null_iters
        self.seed = seed
        self.log: list[Decision] = []

    def _judge(self, cid, config, curv, col, G, r_res) -> Decision:
        rules, reasons, metrics = self.rules, [], {}
        n_edges = G.number_of_edges()
        metrics["edges"] = n_edges
        if n_edges < rules.min_edges:
            return Decision(cid, config, False, ["too few edges"], metrics)

        C = r_res.corr().abs()
        abs_corr = pd.Series({(u, v): C.loc[u, v] for u, v in G.edges()})
        spear = spearman_curvature_vs_corr(curv[col], abs_corr)
        jacc = topk_jaccard(curv[col], -abs_corr, k=self.k)
        feats = pd.DataFrame({
            "deg_in": {(u, v): G.in_degree(u) for u, v in G.edges()},
            "deg_out": {(u, v): G.out_degree(v) for u, v in G.edges()},
            "abs_rho": abs_corr,
        })
        r2 = residual_orthogonalization(curv[col], feats).r_squared
        metrics.update(spearman=float(spear), jaccard=float(jacc), r2_on_degree=float(r2))

        if abs(spear) >= rules.max_spearman:
            reasons.append(f"spearman {spear:.2f} >= {rules.max_spearman} (~correlation)")
        if jacc > rules.max_jaccard:
            reasons.append(f"jaccard {jacc:.2f} > {rules.max_jaccard} (~correlation picks)")
        if r2 >= rules.max_r2_on_degree:
            reasons.append(f"R2-on-degree {r2:.2f} >= {rules.max_r2_on_degree} (~degree, no higher-order)")
        if self.null_iters > 0:
            frac = config_model_zscores(G, n_null=self.null_iters, seed=self.seed).frac_significant
            metrics["null_frac_significant"] = float(frac)
            if frac < rules.min_null_frac:
                reasons.append(f"null-significant frac {frac:.2f} < {rules.min_null_frac}")

        return Decision(cid, config, accepted=(len(reasons) == 0), reasons=reasons, metrics=metrics)

    def run(self, bundle: DataBundle) -> dict:
        """Execute the loop; returns a structured log of every accept/reject."""
        returns, sectors = bundle.returns, bundle.sectors
        if sectors is not None and sectors.isna().any():
            sectors = sectors.fillna("OTHER")
        cands = propose(self.grid)
        # cache graphs by (residualize, threshold) so each is built once
        gcache: dict = {}
        self.log = []
        for c in cands:
            cfg = c.config
            key = (cfg["residualize"], cfg["threshold"])
            if key not in gcache:
                r_res = _residualize(returns, sectors, cfg["residualize"])
                G = build_lead_lag_graph(r_res, lags=self.lags, threshold=cfg["threshold"])
                gcache[key] = (G, r_res, {})
            G, r_res, curv_cache = gcache[key]
            tm = cfg["triangle_mode"]
            if tm not in curv_cache:
                curv_cache[tm] = compute_all_objects(G, triangle_mode=tm, with_ollivier=False)
            curv = curv_cache[tm]
            self.log.append(self._judge(c.cid, cfg, curv, cfg["curvature"], G, r_res))

        accepted = [d for d in self.log if d.accepted]
        return {
            "n_candidates": len(self.log),
            "n_accepted": len(accepted),
            "n_rejected": len(self.log) - len(accepted),
            "decisions": self.log,
        }

    # ---- auditable artifacts (Lec 17 persistent-memory pattern) ----------- #
    def findings_markdown(self, result: dict) -> str:
        lines = ["# Orchestrator findings — propose → test → reject log", ""]
        lines.append(f"Proposed **{result['n_candidates']}** candidate signals · "
                     f"accepted **{result['n_accepted']}** · rejected **{result['n_rejected']}**.")
        lines.append("")
        lines.append("| cand | residualize | thr | curvature | verdict | spearman | jaccard | R²(deg) | reason |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for d in result["decisions"]:
            m = d.metrics
            v = "✅ accept" if d.accepted else "❌ reject"
            reason = "" if d.accepted else "; ".join(d.reasons)
            lines.append(
                f"| {d.cid} | {d.config['residualize']} | {d.config['threshold']} | "
                f"{d.config['curvature']} | {v} | {m.get('spearman', float('nan')):.2f} | "
                f"{m.get('jaccard', float('nan')):.2f} | {m.get('r2_on_degree', float('nan')):.2f} | {reason} |")
        return "\n".join(lines) + "\n"
