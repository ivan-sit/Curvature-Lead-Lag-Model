"""Synthetic data generators with KNOWN ground truth.

Two generators:

1. ``planted_directed_sbm`` — a directed stochastic block model with positive
   edge *strengths*. Used as ground truth for kill-switch A: the curvature ->
   line-graph -> AFRC pipeline should recover the planted blocks, and the blocks
   are dense enough to contain triangles (so the AFRC augmentation is non-trivial).

2. ``factor_lead_lag_returns`` — a returns panel with an injected market factor,
   sector factors, idiosyncratic noise, and explicit leader -> lagger lead-lag
   links at a known lag. Used to test (a) factor/sector residualization (the
   common variance must be removable) and (b) the BCR lead-lag estimator (it must
   recover the planted leaders and lag sign).

All randomness flows through an explicit ``numpy.random.Generator`` so results are
reproducible from a seed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import numpy as np
import pandas as pd

__all__ = [
    "PlantedSBM",
    "planted_directed_sbm",
    "LeadLagReturns",
    "factor_lead_lag_returns",
]


# --------------------------------------------------------------------------- #
# 1. Planted directed stochastic block model
# --------------------------------------------------------------------------- #
@dataclass
class PlantedSBM:
    """A planted directed SBM and its ground-truth community labels."""

    graph: nx.DiGraph
    labels: np.ndarray  # labels[i] = block id of node i
    block_sizes: list[int]

    @property
    def n_nodes(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def n_blocks(self) -> int:
        return len(self.block_sizes)


def planted_directed_sbm(
    block_sizes: list[int],
    p_in: float = 0.45,
    p_out: float = 0.03,
    weight_in: tuple[float, float] = (1.0, 0.25),
    weight_out: tuple[float, float] = (0.4, 0.2),
    seed: int | None = 0,
) -> PlantedSBM:
    """Generate a directed SBM with positive edge strengths.

    For each *ordered* pair (i, j), i != j, add a directed edge i -> j with
    probability ``p_in`` if i and j share a block, else ``p_out``. Edge weight
    (a positive *strength*, analogous to |lead-lag statistic|) is drawn from a
    Normal truncated at a small positive floor; intra-block edges are stronger.

    Parameters
    ----------
    block_sizes : sizes of each planted community.
    p_in, p_out : intra-/inter-block directed edge probabilities. ``p_in`` is kept
        well above ``p_out`` so blocks are triangle-dense (AFRC needs triangles).
    weight_in, weight_out : (mean, std) of edge strengths for intra/inter edges.
    seed : RNG seed.

    Returns
    -------
    PlantedSBM
    """
    if any(s <= 0 for s in block_sizes):
        raise ValueError("block_sizes must be positive")
    if not (0.0 <= p_out <= p_in <= 1.0):
        raise ValueError("require 0 <= p_out <= p_in <= 1")

    rng = np.random.default_rng(seed)
    n = sum(block_sizes)
    labels = np.concatenate([np.full(s, b) for b, s in enumerate(block_sizes)])

    g = nx.DiGraph()
    g.add_nodes_from(range(n))

    floor = 1e-3
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            same = labels[i] == labels[j]
            p = p_in if same else p_out
            if rng.random() < p:
                mu, sigma = weight_in if same else weight_out
                w = float(max(floor, rng.normal(mu, sigma)))
                g.add_edge(i, j, weight=w)

    return PlantedSBM(graph=g, labels=labels, block_sizes=list(block_sizes))


# --------------------------------------------------------------------------- #
# 2. Factor + lead-lag returns panel
# --------------------------------------------------------------------------- #
@dataclass
class LeadLagReturns:
    """A synthetic returns panel with known factor and lead-lag structure."""

    returns: pd.DataFrame                 # (T, N) daily returns, columns = tickers
    sectors: pd.Series                    # ticker -> sector id
    lead_lag_pairs: list[tuple[str, str, int]]  # (leader, lagger, lag)
    market: np.ndarray = field(repr=False)       # (T,) market factor
    sector_factors: np.ndarray = field(repr=False)  # (T, n_sectors)


def factor_lead_lag_returns(
    n_assets: int = 40,
    n_periods: int = 1500,
    n_sectors: int = 4,
    market_beta: float = 1.0,
    market_vol: float = 0.01,
    sector_vol: float = 0.008,
    idio_vol: float = 0.012,
    n_lead_lag_pairs: int = 8,
    lead_lag_strength: float = 0.5,
    lead_lag: int = 1,
    seed: int | None = 0,
) -> LeadLagReturns:
    """Generate returns = market + sector + idiosyncratic + injected lead-lag.

    The data-generating process for asset ``a`` at time ``t``::

        r[t, a] = beta_a * market[t]
                  + sector_factor[t, sector(a)]
                  + idio[t, a]
                  + (lead-lag injections: lagger gets strength * leader[t - lag])

    Lead-lag pairs are chosen *within* a sector so that the directional signal is
    idiosyncratic (survives market+sector residualization) — this mirrors the
    project's claim that the real signal lives in residual returns.

    Returns
    -------
    LeadLagReturns with ground-truth ``lead_lag_pairs`` as (leader, lagger, lag).
    """
    if n_lead_lag_pairs * 2 > n_assets:
        raise ValueError("need at least 2 assets per lead-lag pair")
    if lead_lag < 1:
        raise ValueError("lead_lag must be >= 1")

    rng = np.random.default_rng(seed)
    tickers = [f"A{a:03d}" for a in range(n_assets)]
    sector_ids = rng.integers(0, n_sectors, size=n_assets)
    sectors = pd.Series(sector_ids, index=tickers, name="sector")

    market = rng.normal(0.0, market_vol, size=n_periods)
    sector_factors = rng.normal(0.0, sector_vol, size=(n_periods, n_sectors))
    betas = rng.normal(market_beta, 0.2, size=n_assets)
    idio = rng.normal(0.0, idio_vol, size=(n_periods, n_assets))

    r = np.empty((n_periods, n_assets))
    for a in range(n_assets):
        r[:, a] = betas[a] * market + sector_factors[:, sector_ids[a]] + idio[:, a]

    # Inject lead-lag links *within sector*: pick disjoint (leader, lagger) pairs.
    lead_lag_pairs: list[tuple[str, str, int]] = []
    available = list(range(n_assets))
    rng.shuffle(available)
    used: set[int] = set()
    for _ in range(n_lead_lag_pairs):
        leader = None
        lagger = None
        # find a same-sector disjoint pair
        for li in available:
            if li in used:
                continue
            for lj in available:
                if lj in used or lj == li:
                    continue
                if sector_ids[li] == sector_ids[lj]:
                    leader, lagger = li, lj
                    break
            if leader is not None:
                break
        if leader is None:  # no same-sector pair left; take any disjoint pair
            rem = [x for x in available if x not in used]
            if len(rem) < 2:
                break
            leader, lagger = rem[0], rem[1]
        used.update({leader, lagger})
        # lagger today partially follows leader `lead_lag` steps ago
        r[lead_lag:, lagger] += lead_lag_strength * idio[:-lead_lag, leader]
        lead_lag_pairs.append((tickers[leader], tickers[lagger], lead_lag))

    returns = pd.DataFrame(r, columns=tickers)
    returns.index.name = "t"
    return LeadLagReturns(
        returns=returns,
        sectors=sectors,
        lead_lag_pairs=lead_lag_pairs,
        market=market,
        sector_factors=sector_factors,
    )
