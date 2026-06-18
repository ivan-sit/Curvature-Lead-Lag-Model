#!/usr/bin/env python3
"""Extend Sandhu 2016 properly: RAW returns (don't residualize away the systemic signal).
Does the DIRECTED lead-lag curvature add to / LEAD the undirected correlation curvature
(earlier systemic-risk warning)? Weekly, 25-yr daily, fixed universe.
"""
from __future__ import annotations
import networkx as nx, numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.curvature import compute_all_objects, forman_curvatures
from cllm.network import build_lead_lag_graph
WIN, STEP = 63, 5
rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)   # RAW (not residualized)
mkt = R.mean(axis=1); idx = R.index
recs = []
for end in range(WIN, len(R) - STEP, STEP):
    w = R.iloc[end - WIN:end]; cols = list(w.columns)
    A = w.corr().abs().to_numpy(); iu, ju = np.triu_indices(len(cols), 1)
    G = nx.Graph(); G.add_nodes_from(cols)
    for i, j in zip(iu, ju):
        if A[i, j] > 0.5: G.add_edge(cols[i], cols[j])
    cu = float(np.mean(list(forman_curvatures(G).values()))) if G.number_of_edges() else np.nan
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)   # raw lead-lag
    cd = float(compute_all_objects(GL, with_ollivier=False)["F_weighted"].mean()) if GL.number_of_edges() else np.nan
    recs.append({"pos": end - 1, "cu": cu, "cd": cd, "vol": float(mkt.iloc[end - WIN:end].std())})
d = pd.DataFrame(recs).dropna().reset_index(drop=True)
mktv = mkt.to_numpy()
def partial(x, y, *c):
    Z = np.column_stack([np.ones_like(x)] + list(c))
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]; ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return spearmanr(rx, ry).statistic
print(f"{len(d)} weekly windows (RAW)\n")
print(f"contemporaneous tracking of volatility:  undirected curv {spearmanr(d.cu,d.vol).statistic:+.2f}"
      f"   directed curv {spearmanr(d.cd,d.vol).statistic:+.2f}")
# does directed curvature LEAD undirected curvature?  (cu_{t+h} vs cd_t, control cu_t)
print("\nDoes DIRECTED curvature LEAD UNDIRECTED curvature (earlier warning)?")
for h in [1,2,4]:
    cd_t=d.cd.to_numpy()[:-h]; cu_fut=d.cu.to_numpy()[h:]; cu_t=d.cu.to_numpy()[:-h]
    print(f"   h={h}w: partial(cd_t, cu_future | cu_now) = {partial(cd_t, cu_fut, cu_t):+.3f}")
# does directed lead FORWARD vol beyond current vol AND undirected curv?
print("\nDoes DIRECTED curvature predict FORWARD vol, beyond vol_now + undirected curv?")
pos=d.pos.to_numpy()
for h in [1,2,4]:
    fv=mktv[np.minimum(pos+h*STEP,len(mktv)-1)]
    print(f"   h={h}w: partial(cd, fwd_vol | vol_now, cu) = {partial(d.cd.to_numpy(), fv, d.vol.to_numpy(), d.cu.to_numpy()):+.3f}")
