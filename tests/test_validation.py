"""Structural validation cascade tests."""

import networkx as nx
import numpy as np
import pandas as pd

from cllm.curvature import augmented_forman_curvatures, forman_curvatures
from cllm.diagnostics import kill_switch_a  # noqa: F401 (ensures import graph ok)
from cllm.synthetic import planted_directed_sbm
from cllm.validation import (
    benjamini_hochberg,
    config_model_zscores,
    residual_orthogonalization,
    spearman_curvature_vs_corr,
    topk_jaccard,
    train_val_test_split,
)


def test_spearman_independent_is_low():
    rng = np.random.default_rng(0)
    curv = pd.Series(rng.normal(size=200), index=range(200))
    rho = pd.Series(rng.uniform(size=200), index=range(200))  # independent
    s = spearman_curvature_vs_corr(curv, rho)
    assert abs(s) < 0.8


def test_topk_jaccard_extremes():
    a = pd.Series(range(10), index=[f"e{i}" for i in range(10)])
    assert topk_jaccard(a, a, k=3) == 1.0  # identical rankings
    b = pd.Series(range(10), index=[f"e{i}" for i in range(10)][::-1])
    # top-3 of a = {e0,e1,e2}; top-3 of b (smallest values) = {e9,e8,e7} -> disjoint
    assert topk_jaccard(a, b, k=3) == 0.0


def test_plain_forman_is_degree_identity():
    # (iv): on the real (non-reciprocal) lead-lag graph, plain Forman is an exact
    # function of (deg_in(src), deg_out(dst)) -> R^2 = 1, residual ~ 0.
    from cllm.network import build_lead_lag_graph
    from cllm.synthetic import factor_lead_lag_returns

    data = factor_lead_lag_returns(n_assets=40, n_periods=2000, n_lead_lag_pairs=6, seed=1)
    G = build_lead_lag_graph(data.returns, lags=(1, 2, 3), sparsify="quantile", threshold=0.8)
    assert not any(G.has_edge(v, u) for u, v in G.edges())  # non-reciprocal

    fp = forman_curvatures(G)  # weighted? no -> use unit-weight plain baseline
    H = nx.DiGraph()
    H.add_edges_from(G.edges())
    fp = forman_curvatures(H)
    curv = pd.Series({e: v for e, v in fp.items()})
    feats = pd.DataFrame(
        {
            "deg_in_src": {e: H.in_degree(e[0]) for e in fp},
            "deg_out_dst": {e: H.out_degree(e[1]) for e in fp},
        }
    )
    res = residual_orthogonalization(curv, feats)
    assert res.is_degree_identity
    assert res.r_squared > 0.999
    assert np.allclose(res.residuals.to_numpy(), 0.0, atol=1e-6)


def test_augmented_is_not_degree_identity():
    # the augmentation (triangles) is NOT explained by degree -> R^2 < 1
    G = planted_directed_sbm([15, 15], p_in=0.45, p_out=0.05, seed=2).graph
    fa = augmented_forman_curvatures(G, triangle_mode="common")
    curv = pd.Series({e: v for e, v in fa.items()})
    feats = pd.DataFrame(
        {
            "deg_in_src": {e: G.in_degree(e[0]) for e in fa},
            "deg_out_dst": {e: G.out_degree(e[1]) for e in fa},
        }
    )
    res = residual_orthogonalization(curv, feats)
    assert res.r_squared < 0.999  # higher-order signal survives degree regression
    assert not np.allclose(res.residuals.to_numpy(), 0.0, atol=1e-6)


def test_config_null_detects_structure_in_sbm():
    # assortative SBM edges have more common neighbours than degree alone predicts
    sbm = planted_directed_sbm([18, 18, 18], p_in=0.45, p_out=0.02, seed=4)
    res = config_model_zscores(sbm.graph, n_null=60, swap_mult=8, seed=0)
    assert res.n_null == 60
    assert np.isfinite(res.zscores).all()
    # a meaningful fraction of edges carry significant higher-order structure
    assert res.frac_significant > 0.05


def test_benjamini_hochberg_basic():
    p = pd.Series([0.001, 0.01, 0.2, 0.04, 0.8], index=list("abcde"))
    out = benjamini_hochberg(p, alpha=0.05)
    assert out.loc["a", "reject"]  # smallest p rejected
    assert not out.loc["e", "reject"]  # largest p not rejected
    assert (out["p_adj"] >= p.loc[out.index]).all()  # adjusted >= raw


def test_train_val_test_split_is_ordered_and_contiguous():
    tr, va, te = train_val_test_split(1000, (0.6, 0.2, 0.2))
    assert len(tr) == 600 and len(va) == 200 and len(te) == 200
    assert tr.max() < va.min() < va.max() < te.min()  # strict time order
