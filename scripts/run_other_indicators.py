#!/usr/bin/env python3
"""Other targets for curvature (25-yr daily, fixed universe). Partial-controls throughout.
Targets: future market RETURN (timing), future TAIL RISK (skew/kurt), future CONTAGION (corr level).
"""
from __future__ import annotations
import networkx as nx, numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.curvature import forman_curvatures
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
    curv = float(np.mean(list(forman_curvatures(G).values()))) if G.number_of_edges() else np.nan
    fwd = mkt.iloc[end:end + STEP]; nxtw = R.iloc[end:end + STEP]
    An = nxtw.corr().abs().to_numpy()
    rows.append({"curv": curv, "vol_now": float(mkt.iloc[end - WIN:end].std()),
                 "corr_now": float(A[iu, ju].mean()),
                 "fwd_ret": float((1 + fwd).prod() - 1), "fwd_skew": float(fwd.skew()),
                 "fwd_kurt": float(fwd.kurt()), "fwd_corr": float(An[iu, ju].mean())})
df = pd.DataFrame(rows).dropna(); z = df["vol_now"].to_numpy()
print(f"{len(df)} windows\n")
print("partial Spearman of curvature vs target (controlling current vol):")
for t in ["fwd_ret", "fwd_skew", "fwd_kurt"]:
    p = partial(df["curv"].to_numpy(), df[t].to_numpy(), z)
    print(f"  curv vs {t:9} = {p:+.3f}   -> {'PASS' if abs(p)>0.2 else 'weak/null'}")
# contagion: control CURRENT corr level (autocorr), not vol
pc = partial(df["curv"].to_numpy(), df["fwd_corr"].to_numpy(), df["corr_now"].to_numpy())
print(f"  curv vs fwd_corr (| corr_now) = {pc:+.3f}   -> {'PASS' if abs(pc)>0.2 else 'weak/null'}")
