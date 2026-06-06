"""Tests for synthetic generators — they must have the structure we plant."""

import networkx as nx
import numpy as np

from cllm.synthetic import factor_lead_lag_returns, planted_directed_sbm


def test_sbm_shapes_and_reproducibility():
    a = planted_directed_sbm([10, 10, 10], seed=1)
    b = planted_directed_sbm([10, 10, 10], seed=1)
    assert a.n_nodes == 30
    assert a.n_blocks == 3
    assert sorted(a.graph.edges()) == sorted(b.graph.edges())  # deterministic
    assert len(a.labels) == 30


def test_sbm_is_assortative_and_weighted():
    sbm = planted_directed_sbm([15, 15, 15], p_in=0.45, p_out=0.03, seed=2)
    lab = sbm.labels
    intra = inter = 0
    for u, v in sbm.graph.edges():
        if lab[u] == lab[v]:
            intra += 1
        else:
            inter += 1
        assert sbm.graph[u][v]["weight"] > 0  # positive strengths
    # far more intra-block edges than inter-block (assortative communities)
    assert intra > 3 * inter


def test_sbm_has_triangles():
    # AFRC needs triangles; the planted blocks must be triangle-dense.
    sbm = planted_directed_sbm([15, 15, 15], p_in=0.45, p_out=0.03, seed=3)
    undirected = sbm.graph.to_undirected()
    n_triangles = sum(nx.triangles(undirected).values()) // 3
    assert n_triangles > 0


def test_returns_panel_shape_and_pairs():
    data = factor_lead_lag_returns(n_assets=40, n_periods=1200, n_lead_lag_pairs=8, seed=5)
    assert data.returns.shape == (1200, 40)
    assert len(data.lead_lag_pairs) == 8
    # leaders/laggers are disjoint
    leaders = [p[0] for p in data.lead_lag_pairs]
    laggers = [p[1] for p in data.lead_lag_pairs]
    assert len(set(leaders) | set(laggers)) == len(leaders) + len(laggers)


def test_injected_lead_lag_is_detectable():
    # The lagger's return should correlate with the leader's lagged return.
    data = factor_lead_lag_returns(
        n_assets=20, n_periods=4000, n_lead_lag_pairs=4,
        lead_lag=1, lead_lag_strength=0.6, seed=7,
    )
    leader, lagger, lag = data.lead_lag_pairs[0]
    x = data.returns[leader].values[:-lag]
    y = data.returns[lagger].values[lag:]
    rho_lead = np.corrcoef(x, y)[0, 1]
    # and the reverse direction should be weaker (asymmetry => directed signal)
    x_rev = data.returns[lagger].values[:-lag]
    y_rev = data.returns[leader].values[lag:]
    rho_rev = np.corrcoef(x_rev, y_rev)[0, 1]
    assert rho_lead > 0.05
    assert rho_lead > rho_rev
