#!/usr/bin/env python3
"""Pull quarterly EPS (Compustat fundq) for the fixed daily universe, mapped to permno
via the CCM link. For the fundamentals angle: does curvature relate to earnings risk?
"""
from __future__ import annotations
import pandas as pd
from cllm.data import load_wrds_crsp  # noqa: ensures cllm import path
import wrds

rets = pd.read_parquet("data/returns_wrds.parquet")
permnos = tuple(int(c) for c in rets.columns[rets.notna().mean() >= 0.98])
print(f"pulling EPS for {len(permnos)} permnos")
db = wrds.Connection(wrds_username="ivansit1214")
sql = """
SELECT DISTINCT l.lpermno AS permno, f.gvkey, f.datadate, f.rdq, f.epsfxq, f.epspxq, f.saleq
FROM comp.fundq f
JOIN crsp.ccmxpf_linktable l
  ON f.gvkey = l.gvkey
 AND l.linktype IN ('LU','LC') AND l.linkprim IN ('P','C')
 AND f.datadate >= l.linkdt AND (l.linkenddt IS NULL OR f.datadate <= l.linkenddt)
WHERE l.lpermno IN %(p)s
  AND f.indfmt='INDL' AND f.datafmt='STD' AND f.popsrc='D' AND f.consol='C'
  AND f.datadate BETWEEN '2000-01-01' AND '2024-12-31'
"""
df = db.raw_sql(sql, params={"p": permnos}, date_cols=["datadate", "rdq"])
db.close()
df.to_parquet("data/eps_wrds.parquet")
print(f"saved data/eps_wrds.parquet {df.shape}; {df['permno'].nunique()} permnos with EPS")
print(df.head())
