#!/usr/bin/env python3
"""Decisive structural test: are curvature's cross-sector BRIDGES enriched for REAL
customer-supplier links (comp.wrds_seg_customer) vs correlation pairs vs base rate?
If yes -> curvature recovers economic structure. If no -> its bridges are statistical.
"""
from __future__ import annotations
import re, numpy as np, pandas as pd, networkx as nx
import wrds
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize

def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    s = re.sub(r"\b(INC|CORP|CO|LTD|COMPANY|THE|PLC|GROUP|HOLDINGS|CL A|CL B|SA|NV|AG)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

eps = pd.read_parquet("data/eps_wrds.parquet")[["permno", "gvkey"]].drop_duplicates()
eps["permno"] = eps["permno"].astype(int).astype(str)
uni_g = tuple(eps["gvkey"].unique())
db = wrds.Connection(wrds_username="ivansit1214")
names = db.raw_sql("select gvkey, conm from comp.company where gvkey in %(g)s", params={"g": uni_g})
seg = db.raw_sql("select gvkey, cnms from comp.wrds_seg_customer where gvkey in %(g)s", params={"g": uni_g})
db.close()
uni_norm = {norm(r.conm): r.gvkey for r in names.itertuples() if norm(r.conm)}
g2p = dict(zip(eps["gvkey"], eps["permno"]))
links = set()
for r in seg.itertuples():
    cn = norm(r.cnms)
    if len(cn) < 4: continue
    for un, ug in uni_norm.items():
        if len(un) > 3 and (un in cn or cn in un) and r.gvkey in g2p and ug in g2p:
            links.add(frozenset((g2p[r.gvkey], g2p[ug]))); break
print(f"real customer-supplier pairs within universe: {len(links)}")

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.98]].fillna(0.0)
sec = pd.read_parquet("data/sectors_wrds.parquet")["gsector"].astype(str); sec.index=[str(c) for c in sec.index]
rr = residualize(R, sectors=sec.reindex(R.columns).fillna("OTHER"), method="market_sector")
GL = build_lead_lag_graph(rr, lags=(1,2,3,5), threshold=0.90)
curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"].sort_values()  # most negative first
cross = [(u,v) for (u,v) in curv.index if sec.get(u,"x")!=sec.get(v,"y")]
K = len(links) if links else 50
bridges = [frozenset((u,v)) for (u,v) in cross[:max(K,50)]]
C = R.corr().abs(); allp=list(GL.to_undirected().edges())
corr_top = sorted(allp, key=lambda e: C.loc[e[0],e[1]], reverse=True)[:max(K,50)]
corr_set = [frozenset(e) for e in corr_top]
def rate(pairs): return np.mean([p in links for p in pairs]) if pairs else 0
import itertools
nodes=list(GL.nodes()); allpairs=[frozenset((nodes[i],nodes[j])) for i in range(len(nodes)) for j in range(i+1,len(nodes))]
base = np.mean([p in links for p in allpairs])
print(f"base rate of economic links among all pairs: {base:.4f}")
print(f"economic-link rate among curvature bridges: {rate(bridges):.4f}  (enrichment {rate(bridges)/base if base else 0:.1f}x)")
print(f"economic-link rate among top-correlation pairs: {rate(corr_set):.4f}  (enrichment {rate(corr_set)/base if base else 0:.1f}x)")
