r"""Discrete Ricci curvature — the four objects compared in this project.

Objects (CLAUDE.md §4.6)
------------------------
1. **Plain directed Forman** (degree BASELINE only).
2. **Augmented Forman** ``F# = F + 3 m`` (m = triangles on the edge).
3. **Weighted augmented directed Forman** (the MAIN method).
4. **Ollivier-Ricci** (robustness / what Sandhu et al. used).

Weighted Forman (Samal et al. 2018 Eq. 7 / Sreejith et al. 2016), for an edge
``e = (v1, v2)`` with edge weight ``w_e`` and vertex weights ``w_v1, w_v2``::

    F(e) = w_e * ( w_v1/w_e + w_v2/w_e
                   - Σ_{e' ~ v1}  w_v1 / sqrt(w_e * w_{e'})
                   - Σ_{e' ~ v2}  w_v2 / sqrt(w_e * w_{e'}) )

where ``e' ~ v`` ranges over the *incident edge set* at vertex ``v``. The choice
of incident set is what makes the curvature undirected or directed:

* **undirected**: all edges touching ``v`` except ``e`` itself.
* **directed, "bottleneck" flow** (default; CLAUDE.md §4.2 — in-edges at the
  source, out-edges at the target): at ``v1`` the in-edges (predecessors), at
  ``v2`` the out-edges (successors); the reverse edge ``v2 -> v1`` is excluded
  from both sets.

Unweighted reductions (set all weights = 1):

* undirected: ``F(e) = 4 - deg(v1) - deg(v2)``  (Samal Eq. 8 — matches spec).
* directed bottleneck, no reciprocal edge:
  ``F(e) = 2 - deg_in(v1) - deg_out(v2)``.

  NOTE / FLAG: CLAUDE.md §4.2 writes the directed reduction as
  ``4 - deg_in(v1) - deg_out(v2)``. Under the clean "bottleneck" flow convention
  the constant is **2**, not 4, because the edge ``e`` belongs to neither incident
  set (it is an out-edge of ``v1`` and an in-edge of ``v2``), so there is no
  "-1 for excluding e" bonus at either endpoint. The constant is a pure additive
  offset and does **not** affect rankings, residualization, or any downstream
  test. Verify against arXiv:1605.04662 before quoting a constant in the paper.
  We expose ``base`` so the offset is auditable.
"""

from __future__ import annotations

import math
from typing import Iterable, Literal, Sequence

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linprog

__all__ = [
    "forman_curvature",
    "forman_curvatures",
    "triangle_count",
    "augmented_forman_curvatures",
    "ollivier_ricci_curvature",
    "compute_all_objects",
]

Flow = Literal["bottleneck", "through"]
TriangleMode = Literal["common", "cyclic"]


# --------------------------------------------------------------------------- #
# Incident edge sets
# --------------------------------------------------------------------------- #
def _incident_weights(
    G: nx.Graph | nx.DiGraph,
    v1: object,
    v2: object,
    weight: str,
    flow: Flow,
) -> tuple[list[float], list[float]]:
    """Return (weights of edges incident to v1, incident to v2) under the
    chosen convention, each excluding the edge ``e=(v1,v2)`` and its reverse."""
    directed = G.is_directed()

    def w(a: object, b: object) -> float:
        return float(G[a][b].get(weight, 1.0))

    if not directed:
        inc1 = [w(v1, nb) for nb in G.neighbors(v1) if nb != v2]
        inc2 = [w(v2, nb) for nb in G.neighbors(v2) if nb != v1]
        return inc1, inc2

    if flow == "bottleneck":
        # in-edges at the source v1, out-edges at the target v2
        inc1 = [w(p, v1) for p in G.predecessors(v1) if p != v2]
        inc2 = [w(v2, s) for s in G.successors(v2) if s != v1]
    elif flow == "through":
        # out-edges at the source v1, in-edges at the target v2 (exclude e)
        inc1 = [w(v1, s) for s in G.successors(v1) if s != v2]
        inc2 = [w(p, v2) for p in G.predecessors(v2) if p != v1]
    else:  # pragma: no cover
        raise ValueError(f"unknown flow convention: {flow!r}")
    return inc1, inc2


def forman_curvature(
    G: nx.Graph | nx.DiGraph,
    v1: object,
    v2: object,
    weight: str = "weight",
    vertex_weight: float = 1.0,
    flow: Flow = "bottleneck",
) -> float:
    """Weighted Forman-Ricci curvature of the single edge ``(v1, v2)``.

    Vertex weights are taken constant (``vertex_weight``) per CLAUDE.md §4.4
    (``w_v = 1`` default). The unweighted special case is recovered when all
    edge weights are 1 and ``vertex_weight == 1``.
    """
    w_e = float(G[v1][v2].get(weight, 1.0))
    if w_e <= 0:
        raise ValueError("edge weights must be positive for weighted Forman")
    wv = float(vertex_weight)

    inc1, inc2 = _incident_weights(G, v1, v2, weight, flow)
    base = wv / w_e + wv / w_e  # w_v1/w_e + w_v2/w_e
    s1 = sum(wv / math.sqrt(w_e * we) for we in inc1)
    s2 = sum(wv / math.sqrt(w_e * we) for we in inc2)
    return w_e * (base - s1 - s2)


def forman_curvatures(
    G: nx.Graph | nx.DiGraph,
    weight: str = "weight",
    vertex_weight: float = 1.0,
    flow: Flow = "bottleneck",
) -> dict[tuple, float]:
    """Forman curvature for every edge. Keys are edge tuples as stored in G."""
    return {
        (u, v): forman_curvature(G, u, v, weight, vertex_weight, flow)
        for u, v in G.edges()
    }


# --------------------------------------------------------------------------- #
# Triangles and augmentation
# --------------------------------------------------------------------------- #
def triangle_count(
    G: nx.Graph | nx.DiGraph,
    u: object,
    v: object,
    mode: TriangleMode = "common",
) -> int:
    """Number of triangles on edge ``(u, v)``.

    * ``"common"``: common neighbours ignoring direction — ``|N(u) ∩ N(v)|`` in
      the underlying undirected graph. (CLAUDE.md §4.3 convention (b).)
    * ``"cyclic"``: strict directed 3-cycles ``u -> v -> w -> u`` (only meaningful
      for a DiGraph). (Convention (a).)
    """
    if mode == "common":
        UG = G.to_undirected() if G.is_directed() else G
        return len(set(UG.neighbors(u)) & set(UG.neighbors(v)) - {u, v})
    if mode == "cyclic":
        if not G.is_directed():
            raise ValueError("cyclic triangles require a directed graph")
        succ_v = set(G.successors(v))
        pred_u = set(G.predecessors(u))
        return len((succ_v & pred_u) - {u, v})
    raise ValueError(f"unknown triangle mode: {mode!r}")


def augmented_forman_curvatures(
    G: nx.Graph | nx.DiGraph,
    weight: str = "weight",
    vertex_weight: float = 1.0,
    flow: Flow = "bottleneck",
    triangle_mode: TriangleMode = "common",
) -> dict[tuple, float]:
    """Augmented Forman ``F#(e) = F(e) + 3 m(e)`` for every edge (Samal Eq. 10,
    triangles only per Serrano de Haro Iváñez 2022)."""
    base = forman_curvatures(G, weight, vertex_weight, flow)
    return {
        (u, v): base[(u, v)] + 3 * triangle_count(G, u, v, triangle_mode)
        for u, v in G.edges()
    }


# --------------------------------------------------------------------------- #
# Ollivier-Ricci (baseline / robustness) — exact W1 via LP
# --------------------------------------------------------------------------- #
def _probability_measure(
    G: nx.Graph | nx.DiGraph,
    x: object,
    alpha: float,
    weight: str,
) -> dict[object, float]:
    """Mass ``alpha`` on x, ``1-alpha`` spread over neighbours proportional to
    edge weight (uniform if unweighted). Uses the undirected neighbourhood."""
    UG = G.to_undirected() if G.is_directed() else G
    nbrs = list(UG.neighbors(x))
    measure: dict[object, float] = {}
    if not nbrs:
        return {x: 1.0}
    w = np.array([float(UG[x][n].get(weight, 1.0)) for n in nbrs], dtype=float)
    w = w / w.sum()
    if alpha > 0:
        measure[x] = alpha
    for n, wi in zip(nbrs, w):
        measure[n] = measure.get(n, 0.0) + (1.0 - alpha) * wi
    return measure


def ollivier_ricci_curvature(
    G: nx.Graph | nx.DiGraph,
    u: object,
    v: object,
    alpha: float = 0.0,
    weight: str = "weight",
) -> float:
    """Ollivier-Ricci curvature ``κ(u,v) = 1 - W1(m_u, m_v) / d(u,v)``.

    W1 is the exact 1-Wasserstein (earth-mover) distance, solved as a small LP
    with ``scipy.optimize.linprog``; ground distances are hop distances on the
    undirected graph. ``alpha`` is the lazy-walk idleness (0 = no laziness).
    """
    UG = G.to_undirected() if G.is_directed() else G
    m_u = _probability_measure(G, u, alpha, weight)
    m_v = _probability_measure(G, v, alpha, weight)
    src = list(m_u), list(m_v)
    supp_u, supp_v = src
    a = np.array([m_u[s] for s in supp_u], dtype=float)
    b = np.array([m_v[s] for s in supp_v], dtype=float)

    # ground distances between supports (hop distance)
    cost = np.zeros((len(supp_u), len(supp_v)))
    for i, su in enumerate(supp_u):
        lengths = nx.single_source_shortest_path_length(UG, su)
        for j, sv in enumerate(supp_v):
            cost[i, j] = lengths.get(sv, len(UG))  # unreachable -> large
    c = cost.reshape(-1)

    nu, nv = len(supp_u), len(supp_v)
    # equality constraints: row marginals = a, column marginals = b
    A_eq = np.zeros((nu + nv, nu * nv))
    for i in range(nu):
        A_eq[i, i * nv : (i + 1) * nv] = 1.0
    for j in range(nv):
        A_eq[nu + j, j::nv] = 1.0
    b_eq = np.concatenate([a, b])
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method="highs")
    if not res.success:  # pragma: no cover
        raise RuntimeError(f"OT LP failed: {res.message}")
    w1 = float(res.fun)
    d_uv = 1.0  # adjacent
    return 1.0 - w1 / d_uv


def ollivier_ricci_curvatures(
    G: nx.Graph | nx.DiGraph,
    alpha: float = 0.0,
    weight: str = "weight",
) -> dict[tuple, float]:
    return {(u, v): ollivier_ricci_curvature(G, u, v, alpha, weight) for u, v in G.edges()}


# --------------------------------------------------------------------------- #
# All four objects in one DataFrame (the ablation spine)
# --------------------------------------------------------------------------- #
def compute_all_objects(
    G: nx.DiGraph,
    weight: str = "weight",
    flow: Flow = "bottleneck",
    triangle_mode: TriangleMode = "common",
    with_ollivier: bool = True,
) -> pd.DataFrame:
    """Compute the four curvature objects for every directed edge.

    Columns: ``F_plain`` (unweighted degree baseline), ``F_weighted``,
    ``F_augmented`` (weighted F + 3m), ``m`` (triangle count), ``ollivier``,
    and ``weight``. Index is a MultiIndex (source, target).
    """
    if not G.is_directed():
        raise ValueError("compute_all_objects expects a directed graph")

    # plain unweighted: set all weights to 1 by computing on a unit-weight view
    H = nx.DiGraph()
    H.add_nodes_from(G.nodes())
    H.add_edges_from((u, v) for u, v in G.edges())  # no weights -> default 1.0
    f_plain = forman_curvatures(H, weight="weight", vertex_weight=1.0, flow=flow)

    f_w = forman_curvatures(G, weight=weight, vertex_weight=1.0, flow=flow)
    rows = []
    oll = ollivier_ricci_curvatures(G, weight=weight) if with_ollivier else {}
    for u, v in G.edges():
        m = triangle_count(G, u, v, triangle_mode)
        rows.append(
            {
                "source": u,
                "target": v,
                "weight": float(G[u][v].get(weight, 1.0)),
                "F_plain": f_plain[(u, v)],
                "F_weighted": f_w[(u, v)],
                "m": m,
                "F_augmented": f_w[(u, v)] + 3 * m,
                "ollivier": oll.get((u, v), np.nan),
            }
        )
    df = pd.DataFrame(rows).set_index(["source", "target"])
    return df
