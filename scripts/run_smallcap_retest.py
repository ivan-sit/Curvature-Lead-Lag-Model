#!/usr/bin/env python3
"""Small-cap retest: (A) does the supply-chain ENRICHMENT strengthen, and (B) does the
link-momentum ALPHA open up where Cohen-Frazzini actually lives (under-covered firms)?
"""
from __future__ import annotations
import re, numpy as np, pandas as pd, wrds
from collections import defaultdict
from scipy.stats import hypergeom
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize
LOOK, STEP = 252, 21

def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    s = re.sub(r"\b(INC|CORP|CO|LTD|COMPANY|THE|PLC|GROUP|HOLDINGS|CL A|CL B|SA|NV|AG|LLC)\b"," ",s)
    return re.sub(r"\s+", " ", s).strip()

R = pd.read_parquet("data/returns_smallcap.parquet")
R = R.loc[:, R.notna().mean() >= 0.7].fillna(0.0)
sec = pd.read_parquet("data/sectors_smallcap.parquet")["gsector"].astype(str)
permnos = tuple(int(c) for c in R.columns)
db = wrds.Connection(wrds_username="ivansit1214")
link = db.raw_sql("""select distinct l.lpermno as permno, c.gvkey, c.conm from comp.company c
  join crsp.ccmxpf_linktable l on c.gvkey=l.gvkey and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
  where l.lpermno in %(p)s""", params={"p": permnos})
g2p = {r.gvkey: str(int(r.permno)) for r in link.itertuples()}
uni_norm = {norm(r.conm): str(int(r.permno)) for r in link.itertuples() if norm(r.conm)}
seg = db.raw_sql("select gvkey, cnms from comp.wrds_seg_customer where gvkey in %(g)s", params={"g": tuple(g2p.keys())})
db.close()
links = set(); sup2cust = defaultdict(set)
for r in seg.itertuples():
    cn = norm(r.cnms)
    if len(cn) < 4 or r.gvkey not in g2p: continue
    for un, up in uni_norm.items():
        if len(un) > 3 and (un in cn or cn in un) and g2p[r.gvkey] != up:
            links.add(frozenset((g2p[r.gvkey], up))); sup2cust[g2p[r.gvkey]].add(up); break
print(f"universe {R.shape[1]} names; real customer-supplier pairs: {len(links)}")

# (A) enrichment on a full-period graph
rr = residualize(R, method="market")
GL0 = build_lead_lag_graph(rr, lags=(1,2,3,5), threshold=0.95)
curv0 = compute_all_objects(GL0, with_ollivier=False)["F_augmented"].sort_values()
cross0 = [(u,v) for (u,v) in curv0.index if sec.get(u,"x")!=sec.get(v,"y")]
nodes=list(GL0.nodes()); M=len(nodes)*(len(nodes)-1)//2; n=len(links)
print("\n(A) ENRICHMENT:")
for K in [300, 500, 1000]:
    bs=[frozenset(e) for e in cross0[:K]]; h=sum(p in links for p in bs); e=K*n/M
    print(f"   top-{K}: {h} links (exp {e:.1f}) {h/e if e else 0:.1f}x  p={hypergeom.sf(h-1,M,n,K):.3g}")

# (B) link momentum
def ls(sig, end):
    s=pd.Series(sig).dropna().sort_values()
    if len(s)<10: return np.nan
    q=max(len(s)//5,3); fwd=(1+R.iloc[end:end+STEP]).prod()-1
    return float(fwd[list(s.index[-q:])].mean()-fwd[list(s.index[:q])].mean())
real,brg=[],[]
for end in range(LOOK,len(R)-STEP,STEP):
    last=(1+R.iloc[end-STEP:end]).prod()-1
    real.append(ls({s:np.mean([last.get(c,0) for c in cs]) for s,cs in sup2cust.items() if cs and s in R.columns}, end))
    GL=build_lead_lag_graph(residualize(R.iloc[end-LOOK:end],method="market"),lags=(1,2,3,5),threshold=0.95)
    if GL.number_of_edges()<50: brg.append(np.nan); continue
    cv=compute_all_objects(GL,with_ollivier=False)["F_augmented"].sort_values()
    cr=[(u,v) for (u,v) in cv.index if sec.get(u,"x")!=sec.get(v,"y")]
    d=defaultdict(list)
    for u,v in cr[:300]: d[v].append(np.sign(GL[u][v]["signed"])*last.get(u,0))
    brg.append(ls({k:np.mean(x) for k,x in d.items() if x}, end))
def rep(name,x):
    x=np.array([v for v in x if np.isfinite(v)]); m=x.mean(); t=m/(x.std()/np.sqrt(len(x)))
    print(f"   {name}: {m*12*100:+.1f}%/yr  Sharpe {m/x.std()*np.sqrt(12):+.2f}  t={t:+.2f} (n={len(x)}) -> {'SIGNAL' if abs(t)>2 else 'weak/null'}")
print("\n(B) LINK MOMENTUM:")
rep("REAL customer-supplier links", real)
rep("curvature-discovered bridges ", brg)
