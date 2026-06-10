#!/usr/bin/env python3
"""Regime preview: is curvature on the directed lead-lag graph a fragility signal?

For each regime year (2008 GFC, 2015 calm, 2019 calm, 2020 COVID), split into months;
per month build the directed lead-lag graph on RAW intraday returns (NOT residualized —
the systemic co-movement that spikes in a crash is what residualization removes, so the
fragility lens keeps it), and report two network-wide aggregates:

  coupling = mean |BCR lead-lag| over all pairs   (directed coupling intensity)
  meanF    = mean weighted Forman curvature        (Sandhu-style aggregate curvature)

Then compare crisis months (2008-09..12, 2020-02..04) to calm months.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph, signed_lead_lag

FILES = {2008: "data/taq_intraday_2008.parquet", 2015: "data/taq_intraday_2015.parquet",
         2019: "data/taq_intraday_2019.parquet", 2020: "data/taq_intraday_2020.parquet"}
CRISIS = {(2008, 9), (2008, 10), (2008, 11), (2008, 12), (2020, 2), (2020, 3), (2020, 4)}


def main() -> None:
    rows = []
    for yr, f in FILES.items():
        rets = pd.read_parquet(f).dropna(axis=1, how="all").fillna(0.0)
        for m, sub in rets.groupby(rets.index.month):
            if sub.shape[0] < 60 or sub.shape[1] < 30:
                continue
            groups = sub.index.normalize().to_numpy()
            est = signed_lead_lag(sub, lags=(1, 2, 3), groups=groups)
            N = est.W.shape[0]
            iu, ju = np.triu_indices(N, 1)
            coupling = float(np.mean(np.abs(est.W[iu, ju])))
            G = build_lead_lag_graph(sub, lags=(1, 2, 3), threshold=0.90, groups=groups)
            meanF = float(compute_all_objects(G, with_ollivier=False)["F_weighted"].mean()) \
                if G.number_of_edges() else float("nan")
            rows.append({"year": yr, "month": m, "names": sub.shape[1],
                         "coupling": coupling, "meanF": meanF,
                         "crisis": (yr, m) in CRISIS})
    df = pd.DataFrame(rows)

    print("=== monthly network coupling & curvature (raw lead-lag) ===")
    for yr in FILES:
        d = df[df.year == yr]
        s = "  ".join(f"{int(r.month):02d}:{r.coupling:.3f}{'*' if r.crisis else ' '}"
                      for r in d.itertuples())
        print(f"{yr} coupling  {s}")
    print()
    cri, calm = df[df.crisis], df[~df.crisis]
    print(f"coupling  — crisis months: {cri.coupling.mean():.4f}   calm months: {calm.coupling.mean():.4f}"
          f"   ratio: {cri.coupling.mean() / calm.coupling.mean():.2f}x")
    print(f"meanF     — crisis months: {cri.meanF.mean():.3f}    calm months: {calm.meanF.mean():.3f}")
    print(f"\ncrisis n={len(cri)}, calm n={len(calm)}")


if __name__ == "__main__":
    main()
