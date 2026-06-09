#!/usr/bin/env python3
"""Walk-forward out-of-sample directional IC on DAILY close-to-close returns,
across the full 2000-2024 CRSP span (answers: "why only one year?").

Each window: ~3y train + ~1y test, stepped 1y. Per window we residualize the
train, build the directed lead-lag graph, select pairs by curvature (augmented
directed) / undirected Forman / correlation / random, and measure the test-window
directional IC (close-to-close, cross-period, tau in 1-5 trading days). We report
the IC per method per window and aggregated across windows.

This is the DAILY companion to the intraday-2019 headline; daily lead-lag is weak,
so the expected story is a flat/near-zero IC across all years — i.e. the H2 null
is stable over 25 years, not a one-year artifact.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from cllm.curvature import compute_all_objects, forman_curvatures
from cllm.evaluation import (
    directional_ic,
    select_by_correlation,
    select_random,
    select_top_edges,
)
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize
from cllm.validation import (
    residual_orthogonalization,
    spearman_curvature_vs_corr,
    topk_jaccard,
    train_val_test_split,
)

LAGS = (1, 2, 3, 5)
K = 20
WIN, STEP = 1008, 252      # ~4y window (3.2y train / 0.8y test), step ~1y
THRESH = 0.90


def main() -> None:
    t0 = time.time()
    rets = pd.read_parquet("data/returns_wrds.parquet")
    sec = pd.read_parquet("data/sectors_wrds.parquet")["gsector"].astype(str)
    print(f"daily panel {rets.shape}, {rets.index.min().date()}..{rets.index.max().date()}")

    rows = []
    for s0 in range(0, len(rets) - WIN + 1, STEP):
        sub = rets.iloc[s0:s0 + WIN]
        sub = sub.loc[:, sub.notna().all()]          # names present the whole window
        if sub.shape[1] < 50:
            continue
        secs = sec.reindex(sub.columns).fillna("OTHER")
        tr, va, te = train_val_test_split(len(sub), (0.6, 0.2, 0.2))
        r_train = sub.iloc[np.concatenate([tr, va])].reset_index(drop=True)
        r_test = sub.iloc[te].reset_index(drop=True)
        r_res = residualize(r_train, sectors=secs, method="market_sector")
        G = build_lead_lag_graph(r_res, lags=LAGS, threshold=THRESH)
        if G.number_of_edges() < 10:
            continue

        curv = compute_all_objects(G, triangle_mode="common", with_ollivier=False)
        curv = curv.assign(lag=[G[u][v]["lag"] for u, v in curv.index])
        cpairs = select_top_edges(curv, "F_augmented", K, ascending=True)
        und = pd.DataFrame({"F_und": forman_curvatures(G.to_undirected())})
        und["lag"] = [G[u][v]["lag"] if G.has_edge(u, v) else G[v][u]["lag"] for u, v in und.index]
        upairs = select_top_edges(und, "F_und", K, ascending=True)

        tk = list(sub.columns)
        cands = [(tk[i], tk[j]) for i in range(len(tk)) for j in range(i + 1, len(tk))]
        corr = select_by_correlation(r_train, cands, K, LAGS)
        rnd = select_random(cands, K, r_train, LAGS, seed=0)

        # structural cascade (same metrics as the intraday run)
        C = r_res.corr().abs()
        abs_corr = pd.Series({(u, v): C.loc[u, v] for u, v in G.edges()})
        spearman = spearman_curvature_vs_corr(curv["F_augmented"], abs_corr)
        jacc = topk_jaccard(curv["F_augmented"], -abs_corr, k=K)
        feats = pd.DataFrame({
            "deg_in": {(u, v): G.in_degree(u) for u, v in G.edges()},
            "deg_out": {(u, v): G.out_degree(v) for u, v in G.edges()},
            "abs_rho": abs_corr,
        })
        r2_plain = residual_orthogonalization(curv["F_plain"], feats[["deg_in", "deg_out"]]).r_squared
        r2_aug = residual_orthogonalization(curv["F_augmented"], feats).r_squared

        yr0, yr1 = rets.index[s0].year, rets.index[min(s0 + WIN - 1, len(rets) - 1)].year
        rows.append({
            "window": f"{yr0}-{yr1}", "names": sub.shape[1], "edges": G.number_of_edges(),
            "curv(aug,dir)": directional_ic(r_train, r_test, cpairs).mean_ic,
            "undirected": directional_ic(r_train, r_test, upairs).mean_ic,
            "correlation": directional_ic(r_train, r_test, corr).mean_ic,
            "random": directional_ic(r_train, r_test, rnd).mean_ic,
            "spearman": spearman, "jaccard": jacc, "R2_plain": r2_plain, "R2_aug": r2_aug,
        })
        print("  ", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rows[-1].items()})

    df = pd.DataFrame(rows).set_index("window")
    methods = ["curv(aug,dir)", "undirected", "correlation", "random"]
    print("\n=== per-window IC ===")
    print(df[methods].round(4).to_string())
    print(f"\n=== aggregated across {len(df)} windows (2000-2024 daily, close-to-close) ===")
    summ = pd.DataFrame({
        "mean_IC": df[methods].mean(),
        "std": df[methods].std(),
        "ci_low": df[methods].mean() - 1.96 * df[methods].std() / np.sqrt(len(df)),
        "ci_high": df[methods].mean() + 1.96 * df[methods].std() / np.sqrt(len(df)),
        "frac_windows>0": (df[methods] > 0).mean(),
    })
    print(summ.round(4).to_string())

    casc = ["spearman", "jaccard", "R2_plain", "R2_aug"]
    print("\n=== structural cascade, averaged across windows (2000-2024 daily) ===")
    print(df[casc].mean().round(4).to_string())
    print(f"\nDONE in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
