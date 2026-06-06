"""Tests for lead-lag network construction — must recover planted direction."""

import numpy as np

from cllm.network import (
    build_lead_lag_graph,
    lagged_cross_correlation,
    signed_lead_lag,
    walk_forward_windows,
)
from cllm.synthetic import factor_lead_lag_returns


def test_signed_statistic_is_antisymmetric():
    data = factor_lead_lag_returns(n_assets=15, n_periods=2000, n_lead_lag_pairs=4, seed=1)
    est = signed_lead_lag(data.returns, lags=(1, 2, 3))
    W = est.W
    assert np.allclose(W, -W.T, atol=1e-12)
    assert np.allclose(np.diag(W), 0.0)


def test_lagged_corr_shape():
    data = factor_lead_lag_returns(n_assets=10, n_periods=500, n_lead_lag_pairs=3, seed=2)
    C = lagged_cross_correlation(data.returns, lag=1)
    assert C.shape == (10, 10)
    assert np.isfinite(C).all()


def test_graph_recovers_planted_direction():
    # strong, clean lead-lag at lag 1; the directed edge must point leader->lagger
    data = factor_lead_lag_returns(
        n_assets=24, n_periods=6000, n_lead_lag_pairs=6,
        lead_lag=1, lead_lag_strength=0.7, seed=11,
    )
    G = build_lead_lag_graph(data.returns, lags=(1, 2, 3), sparsify="quantile", threshold=0.85)
    recovered = 0
    for leader, lagger, _ in data.lead_lag_pairs:
        # the planted edge should appear leader->lagger (not the reverse)
        if G.has_edge(leader, lagger):
            recovered += 1
        assert not G.has_edge(lagger, leader)  # never the wrong direction
    # most planted pairs should survive sparsification with correct orientation
    assert recovered >= len(data.lead_lag_pairs) // 2


def test_walk_forward_windows_no_overlap_or_lookahead():
    wins = list(walk_forward_windows(1000, train=250, test=125))
    assert len(wins) > 0
    for tr, te in wins:
        assert tr.max() < te.min()  # train strictly precedes test (no lookahead)
        assert len(tr) == 250 and len(te) == 125
