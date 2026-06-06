"""Line graph construction + AFRC community detection + curvature gap."""

import networkx as nx
from sklearn.metrics import adjusted_rand_score

from cllm.linegraph import afrc_communities, curvature_gap, line_graph
from cllm.synthetic import planted_directed_sbm


def test_line_graph_basic_structure():
    # path 0-1-2 : edges (0,1) and (1,2) share vertex 1 -> adjacent in L(G)
    G = nx.Graph([(0, 1), (1, 2)])
    L = line_graph(G)
    assert L.number_of_nodes() == 2
    assert L.has_edge((0, 1), (1, 2)) or L.has_edge((1, 2), (0, 1))


def test_line_graph_star_is_complete():
    # star edges all share the center -> L(G) is complete on the spokes
    star = nx.star_graph(4)  # center 0, leaves 1..4 -> 4 edges
    L = line_graph(star)
    n = L.number_of_nodes()
    assert n == 4
    assert L.number_of_edges() == n * (n - 1) // 2  # complete graph K4


def test_afrc_recovers_planted_blocks():
    sbm = planted_directed_sbm([20, 20, 20], p_in=0.45, p_out=0.02, seed=7)
    labels = afrc_communities(sbm.graph.to_undirected(), iterative=True)
    pred = [labels[i] for i in range(sbm.n_nodes)]
    ari = adjusted_rand_score(sbm.labels.tolist(), pred)
    # curvature-based detection should substantially recover the planted blocks
    assert ari > 0.6


def test_curvature_gap_positive_on_planted_communities():
    sbm = planted_directed_sbm([20, 20, 20], p_in=0.45, p_out=0.02, seed=8)
    truth = {i: int(sbm.labels[i]) for i in range(sbm.n_nodes)}
    gap = curvature_gap(sbm.graph.to_undirected(), truth)
    # intra-community edges are triangle-rich (more positive) than inter-community
    assert gap["kappa_intra"] > gap["kappa_inter"]
    assert gap["gap"] > 0
