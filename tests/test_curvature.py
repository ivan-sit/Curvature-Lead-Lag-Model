"""Curvature validated against hand-computed analytic values."""

import math

import networkx as nx
import pytest

from cllm.curvature import (
    augmented_forman_curvatures,
    compute_all_objects,
    forman_curvature,
    ollivier_ricci_curvature,
    triangle_count,
)


# --------------------------------------------------------------------------- #
# Unweighted undirected Forman: F(e) = 4 - deg(v1) - deg(v2)  (Samal Eq. 8)
# --------------------------------------------------------------------------- #
def test_undirected_unweighted_reduction_path():
    G = nx.path_graph(3)  # 0-1-2
    assert forman_curvature(G, 0, 1) == pytest.approx(4 - 1 - 2)  # = 1
    assert forman_curvature(G, 1, 2) == pytest.approx(4 - 2 - 1)  # = 1


def test_undirected_unweighted_reduction_star_and_complete():
    star = nx.star_graph(3)  # center 0, leaves 1,2,3
    assert forman_curvature(star, 0, 1) == pytest.approx(4 - 3 - 1)  # = 0
    k4 = nx.complete_graph(4)
    assert forman_curvature(k4, 0, 1) == pytest.approx(4 - 3 - 3)  # = -2


# --------------------------------------------------------------------------- #
# Unweighted directed Forman, "bottleneck" flow:
#   F(e=v1->v2) = 2 - deg_in(v1) - deg_out(v2)   (no reciprocal edge)
# --------------------------------------------------------------------------- #
def test_directed_unweighted_reduction_path():
    G = nx.DiGraph([(0, 1), (1, 2), (2, 3)])
    # edge (1,2): deg_in(1)=1, deg_out(2)=1 -> 2-1-1 = 0
    assert forman_curvature(G, 1, 2) == pytest.approx(2 - 1 - 1)
    # edge (0,1): deg_in(0)=0, deg_out(1)=1 -> 2-0-1 = 1
    assert forman_curvature(G, 0, 1) == pytest.approx(2 - 0 - 1)


def test_directed_reduction_matches_formula_on_random_dag():
    G = nx.gnp_random_graph(15, 0.3, seed=4, directed=True)
    for u, v in G.edges():
        if G.has_edge(v, u):
            continue  # skip reciprocal edges (the +2*rev correction)
        deg_in_u = G.in_degree(u)
        deg_out_v = G.out_degree(v)
        assert forman_curvature(G, u, v) == pytest.approx(2 - deg_in_u - deg_out_v)


# --------------------------------------------------------------------------- #
# Weighted Forman: a fully hand-computed example
# --------------------------------------------------------------------------- #
def test_weighted_forman_hand_computed():
    # 5 ->(9) 0 ->(4) 1 ->(1) 2 ; evaluate edge e=(0,1), w_e=4
    G = nx.DiGraph()
    G.add_edge(5, 0, weight=9.0)
    G.add_edge(0, 1, weight=4.0)
    G.add_edge(1, 2, weight=1.0)
    # bottleneck: inc(v1=0)=in-edges at 0 = {5->0, w=9}; inc(v2=1)=out-edges at 1 = {1->2, w=1}
    # base = 1/4 + 1/4 = 0.5
    # s1 = 1/sqrt(4*9) = 1/6 ; s2 = 1/sqrt(4*1) = 1/2
    # F = 4 * (0.5 - 1/6 - 1/2) = 4 * (-1/6) = -2/3
    expected = 4.0 * (0.5 - 1.0 / 6.0 - 0.5)
    assert forman_curvature(G, 0, 1) == pytest.approx(expected)
    assert expected == pytest.approx(-2.0 / 3.0)


def test_weighted_reduces_to_unweighted_when_all_weights_one():
    G = nx.DiGraph([(0, 1), (1, 2), (3, 1)])
    for u, v in G.edges():
        nx.set_edge_attributes(G, 1.0, "weight")
    # weighted with unit weights == unweighted reduction
    assert forman_curvature(G, 1, 2, weight="weight") == pytest.approx(
        forman_curvature(G, 1, 2)
    )


# --------------------------------------------------------------------------- #
# Triangles and augmentation
# --------------------------------------------------------------------------- #
def test_triangle_counts_common_and_cyclic():
    tri = nx.DiGraph([(0, 1), (1, 2), (2, 0)])  # directed 3-cycle
    assert triangle_count(tri, 0, 1, mode="common") == 1
    assert triangle_count(tri, 0, 1, mode="cyclic") == 1  # 0->1->2->0
    # reverse-direction triangle has no compatible cycle for edge (0,1)
    acyc = nx.DiGraph([(0, 1), (0, 2), (1, 2)])  # common neighbor of 0,1 is 2
    assert triangle_count(acyc, 0, 1, mode="common") == 1
    assert triangle_count(acyc, 0, 1, mode="cyclic") == 0


def test_augmented_adds_three_per_triangle():
    k4 = nx.complete_graph(4)  # undirected
    f = forman_curvature(k4, 0, 1)            # = -2
    m = triangle_count(k4, 0, 1, "common")    # common neighbors {2,3} -> 2
    aug = augmented_forman_curvatures(k4, triangle_mode="common")
    assert m == 2
    assert aug[(0, 1)] == pytest.approx(f + 3 * m)  # -2 + 6 = 4


# --------------------------------------------------------------------------- #
# Ollivier-Ricci sign behaviour
# --------------------------------------------------------------------------- #
def test_ollivier_triangle_positive_bridge_negative():
    # two triangles joined by a bridge edge (2,3)
    G = nx.Graph([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (2, 3)])
    k_tri = ollivier_ricci_curvature(G, 0, 1)
    k_bridge = ollivier_ricci_curvature(G, 2, 3)
    assert k_tri > 0
    assert k_bridge < 0
    # exact value on a clean triangle K3
    k3 = nx.complete_graph(3)
    assert ollivier_ricci_curvature(k3, 0, 1) == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# The four-object table
# --------------------------------------------------------------------------- #
def test_compute_all_objects_columns_and_plain_baseline():
    G = nx.DiGraph()
    G.add_edge(0, 1, weight=2.0)
    G.add_edge(1, 2, weight=3.0)
    G.add_edge(2, 0, weight=1.5)  # makes a directed cycle -> triangles
    df = compute_all_objects(G, with_ollivier=True)
    assert set(df.columns) == {"weight", "F_plain", "F_weighted", "m", "F_augmented", "ollivier"}
    # F_plain is the unweighted degree baseline (independent of weights)
    for (u, v), row in df.iterrows():
        assert row["F_plain"] == pytest.approx(2 - G.in_degree(u) - G.out_degree(v)) or G.has_edge(v, u)
        assert row["F_augmented"] == pytest.approx(row["F_weighted"] + 3 * row["m"])
