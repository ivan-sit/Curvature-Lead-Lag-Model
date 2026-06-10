#!/usr/bin/env python3
"""Does STRUCTURAL (curvature/community) diversification reduce realized risk vs
correlation diversification? 25-yr daily, monthly rebalance, OOS risk (not return).

Hypothesis: in stress, correlations -> 1 so correlation-diversification fails, but the
structural (lead-lag community) spread is a different signal that may hold up.
"""
from __future__ import annotations
import networkx as nx, numpy as np, pandas as pd
from networkx.algorithms.community import greedy_modularity_communities
from cllm.network import build_lead_lag_graph

LOOK, STEP, K = 252, 21, 20
CRISIS = [("2008-09-01", "2009-03-31"), ("2020-02-15", "2020-04-30")]

def in_crisis(d):
    return any(pd.Timestamp(a) <= d <= pd.Timestamp(b) for a, b in CRISIS)

def sel_mincorr(C, cols, K, rng):
    Aabs = C.abs(); sel = [cols[rng.integers(len(cols))]]
    while len(sel) < K:
        rest = [c for c in cols if c not in sel]
        sel.append(min(rest, key=lambda c: Aabs.loc[c, sel].mean()))
    return sel

def sel_structural(GL, K):
    UG = GL.to_undirected()
    comms = sorted(greedy_modularity_communities(UG), key=len, reverse=True)
    reps = []
    while len(reps) < K and comms:
        for comm in comms:
            m = [x for x in comm if x not in reps]
            if m: reps.append(max(m, key=lambda x: UG.degree(x)))
            if len(reps) >= K: break
        if all(all(x in reps for x in c) for c in comms): break
    return reps[:K]

def risk(R, names, s, e):
    pr = R[names].iloc[s:e].mean(axis=1)
    vol = float(pr.std() * np.sqrt(252))
    cum = (1 + pr).cumprod(); dd = float((cum / cum.cummax() - 1).min())
    return vol, dd

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
idx = R.index; rng = np.random.default_rng(0)
rows = []
for end in range(LOOK, len(R) - STEP, STEP):
    w = R.iloc[end - LOOK:end]; cols = list(w.columns)
    C = w.corr()
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
    if GL.number_of_edges() < 50: continue
    p_mc = sel_mincorr(C, cols, K, rng)
    p_st = sel_structural(GL, K)
    p_rd = list(rng.choice(cols, K, replace=False))
    if len(p_st) < K: continue
    dcris = in_crisis(idx[end])
    for name, port in [("mincorr", p_mc), ("structural", p_st), ("random", p_rd)]:
        v, d = risk(R, port, end, end + STEP)
        rows.append({"date": idx[end], "method": name, "vol": v, "dd": d, "crisis": dcris})
df = pd.DataFrame(rows)
print(f"{df['date'].nunique()} rebalances\n")
print("OUT-OF-SAMPLE realized risk (lower = better diversification):")
print(f"{'method':12} {'vol_all':>8} {'dd_all':>8} | {'vol_crisis':>10} {'dd_crisis':>10}")
for m in ["mincorr", "structural", "random"]:
    d = df[df.method == m]; c = d[d.crisis]
    print(f"{m:12} {d.vol.mean():>8.3f} {d.dd.mean():>8.3f} | {c.vol.mean():>10.3f} {c.dd.mean():>10.3f}")
