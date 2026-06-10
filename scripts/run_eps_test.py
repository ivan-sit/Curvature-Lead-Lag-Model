#!/usr/bin/env python3
"""Does a stock's curvature relate to its EARNINGS risk? (cross-sectional, fixed universe)
Earnings risk = std of YoY EPS change per stock. Node curvature = time-avg of incident
augmented-Forman on the lead-lag graph. Control for return volatility (is it fundamentals,
not just price vol?).
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
WIN, STEP = 63, 21

eps = pd.read_parquet("data/eps_wrds.parquet").sort_values(["permno", "datadate"])
eps["permno"] = eps["permno"].astype(int).astype(str)
def eps_vol(g):
    s = g.set_index("datadate")["epsfxq"].dropna()
    if len(s) < 8: return np.nan
    return float(s.diff(4).dropna().std())          # YoY change vol (removes seasonality)
evol = eps.groupby("permno").apply(eps_vol).dropna()

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
acc = defaultdict(list)
for end in range(WIN, len(R) - STEP, STEP):
    w = R.iloc[end - WIN:end]
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
    if GL.number_of_edges() < 30: continue
    curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"]
    e = defaultdict(list)
    for (u, v), val in curv.items():
        e[u].append(val); e[v].append(val)
    for n in GL.nodes():
        if e[n]: acc[n].append(np.mean(e[n]))
node_curv = pd.Series({n: np.mean(v) for n, v in acc.items()})
ret_vol = R.std()

common = node_curv.index.intersection(evol.index)
nc = node_curv.loc[common]; ev = evol.loc[common]; rv = ret_vol.loc[common]
print(f"{len(common)} stocks with both curvature and EPS")
r = spearmanr(nc, ev).statistic
# control return vol
rx = nc - np.polyval(np.polyfit(rv, nc, 1), rv); ry = ev - np.polyval(np.polyfit(rv, ev, 1), rv)
pr = spearmanr(rx, ry).statistic
print(f"  spearman(node curvature, EPS vol)            = {r:+.3f}")
print(f"  partial | return-vol (is it fundamentals?)   = {pr:+.3f}")
print(f"  VERDICT: {'PASS' if abs(pr) > 0.2 else 'weak/null'}")
