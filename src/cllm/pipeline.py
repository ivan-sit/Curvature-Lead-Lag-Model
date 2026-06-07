r"""End-to-end pipeline (CLAUDE.md §6 / §11 build order).

returns + sectors
  -> residualize (market+sector)              [§4.5]
  -> directed lead-lag graph (BCR)            [§4.4]
  -> kill-switch B: triangle density          [§10 Risk #1]
  -> four curvature objects                   [§4.6]
  -> line graph L(G) + AFRC communities + Δκ  [§5]
  -> structural validation cascade            [§7.1]
  -> select pairs + OOS directional IC vs baselines  [§7.2]

Returns a ``PipelineResult`` capturing every stage so the critic/agent can audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import pandas as pd

from .curvature import compute_all_objects, forman_curvatures
from .data import DataBundle
from .diagnostics import triangle_density
from .evaluation import (
    block_bootstrap_ic,
    directional_ic,
    select_by_cointegration,
    select_by_correlation,
    select_random,
    select_top_edges,
)
from .linegraph import afrc_communities, curvature_gap, line_graph
from .network import build_lead_lag_graph
from .residualize import residualize
from .validation import (
    config_model_zscores,
    residual_orthogonalization,
    spearman_curvature_vs_corr,
    topk_jaccard,
    train_val_test_split,
)


@dataclass
class PipelineConfig:
    lags: tuple[int, ...] = (1, 2, 3, 5)
    residualize_method: str = "market_sector"
    sparsify: str = "quantile"
    threshold: float = 0.90
    triangle_mode: str = "common"
    curvature_column: str = "F_augmented"   # selection signal (most negative = isolated)
    selection_k: int = 15
    split: tuple[float, float, float] = (0.6, 0.2, 0.2)
    null_iters: int = 100
    seed: int = 0


@dataclass
class PipelineResult:
    config: PipelineConfig
    graph: nx.DiGraph
    curvature: pd.DataFrame
    triangle: object                       # TriangleDensityResult (kill-switch B)
    communities: dict
    gap: dict
    cascade: dict
    selected_pairs: list
    ic_by_method: pd.DataFrame
    notes: list = field(default_factory=list)


def _abs_corr_per_edge(returns: pd.DataFrame, edges) -> pd.Series:
    C = returns.corr().abs()
    return pd.Series({(u, v): C.loc[u, v] for u, v in edges})


def run_pipeline(bundle: DataBundle, config: PipelineConfig | None = None) -> PipelineResult:
    cfg = config or PipelineConfig()
    notes: list[str] = []
    returns, sectors = bundle.returns, bundle.sectors

    # time-ordered split (lock selection on validate, evaluate once on test)
    tr, va, te = train_val_test_split(len(returns), cfg.split)
    r_train = returns.iloc[np.concatenate([tr, va])].reset_index(drop=True)
    r_test = returns.iloc[te].reset_index(drop=True)

    # 1) residualize on train+val (factors estimated in-sample only)
    if sectors is not None and cfg.residualize_method == "market_sector":
        r_resid = residualize(r_train, sectors=sectors, method="market_sector")
    else:
        r_resid = residualize(r_train, method="market")
        if sectors is None:
            notes.append("no sectors provided -> market-only residualization")

    # 2) directed lead-lag graph on residual returns
    G = build_lead_lag_graph(r_resid, lags=cfg.lags, sparsify=cfg.sparsify, threshold=cfg.threshold)
    notes.append(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    if G.number_of_edges() < 3:
        notes.append("WARNING: too few edges; loosen sparsification")

    # 3) kill-switch B: triangle density of the real graph
    comm_for_tri = sectors.to_dict() if sectors is not None else None
    tri = triangle_density(G, communities=comm_for_tri, triangle_mode=cfg.triangle_mode,
                           label="lead-lag")
    if tri.triangle_sparse:
        notes.append("KILL-SWITCH B: triangle-sparse -> AFRC augmentation degenerate (escalate)")

    # 4) four curvature objects
    curv = compute_all_objects(G, triangle_mode=cfg.triangle_mode, with_ollivier=True)

    # 5) line graph + AFRC communities + curvature gap
    LG = line_graph(G)
    lg_comms = afrc_communities(LG, iterative=True) if LG.number_of_edges() else {}
    comm_labels = sectors.to_dict() if sectors is not None else afrc_communities(G, iterative=True)
    gap = curvature_gap(G, comm_labels, triangle_mode=cfg.triangle_mode)

    # 6) structural validation cascade
    abs_corr = _abs_corr_per_edge(r_resid, list(G.edges()))
    spearman = spearman_curvature_vs_corr(curv[cfg.curvature_column], abs_corr)
    curv_rank = curv[cfg.curvature_column]                      # ascending => isolated
    corr_rank = (-abs_corr)                                     # ascending => highest corr
    jacc = topk_jaccard(curv_rank, corr_rank, k=cfg.selection_k)
    null = config_model_zscores(G, n_null=cfg.null_iters, seed=cfg.seed)

    feats = pd.DataFrame({
        "deg_in_src": {(u, v): G.in_degree(u) for u, v in G.edges()},
        "deg_out_dst": {(u, v): G.out_degree(v) for u, v in G.edges()},
        "abs_rho": abs_corr,
    })
    res_plain = residual_orthogonalization(curv["F_plain"], feats[["deg_in_src", "deg_out_dst"]])
    res_aug = residual_orthogonalization(curv["F_augmented"], feats)
    cascade = {
        "spearman_F_vs_absrho": spearman,
        "topk_jaccard_vs_corr": jacc,
        "null_frac_significant": null.frac_significant,
        "plain_forman_R2": res_plain.r_squared,
        "plain_is_degree_identity": res_plain.is_degree_identity,
        "augmented_R2": res_aug.r_squared,
    }

    # 7) selection + OOS directional IC vs baselines
    tickers = list(returns.columns)
    candidates = [(tickers[i], tickers[j]) for i in range(len(tickers)) for j in range(i + 1, len(tickers))]

    curv_pairs = select_top_edges(curv.assign(lag=[G[u][v]["lag"] for u, v in curv.index]),
                                  cfg.curvature_column, cfg.selection_k, ascending=True)
    oll_pairs = select_top_edges(curv.assign(lag=[G[u][v]["lag"] for u, v in curv.index]),
                                 "ollivier", cfg.selection_k, ascending=True)
    # undirected Forman on the symmetrized graph
    undirected = forman_curvatures(G.to_undirected())
    undirected_df = pd.DataFrame({"F_und": undirected})
    undirected_df["lag"] = [G[u][v]["lag"] if G.has_edge(u, v) else G[v][u]["lag"]
                            for u, v in undirected_df.index]
    und_pairs = select_top_edges(undirected_df, "F_und", cfg.selection_k, ascending=True)

    method_pairs = {
        "curvature(aug,directed)": curv_pairs,
        "undirected_forman": und_pairs,
        "ollivier": oll_pairs,
        "correlation": select_by_correlation(r_train, candidates, cfg.selection_k, cfg.lags),
        "cointegration": select_by_cointegration(r_train, candidates, cfg.selection_k, cfg.lags),
        "random": select_random(candidates, cfg.selection_k, r_train, cfg.lags, seed=cfg.seed),
    }

    rows = []
    for name, pairs in method_pairs.items():
        ic = directional_ic(r_train, r_test, pairs)
        ci = block_bootstrap_ic(r_train, r_test, pairs, n_boot=100, block=20, seed=cfg.seed)
        rows.append({
            "method": name, "n_pairs": ic.n_pairs, "mean_ic": ic.mean_ic,
            "pooled_ic": ic.pooled_ic, "ic_ci_low": ci["ci_low"], "ic_ci_high": ci["ci_high"],
        })
    ic_by_method = pd.DataFrame(rows).set_index("method").sort_values("mean_ic", ascending=False)

    return PipelineResult(
        config=cfg, graph=G, curvature=curv, triangle=tri, communities=comm_labels,
        gap=gap, cascade=cascade, selected_pairs=curv_pairs, ic_by_method=ic_by_method,
        notes=notes,
    )
