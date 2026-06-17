#!/usr/bin/env python3
"""Broad small/mid-cap universe (CRSP daily) for the supply-chain retest: where economic-link
momentum lives (under-covered firms) and links are denser. Common stock, $150M-$10B, liquid.
"""
from __future__ import annotations
import pandas as pd, wrds
db = wrds.Connection(wrds_username="ivansit1214")
print("selecting universe...", flush=True)
perm = db.raw_sql("""
  select m.permno from (
    select a.permno, avg(abs(a.prc)*a.shrout)/1000.0 as me_musd, count(*) as nd
    from crsp.dsf a where a.date between '2010-01-01' and '2016-12-31' and a.prc is not null and a.shrout>0
    group by a.permno
  ) m
  join (select distinct permno, shrcd, exchcd from crsp.dsenames where shrcd in (10,11) and exchcd in (1,2,3)) n
    on m.permno=n.permno
  where m.me_musd between 150 and 10000 and m.nd > 1200
  order by m.nd desc limit 2000
""")
permnos = tuple(int(p) for p in perm["permno"])
print(f"{len(permnos)} permnos; pulling returns...", flush=True)
r = db.raw_sql("""select date, permno, ret from crsp.dsf
                  where permno in %(p)s and date between '2005-01-01' and '2024-12-31' and ret is not null""",
               params={"p": permnos}, date_cols=["date"])
g = db.raw_sql("""select distinct l.lpermno as permno, c.gsector from comp.company c
  join crsp.ccmxpf_linktable l on c.gvkey=l.gvkey and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
  where l.lpermno in %(p)s and c.gsector is not null""", params={"p": permnos})
db.close()
w = r.pivot_table(index="date", columns="permno", values="ret").sort_index()
w.columns = [str(int(c)) for c in w.columns]
w.to_parquet("data/returns_smallcap.parquet")
gg = g.drop_duplicates("permno"); gg["permno"]=gg["permno"].astype(int).astype(str)
gg.set_index("permno")["gsector"].astype(str).to_frame("gsector").to_parquet("data/sectors_smallcap.parquet")
print(f"SAVED returns_smallcap {w.shape}, {(w.notna().mean()>=0.7).sum()} names >=70% present", flush=True)
