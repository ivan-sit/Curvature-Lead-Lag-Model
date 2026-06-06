"""Kill-switch A (synthetic recovery) and B (triangle density)."""

import networkx as nx

from cllm.diagnostics import kill_switch_a, kill_switch_b, triangle_density
from cllm.synthetic import factor_lead_lag_returns


def test_kill_switch_a_passes_on_structured_sbm():
    res = kill_switch_a(block_sizes=(20, 20, 20), p_in=0.45, p_out=0.02, seed=0)
    assert res.passed
    assert res.ari > 0.6
    assert res.gap > 0
    assert res.kappa_intra > res.kappa_inter


def test_kill_switch_a_fails_on_structureless_graph():
    # p_in ~ p_out => no planted structure => should NOT recover communities
    res = kill_switch_a(block_sizes=(20, 20, 20), p_in=0.12, p_out=0.10, seed=1)
    assert res.ari < 0.4
    assert not res.passed


def test_triangle_density_flags_dense_vs_sparse():
    # dense block (triangle-rich) -> not sparse
    dense = nx.gnp_random_graph(30, 0.5, seed=2)
    comms_dense = {n: 0 for n in dense.nodes()}
    r_dense = triangle_density(dense, communities=comms_dense, label="dense")
    assert not r_dense.triangle_sparse
    assert r_dense.frac_zero_m < 0.5

    # a tree is triangle-free -> sparse, augmentation degenerate
    tree = nx.balanced_tree(2, 4)
    comms_tree = {n: 0 for n in tree.nodes()}
    r_tree = triangle_density(tree, communities=comms_tree, label="tree")
    assert r_tree.triangle_sparse
    assert r_tree.frac_zero_m == 1.0
    assert r_tree.total_triangles == 0


def test_kill_switch_b_sweep_returns_sensible_stats():
    data = factor_lead_lag_returns(n_assets=40, n_periods=2000, n_sectors=4,
                                   n_lead_lag_pairs=8, seed=3)
    results = kill_switch_b(
        data.returns, sectors=data.sectors,
        sparsify_thresholds=(0.80, 0.90, 0.95),
    )
    assert len(results) == 3
    for r in results:
        assert 0.0 <= r.frac_zero_m <= 1.0
        assert r.mean_m >= 0.0
        assert "sparsify_threshold" in r.extra
        # sparser graphs (higher quantile) should never have more edges
    edge_counts = [r.n_edges for r in results]
    assert edge_counts[0] >= edge_counts[-1]
