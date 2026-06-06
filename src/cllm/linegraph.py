r"""Line graph + AFRC curvature-based community detection (CLAUDE.md §5).

Pairs are EDGES of the lead-lag network ``G``. To cluster pairs with node-based
machinery, build the **line graph** ``L(G)``: every edge of ``G`` becomes a node of
``L(G)``; two ``L(G)`` nodes are adjacent iff their ``G``-edges share a vertex.
Curvature on ``L(G)`` answers "is this pair isolated relative to *other pairs*?".

We start with the **undirected reduction** of ``L(G)`` (the Tian-Lubberts-Weber
framework is undirected; the directed construction is flagged as open — §10 Risk
#2). Community detection follows the AFRC approach (Fesser-Weber-Lambiotte):
negatively-curved edges are bridges between communities; remove them and read off
connected components.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from .curvature import augmented_forman_curvatures

__all__ = [
    "line_graph",
    "afrc_communities",
    "curvature_gap",
]


def line_graph(G: nx.Graph | nx.DiGraph, weight: str = "weight") -> nx.Graph:
    """Undirected line graph ``L(G)``.

    Nodes are the edges of ``G`` (as tuples, oriented as stored). Two nodes are
    connected iff the underlying ``G``-edges share an endpoint. Each ``L(G)`` node
    carries the original edge's ``weight`` as node attribute ``g_weight``; each
    ``L(G)`` edge gets a weight = geometric mean of the two incident strengths
    (so strong pairs sharing a stock are strongly linked in pair-space).
    """
    L = nx.Graph()
    edges = list(G.edges())
    # map each G-vertex to the L(G) nodes (edges) touching it
    incident: dict[object, list[tuple]] = {}
    for e in edges:
        u, v = e
        L.add_node(e, g_weight=float(G[u][v].get(weight, 1.0)))
        incident.setdefault(u, []).append(e)
        incident.setdefault(v, []).append(e)

    for _vertex, elist in incident.items():
        for i in range(len(elist)):
            for j in range(i + 1, len(elist)):
                e1, e2 = elist[i], elist[j]
                if e1 == e2:
                    continue
                w1 = L.nodes[e1]["g_weight"]
                w2 = L.nodes[e2]["g_weight"]
                L.add_edge(e1, e2, weight=float(np.sqrt(w1 * w2)))
    return L


def _components_to_labels(graph: nx.Graph) -> dict:
    labels: dict = {}
    for comp_id, comp in enumerate(nx.connected_components(graph)):
        for node in comp:
            labels[node] = comp_id
    return labels


def afrc_communities(
    G: nx.Graph,
    weight: str = "weight",
    triangle_mode: str = "common",
    threshold: float = 0.0,
    iterative: bool = True,
    max_removals: int | None = None,
    patience: int = 25,
) -> dict:
    """Curvature-based community detection via curvature-guided edge removal.

    Negatively-curved edges are bridges between communities. Two modes:

    * ``iterative=True`` (default) — a discrete curvature **flow** guided by
      modularity: repeatedly remove the single most negatively-curved edge and
      recompute; track the connected-component partition whose modularity (on the
      original weighted graph) is highest, and return that. Stops after
      ``patience`` non-improving removals. This is curvature-driven
      Girvan-Newman and is robust without a hand-tuned threshold.
    * ``iterative=False`` — one-shot: remove every edge with curvature below
      ``threshold`` and read off components.

    Returns ``{node: community_label}``.
    """
    from networkx.algorithms.community import modularity

    G0 = G.to_undirected() if G.is_directed() else G.copy()
    H = G0.copy()

    if not iterative:
        curv = augmented_forman_curvatures(H, weight=weight, triangle_mode=triangle_mode)
        for (u, v), val in curv.items():
            if val < threshold and H.has_edge(u, v):
                H.remove_edge(u, v)
        return _components_to_labels(H)

    def mod_of(graph: nx.Graph) -> float:
        comms = list(nx.connected_components(graph))
        return modularity(G0, comms, weight=weight)

    best_labels = _components_to_labels(H)
    best_mod = mod_of(H)
    no_improve = 0
    cap = max_removals if max_removals is not None else G0.number_of_edges()

    for _ in range(cap):
        if H.number_of_edges() == 0:
            break
        curv = augmented_forman_curvatures(H, weight=weight, triangle_mode=triangle_mode)
        edge, val = min(curv.items(), key=lambda kv: kv[1])
        H.remove_edge(*edge)
        m = mod_of(H)
        if m > best_mod + 1e-12:
            best_mod = m
            best_labels = _components_to_labels(H)
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience and val >= threshold:
                break
    return best_labels


def curvature_gap(
    G: nx.Graph | nx.DiGraph,
    labels: dict,
    weight: str = "weight",
    triangle_mode: str = "common",
) -> dict:
    """AFRC curvature gap ``Δκ = (κ_intra − κ_inter) / σ_pooled`` (CLAUDE.md §4.7).

    Edges are split into intra-community (endpoints share a label) vs inter-community;
    we compare their augmented-Forman curvature distributions. A large positive gap
    means communities are curvature-separable. Returns a dict with the gap, the two
    means, and the counts.

    CAVEAT (Fesser-Weber-Lambiotte): the gap collapses for triangle-sparse
    communities — there is no universal numeric threshold. Interpret relative to a
    null, not against a fixed cutoff.
    """
    curv = augmented_forman_curvatures(G, weight=weight, triangle_mode=triangle_mode)
    intra, inter = [], []
    for (u, v), val in curv.items():
        if u not in labels or v not in labels:
            continue
        (intra if labels[u] == labels[v] else inter).append(val)

    intra = np.asarray(intra, dtype=float)
    inter = np.asarray(inter, dtype=float)
    if intra.size == 0 or inter.size == 0:
        return {"gap": np.nan, "kappa_intra": np.nan, "kappa_inter": np.nan,
                "n_intra": int(intra.size), "n_inter": int(inter.size)}

    pooled = np.sqrt((intra.var(ddof=1) + inter.var(ddof=1)) / 2) if (
        intra.size > 1 and inter.size > 1) else np.std(np.concatenate([intra, inter]))
    pooled = pooled if pooled > 0 else 1.0
    return {
        "gap": float((intra.mean() - inter.mean()) / pooled),
        "kappa_intra": float(intra.mean()),
        "kappa_inter": float(inter.mean()),
        "n_intra": int(intra.size),
        "n_inter": int(inter.size),
    }
