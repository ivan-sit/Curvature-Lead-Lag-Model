#!/usr/bin/env python3
"""Professor's idea: can curvature do something with VIX? Test the literature claim that
curvature PREDICTS VIX increases (1/5/10/21d), controlling current VIX and realized vol.
Aggregate Forman curvature on the |corr|>0.5 graph, weekly (step 5) over 25 yrs.
"""
from __future__ import annotations
import networkx as nx, numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.curvature import forman_curvatures
WIN, STEP = 63, 5

vraw = pd.read_csv("data/vix.csv")
vraw.columns = [c.lower() for c in vraw.columns]
vix = pd.Series(pd.to_numeric(vraw.iloc[:, -1], errors="coerce").values,
                index=pd.to_datetime(vraw.iloc[:, 0])).dropna()
rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
mkt = R.mean(axis=1); idx = R.index
vix_np = vix.reindex(idx).ffill().to_numpy()

recs = []
for end in range(WIN, len(R), STEP):
    w = R.iloc[end - WIN:end]; cols = list(w.columns)
    A = w.corr().abs().to_numpy(); iu, ju = np.triu_indices(len(cols), 1)
    G = nx.Graph(); G.add_nodes_from(cols)
    for i, j in zip(iu, ju):
        if A[i, j] > 0.5: G.add_edge(cols[i], cols[j])
    curv = float(np.mean(list(forman_curvatures(G).values()))) if G.number_of_edges() else np.nan
    recs.append({"pos": end - 1, "curv": curv, "rvol": float(mkt.iloc[end - WIN:end].std()),
                 "vix_now": vix_np[end - 1]})
d = pd.DataFrame(recs).dropna()

def partial(x, y, *ctrls):
    Z = np.column_stack([np.ones_like(x)] + list(ctrls))
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return spearmanr(rx, ry).statistic

print(f"{len(d)} weekly windows\n")
print(f"contemporaneous:  spearman(curv, VIX) = {spearmanr(d.curv, d.vix_now).statistic:+.2f}"
      f"   spearman(realized vol, VIX) = {spearmanr(d.rvol, d.vix_now).statistic:+.2f}")
print("\nLEAD — does curvature predict the future VIX CHANGE, beyond current VIX (and rvol)?")
pos = d["pos"].to_numpy()
for h in [1, 5, 10, 21]:
    fwd = vix_np[np.minimum(pos + h, len(vix_np) - 1)]
    dvix = fwd - d["vix_now"].to_numpy()
    ok = np.isfinite(dvix)
    p1 = partial(d.curv.to_numpy()[ok], dvix[ok], d.vix_now.to_numpy()[ok])
    p2 = partial(d.curv.to_numpy()[ok], dvix[ok], d.vix_now.to_numpy()[ok], d.rvol.to_numpy()[ok])
    flag = "  <-- signal" if abs(p2) > 0.1 else ""
    print(f"  h={h:2}d: partial(curv, dVIX | VIX) = {p1:+.3f}   (| VIX+rvol) = {p2:+.3f}{flag}")
