#!/usr/bin/env python3
"""Alpha path: economic-link momentum (Cohen-Frazzini) on
  (1) REAL customer-supplier links  [control: does it replicate in our universe?]
  (2) curvature-discovered BRIDGES   [does the discovered proxy capture it?]
  (3) ALL cross-sector lead-lag edges [baseline / earlier null]
Monthly, equal-weight long-short, RAW returns.
"""
from __future__ import annotations
import re, numpy as np, pandas as pd
import wrds
from collections import defaultdict
from cllm.curvature import compute_all_objects
from cllm.network import build_lead_lag_graph
from cllm.residualize import residualize
LOOK, STEP = 252, 21

def norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    s = re.sub(r"\b(INC|CORP|CO|LTD|COMPANY|THE|PLC|GROUP|HOLDINGS|CL A|CL B|SA|NV|AG|LLC)\b"," ",s)
    return re.sub(r"\s+", " ", s).strip()

rets = pd.read_parquet("data/returns_wrds.parquet")
R = rets[rets.columns[rets.notna().mean() >= 0.90]].fillna(0.0)
permnos = tuple(int(c) for c in R.columns)
db = wrds.Connection(wrds_username="ivansit1214")
link = db.raw_sql("""select distinct l.lpermno as permno, c.gvkey, c.conm from comp.company c
  join crsp.ccmxpf_linktable l on c.gvkey=l.gvkey and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
  where l.lpermno in %(p)s""", params={"p": permnos})
g2p = {r.gvkey: str(int(r.permno)) for r in link.itertuples()}
uni_norm = {norm(r.conm): str(int(r.permno)) for r in link.itertuples() if norm(r.conm)}
seg = db.raw_sql("select gvkey, cnms from comp.wrds_seg_customer where gvkey in %(g)s", params={"g": tuple(g2p.keys())})
db.close()
# real links: supplier permno -> set of customer permnos (customer return predicts supplier)
sup2cust = defaultdict(set)
for r in seg.itertuples():
    cn = norm(r.cnms)
    if len(cn) < 4 or r.gvkey not in g2p: continue
    for un, up in uni_norm.items():
        if len(un) > 3 and (un in cn or cn in un) and g2p[r.gvkey] != up:
            sup2cust[g2p[r.gvkey]].add(up); break
print(f"universe {R.shape[1]}; suppliers with in-universe customers: {len(sup2cust)}")

def ls(sig, end):
    s = pd.Series(sig).dropna().sort_values()
    if len(s) < 10: return np.nan
    q = max(len(s)//5, 3)
    fwd = (1+R.iloc[end:end+STEP]).prod()-1
    return float(fwd[list(s.index[-q:])].mean() - fwd[list(s.index[:q])].mean())

real, brg, alle = [], [], []
for end in range(LOOK, len(R)-STEP, STEP):
    last = (1+R.iloc[end-STEP:end]).prod()-1
    # (1) real links
    real.append(ls({s: np.mean([last.get(c,0) for c in cs]) for s,cs in sup2cust.items() if cs and s in R.columns}, end))
    # network for (2),(3)
    GL = build_lead_lag_graph(residualize(R.iloc[end-LOOK:end], method="market"), lags=(1,2,3,5), threshold=0.92)
    if GL.number_of_edges()<50: brg.append(np.nan); alle.append(np.nan); continue
    sec = pd.read_parquet("data/sectors_wrds.parquet")["gsector"].astype(str); sec.index=[str(c) for c in sec.index]
    curv = compute_all_objects(GL, with_ollivier=False)["F_augmented"].sort_values()
    cross = [(u,v) for (u,v) in curv.index if sec.get(u,"x")!=sec.get(v,"y")]
    def momsig(edges):
        d=defaultdict(list)
        for u,v in edges:
            w = GL[u][v]["signed"]; d[v].append(np.sign(w)*last.get(u,0))
        return {k:np.mean(x) for k,x in d.items() if x}
    brg.append(ls(momsig(cross[:300]), end))
    alle.append(ls(momsig(cross), end))
def rep(name,x):
    x=np.array([v for v in x if np.isfinite(v)]); m=x.mean(); t=m/(x.std()/np.sqrt(len(x)))
    print(f"{name}: monthly {m*100:+.3f}%  ann {m*12*100:+.1f}%  Sharpe {m/x.std()*np.sqrt(12):+.2f}  t={t:+.2f}  (n={len(x)}) -> {'SIGNAL' if abs(t)>2 else 'weak/null'}")
print()
rep("(1) REAL customer-supplier links ", real)
rep("(2) curvature-discovered bridges  ", brg)
rep("(3) all cross-sector edges        ", alle)
