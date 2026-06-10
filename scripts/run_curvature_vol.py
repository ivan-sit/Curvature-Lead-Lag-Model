#!/usr/bin/env python3
"""Does aggregate curvature track / lead market VOLATILITY? (25-yr daily, fixed universe)

Literature (Samal et al., R.Soc.Open Sci.; Sandhu et al.): aggregate Forman-Ricci
curvature on undirected CORRELATION networks tracks market fragility/volatility and
predicts VIX increases. H2 (returns) was the wrong target — risk is the right one.

We test, over 2000-2024 daily on a fixed (high-presence) universe, with trailing
63-day windows stepped 21 days:
  curv_corr = mean Forman curvature on the |corr|>0.5 graph   (literature baseline)
  curv_ll   = mean weighted Forman on the directed lead-lag graph  (our object)
vs market realized volatility — contemporaneous (track) and forward (lead).
"""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from cllm.curvature import compute_all_objects, forman_curvatures
from cllm.network import build_lead_lag_graph

WIN, STEP = 63, 21


def main() -> None:
    rets = pd.read_parquet("data/returns_wrds.parquet")
    keep = rets.columns[rets.notna().mean() >= 0.98]      # fixed high-presence universe
    R = rets[keep].fillna(0.0)
    mkt = R.mean(axis=1)
    idx = R.index
    print(f"fixed universe: {R.shape[1]} names, {R.shape[0]} days "
          f"({idx.min().date()}..{idx.max().date()})")

    rows = []
    for end in range(WIN, len(R) - STEP, STEP):
        w = R.iloc[end - WIN:end]
        cols = list(w.columns)
        A = w.corr().abs().to_numpy()
        iu, ju = np.triu_indices(len(cols), 1)
        G = nx.Graph()
        G.add_nodes_from(cols)
        for i, j in zip(iu, ju):
            if A[i, j] > 0.5:
                G.add_edge(cols[i], cols[j])
        curv_corr = float(np.mean(list(forman_curvatures(G).values()))) if G.number_of_edges() else np.nan
        GL = build_lead_lag_graph(w, lags=(1, 2, 3, 5), threshold=0.90)
        cl = compute_all_objects(GL, with_ollivier=False)["F_weighted"]
        curv_ll = float(cl.mean()) if len(cl) else np.nan
        rows.append({"date": idx[end],
                     "curv_corr": curv_corr, "dens": G.number_of_edges(),
                     "mean_corr": float(A[iu, ju].mean()), "curv_ll": curv_ll,
                     "vol_now": float(mkt.iloc[end - WIN:end].std()),
                     "vol_fwd": float(mkt.iloc[end:end + STEP].std())})
    df = pd.DataFrame(rows).set_index("date").dropna()
    print(f"{len(df)} windows\n")

    print("Spearman correlation with market volatility:")
    print(f"{'signal':12} {'vs vol_now':>11} {'vs vol_fwd':>11}")
    for col in ["curv_corr", "dens", "mean_corr", "curv_ll"]:
        rc = spearmanr(df[col], df["vol_now"]).statistic
        rf = spearmanr(df[col], df["vol_fwd"]).statistic
        print(f"{col:12} {rc:>11.2f} {rf:>11.2f}")

    # lead test: does curvature predict FORWARD vol beyond CURRENT vol?
    print("\nLead test — partial Spearman of curv vs vol_fwd, controlling vol_now:")
    from numpy.polynomial import polynomial as P  # noqa
    def partial(x, y, z):
        # residualize x and y on z (linear), correlate residuals
        bx = np.polyfit(z, x, 1); by = np.polyfit(z, y, 1)
        rx = x - np.polyval(bx, z); ry = y - np.polyval(by, z)
        return spearmanr(rx, ry).statistic
    z = df["vol_now"].to_numpy()
    for col in ["curv_corr", "curv_ll"]:
        pr = partial(df[col].to_numpy(), df["vol_fwd"].to_numpy(), z)
        print(f"  {col:12} partial corr with vol_fwd | vol_now = {pr:.3f}")


if __name__ == "__main__":
    main()
