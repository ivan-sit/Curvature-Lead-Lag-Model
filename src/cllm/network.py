r"""Lead-lag network construction (CLAUDE.md §4.4, build step §11.3).

Edge weight = **Bennett-Cucuringu-Reinert signed lead-lag statistic**::

    w_{i->j} = rho_ij(tau*) - rho_ji(tau*)

where ``rho_ij(tau) = corr(r_i[t], r_j[t+tau])`` (past i vs. future j) and ``tau*``
is the lag at which the *signed* statistic peaks in magnitude. The statistic is
antisymmetric (``w_{j->i} = -w_{i->j}``); a pair becomes a **directed edge in the
sign direction**, with a positive *strength* = ``|w|`` used as the curvature edge
weight (the weighted Forman formula needs positive weights; direction carries the
asymmetry).

The symmetric correlation graph would destroy exactly this directional
information — which is the whole point of using a directed graph.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd

__all__ = [
    "lagged_cross_correlation",
    "signed_lead_lag",
    "build_lead_lag_graph",
    "bootstrap_edge_stability",
    "walk_forward_windows",
]


def _standardize(M: np.ndarray) -> np.ndarray:
    """Column-standardize (z-score) a 2D array; zero-variance cols -> 0."""
    mu = M.mean(axis=0, keepdims=True)
    sd = M.std(axis=0, ddof=1, keepdims=True)
    sd[sd == 0] = np.inf  # zero-variance -> standardized to 0, corr -> 0
    return (M - mu) / sd


def lagged_cross_correlation(returns: pd.DataFrame, lag: int) -> np.ndarray:
    """Cross-correlation matrix ``C[i,j] = corr(r_i[t], r_j[t+lag])`` for lag>=1.

    Past of asset i vs. future of asset j. ``C`` is generally non-symmetric;
    its antisymmetric part is the directional lead-lag signal.
    """
    if lag < 1:
        raise ValueError("lag must be >= 1 (contemporaneous corr carries no direction)")
    R = returns.to_numpy(dtype=float)
    X = _standardize(R[:-lag])   # r_i[t]
    Y = _standardize(R[lag:])    # r_j[t+lag]
    n = X.shape[0]
    return (X.T @ Y) / (n - 1)


@dataclass
class LeadLagEstimate:
    """Output of :func:`signed_lead_lag`."""

    tickers: list[str]
    W: np.ndarray          # antisymmetric signed statistic, W[i,j] = w_{i->j}
    best_lag: np.ndarray   # (N,N) int, the tau* per pair (upper triangle filled)


def signed_lead_lag(returns: pd.DataFrame, lags: tuple[int, ...] = (1, 2, 3, 5)) -> LeadLagEstimate:
    """BCR signed lead-lag statistic, choosing tau* per pair by peak |statistic|."""
    tickers = list(returns.columns)
    N = len(tickers)
    # signed statistic at each lag: S_l = C_l - C_l^T
    signed = {}
    for lag in lags:
        C = lagged_cross_correlation(returns, lag)
        signed[lag] = C - C.T  # antisymmetric

    W = np.zeros((N, N))
    best_lag = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(i + 1, N):
            # pick lag maximizing magnitude of the signed statistic
            vals = {lag: signed[lag][i, j] for lag in lags}
            star = max(vals, key=lambda l: abs(vals[l]))
            w = vals[star]
            W[i, j], W[j, i] = w, -w
            best_lag[i, j] = best_lag[j, i] = star
    return LeadLagEstimate(tickers=tickers, W=W, best_lag=best_lag)


def build_lead_lag_graph(
    returns: pd.DataFrame,
    lags: tuple[int, ...] = (1, 2, 3, 5),
    sparsify: str = "quantile",
    threshold: float = 0.9,
    min_abs: float = 0.0,
) -> nx.DiGraph:
    """Build the sparsified directed lead-lag graph.

    Parameters
    ----------
    sparsify : ``"quantile"`` keeps pairs whose ``|w|`` exceeds the given quantile
        of all ``|w|``; ``"absolute"`` keeps pairs with ``|w| >= threshold``;
        ``"none"`` keeps every pair.
    threshold : quantile in [0,1] (if ``"quantile"``) or absolute cutoff
        (if ``"absolute"``).
    min_abs : additional hard floor on ``|w|`` (drops near-zero edges).

    Each kept pair becomes a directed edge in the sign direction with::

        weight = |w|          (positive strength, used by weighted Forman)
        signed = w            (the raw signed statistic)
        lag    = tau*
    """
    est = signed_lead_lag(returns, lags)
    W, lag_mat, tickers = est.W, est.best_lag, est.tickers
    N = len(tickers)

    iu, ju = np.triu_indices(N, k=1)
    mags = np.abs(W[iu, ju])

    if sparsify == "quantile":
        cut = np.quantile(mags, threshold) if mags.size else 0.0
    elif sparsify == "absolute":
        cut = threshold
    elif sparsify == "none":
        cut = -np.inf
    else:
        raise ValueError(f"unknown sparsify mode: {sparsify!r}")
    cut = max(cut, min_abs)

    G = nx.DiGraph()
    G.add_nodes_from(tickers)
    G.graph["lags"] = list(lags)
    G.graph["sparsify"] = sparsify
    G.graph["cutoff"] = float(cut)
    for i, j in zip(iu, ju):
        w = W[i, j]
        if abs(w) <= cut or abs(w) == 0.0:
            continue
        if w > 0:
            src, dst = tickers[i], tickers[j]
        else:
            src, dst = tickers[j], tickers[i]
        G.add_edge(src, dst, weight=float(abs(w)), signed=float(w),
                   lag=int(lag_mat[i, j]))
    return G


def bootstrap_edge_stability(
    returns: pd.DataFrame,
    lags: tuple[int, ...] = (1, 2, 3, 5),
    n_boot: int = 50,
    block: int = 20,
    sparsify: str = "quantile",
    threshold: float = 0.9,
    seed: int | None = 0,
) -> pd.DataFrame:
    """Block-bootstrap the time series and report directional edge stability.

    Returns a DataFrame indexed by (source, target) with the fraction of
    bootstrap resamples in which that directed edge appears with the same
    orientation. Directly targets lead-lag estimation noise (CLAUDE.md §7.1,
    group ref [G3]).
    """
    rng = np.random.default_rng(seed)
    T = len(returns)
    n_blocks = int(np.ceil(T / block))
    counts: dict[tuple[str, str], int] = {}

    for _ in range(n_boot):
        starts = rng.integers(0, max(1, T - block), size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block, T)) for s in starts])[:T]
        boot = returns.iloc[idx].reset_index(drop=True)
        G = build_lead_lag_graph(boot, lags, sparsify, threshold)
        for u, v in G.edges():
            counts[(u, v)] = counts.get((u, v), 0) + 1

    rows = [{"source": u, "target": v, "stability": c / n_boot} for (u, v), c in counts.items()]
    if not rows:
        return pd.DataFrame(columns=["stability"]).rename_axis(["source", "target"])
    return pd.DataFrame(rows).set_index(["source", "target"]).sort_values("stability", ascending=False)


def walk_forward_windows(n_periods: int, train: int, test: int, step: int | None = None):
    """Yield (train_idx, test_idx) numpy slices for walk-forward evaluation.

    tau* and the trading/IC signal are fit on ``train`` and evaluated on the
    immediately following ``test`` window — no lookahead.
    """
    step = step or test
    start = 0
    while start + train + test <= n_periods:
        tr = np.arange(start, start + train)
        te = np.arange(start + train, start + train + test)
        yield tr, te
        start += step
