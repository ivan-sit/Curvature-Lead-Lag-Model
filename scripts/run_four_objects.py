#!/usr/bin/env python3
"""Head-to-head comparison of the FOUR curvature objects (the ablation spine).

For each object — plain directed Forman (degree baseline), weighted Forman,
weighted-augmented directed Forman (main), Ollivier-Ricci — report the structural
cascade (Spearman vs |rho|, top-K Jaccard vs correlation, R^2 on degree), the
out-of-sample directional IC of its selected pairs, and the compute time. Answers:
"which object is best, and which is most efficient?"

Runs on the intraday 2019 panel.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from cllm.curvature import compute_all_objects
from cllm.evaluation import directional_ic, select_top_edges
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize
from cllm.validation import (
    residual_orthogonalization,
    spearman_curvature_vs_corr,
    topk_jaccard,
    train_val_test_split,
)

OBJECTS = [
    ("F_plain", "plain directed Forman (degree baseline)"),
    ("F_weighted", "weighted Forman"),
    ("F_augmented", "weighted augmented directed (MAIN)"),
    ("ollivier", "Ollivier-Ricci"),
]
K = 20


def main() -> None:
    rets = pd.read_parquet("data/taq_intraday_2019.parquet").dropna(axis=1, how="all").fillna(0.0)
    sec = pd.read_parquet("data/ticker_sectors_wrds.parquet")["gsector"].astype(str)
    sec = sec.reindex(rets.columns).fillna("OTHER")
    idx = rets.index

    tr, va, te = train_val_test_split(len(rets), (0.6, 0.2, 0.2))
    trva = np.concatenate([tr, va])
    r_train = rets.iloc[trva].reset_index(drop=True)
    r_test = rets.iloc[te].reset_index(drop=True)
    g_train = idx[trva].normalize().to_numpy()
    g_test = idx[te].normalize().to_numpy()

    r_res = residualize(r_train, sectors=sec, method="market_sector")
    G = build_lead_lag_graph(r_res, lags=(1, 2, 3), threshold=0.90, groups=g_train)
    print(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    t0 = time.time()
    curv = compute_all_objects(G, triangle_mode="common", with_ollivier=True)
    t_all = time.time() - t0

    # per-object compute time (Forman objects share one pass; Ollivier is the LP cost)
    t1 = time.time(); compute_all_objects(G, triangle_mode="common", with_ollivier=False)
    t_forman = time.time() - t1
    t_ollivier = max(t_all - t_forman, 0.0)

    C = r_res.corr().abs()
    abs_corr = pd.Series({(u, v): C.loc[u, v] for u, v in G.edges()})
    feats = pd.DataFrame({
        "deg_in": {(u, v): G.in_degree(u) for u, v in G.edges()},
        "deg_out": {(u, v): G.out_degree(v) for u, v in G.edges()},
        "abs_rho": abs_corr,
    })

    rows = []
    for col, label in OBJECTS:
        s = curv[col]
        if s.isna().all():
            continue
        spear = spearman_curvature_vs_corr(s, abs_corr)
        jacc = topk_jaccard(s, -abs_corr, k=K)
        r2 = residual_orthogonalization(s, feats).r_squared
        cdf = curv.assign(lag=[G[u][v]["lag"] for u, v in curv.index])
        pairs = select_top_edges(cdf, col, K, ascending=True)
        ic = directional_ic(r_train, r_test, pairs, groups=g_test).mean_ic
        cost = t_forman if col != "ollivier" else t_forman + t_ollivier
        rows.append({"object": label, "spearman": spear, "jaccard": jacc,
                     "R2_deg": r2, "IC": ic, "sec": cost})

    df = pd.DataFrame(rows).set_index("object")
    print(df.round(3).to_string())
    print(f"\nForman pass (3 objects): {t_forman:.2f}s   |   Ollivier (per-edge OT LP): {t_ollivier:.2f}s")
    print(f"=> Ollivier is ~{t_ollivier / max(t_forman,1e-6):.0f}x the cost of the entire Forman family")


if __name__ == "__main__":
    main()
