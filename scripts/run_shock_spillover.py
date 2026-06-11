#!/usr/bin/env python3
"""Structure-dependent test: does a SHOCK propagate along DIRECTED edges, beyond correlation?
When source s takes a big idiosyncratic move at t, does lagger j respond at t+1 in the
lead-lag-predicted direction? Compare directed-edge IC on ALL days vs SHOCK days, and vs a
correlation-based forecast. Propagation follows paths (topology), not covariance.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from cllm.network import build_lead_lag_graph
LOOK, STEP = 252, 21
rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
resid = R.sub(R.mean(axis=1), axis=0)          # market-residualized (remove equal-wt market)
cols = list(resid.columns); ci = {c: i for i, c in enumerate(cols)}
R_np = resid.to_numpy()
all_f, all_r, all_shock = [], [], []
cf, cr = [], []                                # correlation-baseline forecast/realized
for end in range(LOOK, len(R) - STEP, STEP):
    w = resid.iloc[end - LOOK:end]
    GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
    if GL.number_of_edges() < 50: continue
    sd = w.std().to_numpy()
    F = R_np[end:end + STEP]                    # forward residual returns (STEP x N)
    for u, v, d in GL.edges(data=True):
        si, ti = ci[u], ci[v]; sg = np.sign(d["signed"])
        src = F[:-1, si]; tgt = F[1:, ti]
        fore = sg * src
        all_f.append(fore); all_r.append(tgt)
        all_shock.append(np.abs(src) > 2 * sd[si])
    # correlation baseline: undirected, contemporaneous-corr sign
    C = w.corr().to_numpy()
    for u, v in GL.to_undirected().edges():
        si, ti = ci[u], ci[v]; sg = np.sign(C[si, ti])
        cf.append(sg * F[:-1, si]); cr.append(F[1:, ti])
af, ar, ash = np.concatenate(all_f), np.concatenate(all_r), np.concatenate(all_shock)
ic_all = spearmanr(af, ar).statistic
ic_shock = spearmanr(af[ash], ar[ash]).statistic
cfa, cra = np.concatenate(cf), np.concatenate(cr)
ic_corr = spearmanr(cfa, cra).statistic
print(f"directed-edge spillover IC:  all days {ic_all:+.4f}   SHOCK days {ic_shock:+.4f}  (n_shock={ash.sum()})")
print(f"correlation-edge IC (all):   {ic_corr:+.4f}")
print(f"VERDICT: {'PASS' if ic_shock > 0.05 and ic_shock > ic_all + 0.03 else 'weak/null'}")
