#!/usr/bin/env python3
"""Structure-determined RETURN effects (not covariance) — the right place for alpha.
A) Centrality premium (Ahern): do central/bridge stocks (most-negative node curvature) earn more?
B) Cross-sector link momentum (Cohen-Frazzini): does a lagger follow its leaders' recent returns?
Monthly rebalance, equal-weight long-short, RAW returns, 25-yr daily, fixed universe.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np, pandas as pd
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
LOOK, STEP = 252, 21
rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
sec = pd.read_parquet("data/sectors_wrds.parquet")["gsector"].astype(str)
sec.index = [str(c) for c in sec.index]
def fwd_ret(names, s, e):
    return float(((1 + R[names].iloc[s:e]).prod() - 1).mean())
ls_cent, ls_mom = [], []
for end in range(LOOK, len(R) - STEP, STEP):
    w = R.iloc[end - LOOK:end]
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
    if GL.number_of_edges() < 50: continue
    curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"]
    # ---- A) node curvature (centrality): most-negative = most central/bridge ----
    acc = defaultdict(list)
    for (u, v), val in curv.items():
        acc[u].append(val); acc[v].append(val)
    nodes = [n for n in GL.nodes() if acc[n]]
    nc = pd.Series({n: np.mean(acc[n]) for n in nodes}).sort_values()
    q = max(len(nc) // 5, 3)
    central = list(nc.index[:q])            # most negative curvature = most central
    periph = list(nc.index[-q:])
    ls_cent.append(fwd_ret(central, end, end + STEP) - fwd_ret(periph, end, end + STEP))
    # ---- B) cross-sector link momentum: lagger ranked by leaders' last-month return ----
    last = (1 + R.iloc[end - STEP:end]).prod() - 1     # leaders' recent (1mo) return
    sig = {}
    for u, v, d in GL.edges(data=True):                # u leads v
        if sec.get(u, "x") == sec.get(v, "y"): continue  # cross-sector only
        sig.setdefault(v, []).append(np.sign(d["signed"]) * last.get(u, 0.0))
    s = pd.Series({k: np.mean(x) for k, x in sig.items() if x}).sort_values()
    if len(s) >= 10:
        qm = max(len(s) // 5, 3)
        winners = list(s.index[-qm:]); losers = list(s.index[:qm])
        ls_mom.append(fwd_ret(winners, end, end + STEP) - fwd_ret(losers, end, end + STEP))
def report(name, x):
    x = np.array(x); m = x.mean(); t = m / (x.std() / np.sqrt(len(x)))
    print(f"{name}: monthly LS {m*100:+.3f}%  ann {m*12*100:+.1f}%  Sharpe {m/x.std()*np.sqrt(12):+.2f}"
          f"  t={t:+.2f}  win {np.mean(x>0):.0%}  (n={len(x)})  -> {'SIGNAL' if abs(t)>2 else 'weak/null'}")
print()
report("A) centrality premium (central - peripheral)", ls_cent)
report("B) cross-sector link momentum (winners - losers)", ls_mom)
