r"""The two kill-switch diagnostics (CLAUDE.md §10 Risk #1, §11 build order).

These run BEFORE trusting the full pipeline on real data.

Kill-switch A — synthetic recovery
    Run curvature -> AFRC community detection -> curvature gap on a planted
    directed SBM. If the pipeline cannot recover structure we *planted*, it cannot
    be trusted on markets. (Gate A in docs/PLAN.md.)

Kill-switch B — triangle density (the highest-priority risk)
    Fesser-Weber-Lambiotte prove the AFRC curvature gap *collapses* for
    triangle-sparse communities. Directed cyclic triangles are even rarer. We
    measure, across sparsification levels, the fraction of edges with zero
    triangles (degenerate augmentation) and the within-community triangle density.
    If the real lead-lag graph is triangle-sparse, the whole L(G)/AFRC approach is
    at risk and must be reconsidered. (Gate B / go-no-go in docs/PLAN.md.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from .curvature import triangle_count
from .linegraph import afrc_communities, curvature_gap
from .network import build_lead_lag_graph
from .synthetic import planted_directed_sbm

__all__ = [
    "KillSwitchAResult",
    "kill_switch_a",
    "TriangleDensityResult",
    "triangle_density",
    "kill_switch_b",
]


# --------------------------------------------------------------------------- #
# Kill-switch A — synthetic recovery
# --------------------------------------------------------------------------- #
@dataclass
class KillSwitchAResult:
    ari: float
    gap: float
    kappa_intra: float
    kappa_inter: float
    n_communities_found: int
    n_communities_true: int
    passed: bool

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"[Kill-switch A: {verdict}] ARI={self.ari:.3f} "
            f"gap={self.gap:.3f} (intra={self.kappa_intra:.2f}, inter={self.kappa_inter:.2f}) "
            f"communities found={self.n_communities_found}/{self.n_communities_true}"
        )


def kill_switch_a(
    block_sizes: tuple[int, ...] = (20, 20, 20),
    p_in: float = 0.45,
    p_out: float = 0.02,
    seed: int = 0,
    ari_threshold: float = 0.6,
) -> KillSwitchAResult:
    """Does curvature -> AFRC -> gap recover a planted directed SBM?"""
    sbm = planted_directed_sbm(list(block_sizes), p_in=p_in, p_out=p_out, seed=seed)
    UG = sbm.graph.to_undirected()
    labels = afrc_communities(UG, iterative=True)
    pred = [labels[i] for i in range(sbm.n_nodes)]
    ari = adjusted_rand_score(sbm.labels.tolist(), pred)

    truth = {i: int(sbm.labels[i]) for i in range(sbm.n_nodes)}
    gap = curvature_gap(UG, truth)
    passed = bool(ari >= ari_threshold and gap["gap"] > 0)
    return KillSwitchAResult(
        ari=float(ari),
        gap=float(gap["gap"]),
        kappa_intra=float(gap["kappa_intra"]),
        kappa_inter=float(gap["kappa_inter"]),
        n_communities_found=len(set(pred)),
        n_communities_true=sbm.n_blocks,
        passed=passed,
    )


# --------------------------------------------------------------------------- #
# Kill-switch B — triangle density
# --------------------------------------------------------------------------- #
@dataclass
class TriangleDensityResult:
    label: str                       # what graph / threshold this describes
    n_nodes: int
    n_edges: int
    frac_zero_m: float               # fraction of edges with m == 0 (degenerate)
    mean_m: float
    median_m: float
    total_triangles: int
    within_community_triangle_frac: float  # triangles fully inside one community
    avg_within_community_clustering: float
    triangle_sparse: bool
    extra: dict = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        flag = "TRIANGLE-SPARSE (escalate)" if self.triangle_sparse else "ok"
        return (
            f"[{self.label}] edges={self.n_edges} zero-m={self.frac_zero_m:.0%} "
            f"mean_m={self.mean_m:.2f} within-comm tri={self.within_community_triangle_frac:.0%} "
            f"-> {flag}"
        )


def triangle_density(
    G: nx.Graph | nx.DiGraph,
    communities: dict | None = None,
    triangle_mode: str = "common",
    label: str = "graph",
    zero_m_warn: float = 0.5,
    within_frac_warn: float = 0.25,
) -> TriangleDensityResult:
    """Triangle statistics for one graph, with a triangle-sparsity flag.

    ``triangle_sparse`` is raised when a majority of edges carry no triangle
    (``frac_zero_m > zero_m_warn``) OR communities hold little triangle structure
    (``within_community_triangle_frac < within_frac_warn``) — either makes the AFRC
    augmentation degenerate / the curvature gap unreliable.
    """
    UG = G.to_undirected() if G.is_directed() else G
    n_edges = G.number_of_edges()
    ms = [triangle_count(G, u, v, mode=triangle_mode) for u, v in G.edges()]
    ms_arr = np.asarray(ms, dtype=float) if ms else np.array([0.0])

    tri_per_node = nx.triangles(UG)
    total_triangles = int(sum(tri_per_node.values()) // 3)

    within_tri = 0
    clusterings = []
    if communities is not None and total_triangles > 0:
        comm_to_nodes: dict = {}
        for node, c in communities.items():
            comm_to_nodes.setdefault(c, []).append(node)
        for nodes in comm_to_nodes.values():
            sub = UG.subgraph(nodes)
            within_tri += int(sum(nx.triangles(sub).values()) // 3)
            if sub.number_of_nodes() >= 1:
                clusterings.append(nx.average_clustering(sub))
    within_frac = (within_tri / total_triangles) if total_triangles > 0 else 0.0
    avg_clust = float(np.mean(clusterings)) if clusterings else float(nx.average_clustering(UG))

    frac_zero = float(np.mean(ms_arr == 0))
    sparse = bool(frac_zero > zero_m_warn or (communities is not None and within_frac < within_frac_warn))

    return TriangleDensityResult(
        label=label,
        n_nodes=G.number_of_nodes(),
        n_edges=n_edges,
        frac_zero_m=frac_zero,
        mean_m=float(ms_arr.mean()),
        median_m=float(np.median(ms_arr)),
        total_triangles=total_triangles,
        within_community_triangle_frac=float(within_frac),
        avg_within_community_clustering=avg_clust,
        triangle_sparse=sparse,
    )


def kill_switch_b(
    returns: pd.DataFrame,
    sectors: pd.Series | None = None,
    lags: tuple[int, ...] = (1, 2, 3, 5),
    sparsify_thresholds: tuple[float, ...] = (0.80, 0.90, 0.95),
    triangle_mode: str = "common",
) -> list[TriangleDensityResult]:
    """Sweep sparsification and report triangle density of the lead-lag graph.

    The decision gate: if the graph is triangle-sparse at the operating
    sparsification levels, the AFRC augmentation is degenerate and the
    L(G)/AFRC stack must be reconsidered (or switch triangle convention / relax
    sparsification). Communities for the within-community measure are the GICS
    sectors when provided, else AFRC communities.
    """
    results: list[TriangleDensityResult] = []
    sector_labels = sectors.to_dict() if sectors is not None else None
    for thr in sparsify_thresholds:
        G = build_lead_lag_graph(returns, lags=lags, sparsify="quantile", threshold=thr)
        comms = sector_labels
        if comms is None and G.number_of_edges() > 0:
            comms = afrc_communities(G, iterative=True)
        res = triangle_density(
            G, communities=comms, triangle_mode=triangle_mode,
            label=f"lead-lag@q{thr:.2f}",
        )
        res.extra["sparsify_threshold"] = thr
        results.append(res)
    return results
