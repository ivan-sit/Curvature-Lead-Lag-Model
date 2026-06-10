#!/usr/bin/env python3
"""Round 3: does the DIRECTED graph's unique structure (change, dispersion, leadership
concentration) signal anything correlation can't? 25-yr daily, fixed universe.
Partial-controls for current vol throughout, so we only credit signal BEYOND correlation/vol.
"""
from __future__ import annotations
import networkx as nx, numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.curvature import compute_all_objects, forman_curvatures
from cllm.network import build_lead_lag_graph
WIN, STEP = 63, 21

def partial(x, y, z):
    rx = x - np.polyval(np.polyfit(z, x, 1), z); ry = y - np.polyval(np.polyfit(z, y, 1), z)
    return spearmanr(rx, ry).statistic

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
mkt = R.mean(axis=1); idx = R.index
rows = []
for end in range(WIN, len(R) - STEP, STEP):
    w = R.iloc[end - WIN:end]; cols = list(w.columns)
    A = w.corr().abs().to_numpy(); iu, ju = np.triu_indices(len(cols), 1)
    G = nx.Graph(); G.add_nodes_from(cols)
    for i, j in zip(iu, ju):
        if A[i, j] > 0.5: G.add_edge(cols[i], cols[j])
    fc = list(forman_curvatures(G).values()) if G.number_of_edges() else [np.nan]
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
    outdeg = np.array([d for _, d in GL.out_degree()]) if GL.number_of_nodes() else np.array([0])
    g = np.sort(outdeg); n = len(g)
    gini = (2 * np.arange(1, n + 1) - n - 1).dot(g) / (n * g.sum()) if g.sum() > 0 else np.nan
    rows.append({"date": idx[end], "curv_mean": np.nanmean(fc), "curv_disp": np.nanstd(fc),
                 "lead_gini": gini, "vol_now": float(mkt.iloc[end - WIN:end].std()),
                 "vol_fwd": float(mkt.iloc[end:end + STEP].std()),
                 "dd_fwd": float(((1 + mkt.iloc[end:end + STEP]).cumprod() /
                                  (1 + mkt.iloc[end:end + STEP]).cumprod().cummax() - 1).min())})
df = pd.DataFrame(rows).set_index("date").dropna()
df["dcurv"] = df["curv_mean"].diff()
df = df.dropna()
z = df["vol_now"].to_numpy()
print(f"{len(df)} windows\n")
print("partial Spearman (controls current vol) — only credits signal BEYOND vol/correlation:")
for sig in ["dcurv", "curv_disp", "lead_gini"]:
    pv = partial(df[sig].to_numpy(), df["vol_fwd"].to_numpy(), z)
    pd_ = partial(df[sig].to_numpy(), df["dd_fwd"].to_numpy(), z)
    verd = "PASS" if max(abs(pv), abs(pd_)) > 0.2 else "weak/null"
    print(f"  {sig:11} vs fwd_vol {pv:+.3f}   vs fwd_drawdown {pd_:+.3f}   -> {verd}")
