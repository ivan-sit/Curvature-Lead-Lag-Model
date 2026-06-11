#!/usr/bin/env python3
"""Strengthen the positive result: bigger universe, significance test, and the alpha path
(does economic-link momentum show up on curvature-VALIDATED bridges?).
"""
from __future__ import annotations
import re, numpy as np, pandas as pd
import wrds
from scipy.stats import hypergeom
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize

def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    s = re.sub(r"\b(INC|CORP|CO|LTD|COMPANY|THE|PLC|GROUP|HOLDINGS|CL A|CL B|SA|NV|AG|LLC)\b"," ",s)
    return re.sub(r"\s+", " ", s).strip()

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.90]].fillna(0.0)   # broader universe
permnos = tuple(int(c) for c in R.columns)
db = wrds.Connection(wrds_username="ivansit1214")
link = db.raw_sql("""select distinct l.lpermno as permno, c.gvkey, c.conm from comp.company c
  join crsp.ccmxpf_linktable l on c.gvkey=l.gvkey and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
  where l.lpermno in %(p)s""", params={"p": permnos})
g2p = {r.gvkey: str(int(r.permno)) for r in link.itertuples()}
uni_norm = {norm(r.conm): str(int(r.permno)) for r in link.itertuples() if norm(r.conm)}
seg = db.raw_sql("select gvkey, cnms from comp.wrds_seg_customer where gvkey in %(g)s",
                 params={"g": tuple(g2p.keys())})
db.close()
links = set()
for r in seg.itertuples():
    cn = norm(r.cnms)
    if len(cn) < 4 or r.gvkey not in g2p: continue
    for un, up in uni_norm.items():
        if len(un) > 3 and (un in cn or cn in un) and g2p[r.gvkey] != up:
            links.add(frozenset((g2p[r.gvkey], up))); break
print(f"universe {R.shape[1]} names; real customer-supplier pairs found: {len(links)}")

rr = residualize(R, method="market")
GL = build_lead_lag_graph(rr, lags=(1,2,3,5), threshold=0.92)
curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"].sort_values()
edges = list(curv.index)
nodes = list(GL.nodes()); npairs = len(nodes)*(len(nodes)-1)//2
M, n = npairs, len(links)                       # population, successes
for label, K in [("top-100 bridges",100),("top-300 bridges",300),("top-500 bridges",500)]:
    bs = [frozenset(e) for e in edges[:K]]
    hits = sum(p in links for p in bs)
    exp = K * n / M
    p = hypergeom.sf(hits-1, M, n, K)
    print(f"  {label}: {hits} economic links (expected {exp:.1f})  enrichment {hits/exp if exp else 0:.1f}x  p={p:.3g}")
