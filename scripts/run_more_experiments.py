#!/usr/bin/env python3
"""A battery of 'what can curvature signify?' experiments (25-yr daily, fixed universe).

Keep only what works. Each experiment prints a clear PASS/weak verdict.
  B) node curvature  -> ranks stocks by FUTURE volatility?   (cross-sectional risk)
  C) aggregate curvature -> forward market DRAWDOWN?          (tail-risk early warning)
"""

from __future__ import annotations

from collections import defaultdict

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from cllm.curvature import compute_all_objects, forman_curvatures
from cllm.network import build_lead_lag_graph

WIN, STEP = 63, 21


def load():
    rets = pd.read_parquet("data/returns_wrds.parquet")
    keep = rets.columns[rets.notna().mean() >= 0.98]
    R = rets[keep].fillna(0.0)
    return R, R.mean(axis=1)


def exp_B_node_vol(R):
    """Does a node's curvature rank-predict its OWN forward volatility?"""
    node_ic, deg_ic = [], []
    for end in range(WIN, len(R) - STEP, STEP):
        w = R.iloc[end - WIN:end]
        GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
        if GL.number_of_edges() < 30:
            continue
        curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"]
        acc = defaultdict(list)
        for (u, v), val in curv.items():
            acc[u].append(val); acc[v].append(val)
        nodes = [n for n in GL.nodes() if acc[n]]
        ncur = np.array([np.mean(acc[n]) for n in nodes])
        ndeg = np.array([GL.degree(n) for n in nodes])
        fvol = np.array([R[n].iloc[end:end + STEP].std() for n in nodes])
        ok = np.isfinite(ncur) & np.isfinite(fvol)
        if ok.sum() < 20:
            continue
        node_ic.append(spearmanr(ncur[ok], fvol[ok]).statistic)
        deg_ic.append(spearmanr(ndeg[ok], fvol[ok]).statistic)
    node_ic, deg_ic = np.array(node_ic), np.array(deg_ic)
    print("\n=== Exp B: node curvature -> forward stock volatility (cross-sectional) ===")
    print(f"  curvature IC: mean {node_ic.mean():+.3f}  frac>0 {np.mean(node_ic>0):.0%}  (n={len(node_ic)})")
    print(f"  degree   IC: mean {deg_ic.mean():+.3f}  frac>0 {np.mean(deg_ic>0):.0%}")
    print(f"  VERDICT: {'PASS' if abs(node_ic.mean())>0.1 and np.mean(node_ic>0) in (0,1) or abs(node_ic.mean())>0.15 else 'weak/insignificant'}")


def exp_C_drawdown(R, mkt):
    """Does aggregate curvature lead forward market DRAWDOWN?"""
    rows = []
    for end in range(WIN, len(R) - STEP, STEP):
        w = R.iloc[end - WIN:end]
        cols = list(w.columns)
        A = w.corr().abs().to_numpy()
        iu, ju = np.triu_indices(len(cols), 1)
        G = nx.Graph(); G.add_nodes_from(cols)
        for i, j in zip(iu, ju):
            if A[i, j] > 0.5:
                G.add_edge(cols[i], cols[j])
        curv = float(np.mean(list(forman_curvatures(G).values()))) if G.number_of_edges() else np.nan
        fwd = mkt.iloc[end:end + STEP]
        cum = (1 + fwd).cumprod()
        dd = float((cum / cum.cummax() - 1).min())  # most-negative forward drawdown
        rows.append({"curv": curv, "fwd_dd": dd, "vol_now": float(mkt.iloc[end - WIN:end].std())})
    d = pd.DataFrame(rows).dropna()
    rc = spearmanr(d["curv"], d["fwd_dd"]).statistic
    # partial: control current vol
    bz = np.polyfit(d["vol_now"], d["curv"], 1); rx = d["curv"] - np.polyval(bz, d["vol_now"])
    by = np.polyfit(d["vol_now"], d["fwd_dd"], 1); ry = d["fwd_dd"] - np.polyval(by, d["vol_now"])
    pr = spearmanr(rx, ry).statistic
    print("\n=== Exp C: aggregate curvature -> forward market drawdown ===")
    print(f"  spearman(curv, fwd_drawdown) = {rc:+.3f}   (n={len(d)})")
    print(f"  partial | vol_now           = {pr:+.3f}")
    print(f"  VERDICT: {'PASS' if abs(rc)>0.2 else 'weak'} (raw); {'adds beyond vol' if abs(pr)>0.1 else 'no add beyond vol'}")


def main():
    R, mkt = load()
    print(f"fixed universe {R.shape[1]} names, {R.shape[0]} days")
    exp_B_node_vol(R)
    exp_C_drawdown(R, mkt)


if __name__ == "__main__":
    main()
