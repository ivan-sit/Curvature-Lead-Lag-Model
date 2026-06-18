#!/usr/bin/env python3
"""Clean retest with RESOLVED supply-chain links (wrdsapps_link_supplychain.seglink: gvkey->cgvkey,
no fuzzy name matching). Does the curvature-bridge enrichment hold with clean links, and does it
replicate across large-cap and small/mid-cap?
"""
from __future__ import annotations
import numpy as np, pandas as pd, networkx as nx, wrds
from scipy.stats import hypergeom
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize

db = wrds.Connection(wrds_username="ivansit1214")

def clean_links(R):
    permnos = tuple(int(c) for c in R.columns)
    ccm = db.raw_sql("""select distinct lpermno as permno, gvkey from crsp.ccmxpf_linktable
        where lpermno in %(p)s and linktype in ('LU','LC') and linkprim in ('P','C')""", params={"p": permnos})
    g2p = {r.gvkey: str(int(r.permno)) for r in ccm.itertuples()}
    ug = tuple(set(g2p.keys()))
    seg = db.raw_sql("""select distinct gvkey, cgvkey from wrdsapps_link_supplychain.seglink
        where gvkey in %(g)s and cgvkey is not null and cgvkey in %(g)s""", params={"g": ug})
    links = set()
    for r in seg.itertuples():
        a, b = g2p.get(r.gvkey), g2p.get(r.cgvkey)
        if a and b and a != b: links.add(frozenset((a, b)))
    return links

def enrich(name, path, sectorpath, thr):
    R = pd.read_parquet(path)
    R = R.loc[:, R.notna().mean() >= (0.98 if "smallcap" not in path else 0.7)].fillna(0.0)
    sec = pd.read_parquet(sectorpath)["gsector"].astype(str); sec.index = [str(c) for c in sec.index]
    links = clean_links(R)
    GL = build_lead_lag_graph(residualize(R, method="market"), lags=(1,2,3,5), threshold=thr)
    curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"].sort_values()
    cross = [(u,v) for (u,v) in curv.index if sec.get(u,"x")!=sec.get(v,"y")]
    nodes=list(GL.nodes()); M=len(nodes)*(len(nodes)-1)//2; n=len(links)
    C=R.corr().abs()
    print(f"\n=== {name}: {R.shape[1]} names, {n} CLEAN resolved links ===")
    for K in [300,500,1000]:
        bs=[frozenset(e) for e in cross[:K]]; h=sum(p in links for p in bs); e=K*n/M
        print(f"   curvature top-{K}: {h} links (exp {e:.1f}) {h/e if e else 0:.1f}x  p={hypergeom.sf(h-1,M,n,K):.3g}")
    cp=sorted(GL.to_undirected().edges(), key=lambda x:C.loc[x[0],x[1]], reverse=True)[:300]
    hc=sum(frozenset(e) in links for e in cp); ec=300*n/M
    print(f"   correlation top-300: {hc} links (exp {ec:.1f}) {hc/ec if ec else 0:.1f}x")

enrich("LARGE-CAP (S&P500)", "data/returns_wrds.parquet", "data/sectors_wrds.parquet", 0.90)
enrich("SMALL/MID-CAP", "data/returns_smallcap.parquet", "data/sectors_smallcap.parquet", 0.95)
db.close()
