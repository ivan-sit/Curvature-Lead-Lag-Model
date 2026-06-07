#!/usr/bin/env python3
r"""Learn-by-doing: how to pull data from WRDS (Wharton Research Data Services).

Run it:

    python scripts/pull_wrds.py --username YOUR_WRDS_USER --explore
    python scripts/pull_wrds.py --username YOUR_WRDS_USER --start 2000-01-01 --end 2024-12-31

WHAT IS WRDS?
------------
WRDS is a Postgres database hosted by Wharton. The `wrds` Python package opens a
connection and lets you run plain SQL (`db.raw_sql("select ...")`) or convenience
helpers (`db.get_table`, `db.describe_table`). Data is organized as
LIBRARY.TABLE, e.g. `crsp.dsf` (CRSP daily stock file), `comp.company`
(Compustat company), `crsp.dsp500list` (S&P 500 membership).

AUTHENTICATION
--------------
On first connect, `wrds.Connection(wrds_username=...)` asks for your password and
offers to save it to `~/.pgpass` (host:port:db:user:password, chmod 600). After
that, connecting is passwordless. Some institutions also require Duo 2FA — if so,
a push goes to your phone the first time; approve it. NEVER hard-code your
password in a script or commit it to git.

THE KEY TABLES FOR THIS PROJECT
-------------------------------
  crsp.dsf            daily stock file: permno, date, ret, prc, shrout, vol
  crsp.dsedelist      delisting returns (dlret) — needed for survivorship
  crsp.dsp500list     point-in-time S&P 500 membership (permno, start, end dates)
  crsp.dsenames       permno <-> ticker/cusip history
  comp.company        Compustat company: gvkey, GICS (gsector, ggroup, ...)
  crsp.ccmxpf_linktable   links Compustat gvkey <-> CRSP permno
"""

from __future__ import annotations

import argparse
import sys


def connect(username: str):
    """Open a WRDS connection. Uses ~/.pgpass if present, else prompts."""
    import wrds
    print(f"[connect] opening WRDS connection as {username} ...")
    db = wrds.Connection(wrds_username=username)
    print("[connect] connected.")
    return db


def explore(db) -> None:
    """Poke around: list libraries, list a few CRSP tables, describe dsf."""
    print("\n=== libraries you can access (first 25) ===")
    libs = db.list_libraries()
    print(sorted(libs)[:25], "...")

    print("\n=== some tables in the 'crsp' library ===")
    tables = db.list_tables(library="crsp")
    print([t for t in tables if t.startswith(("dsf", "dsp", "dse"))][:15])

    print("\n=== columns of crsp.dsf (the daily stock file) ===")
    print(db.describe_table(library="crsp", table="dsf").head(20).to_string())


def example_single_stocks(db):
    """SIMPLEST query: two stocks by PERMNO over a few days. 10107=MSFT, 14593=AAPL."""
    print("\n=== example 1: two stocks, raw SQL ===")
    df = db.raw_sql(
        """
        select permno, date, ret, prc, vol
        from crsp.dsf
        where date between '2024-01-02' and '2024-01-08'
          and permno in (10107, 14593)
        order by permno, date
        """,
        date_cols=["date"],
    )
    print(df.to_string())
    return df


def example_sp500_universe(db, start: str, end: str):
    """REAL pull: survivorship-correct S&P 500 daily returns, delisting-adjusted.

    Reads like English:
      - `sp500` CTE = point-in-time membership windows from crsp.dsp500list
      - join crsp.dsf to it so each row is only kept while that stock was IN the index
      - LEFT JOIN crsp.dsedelist to splice the delisting-day return (dlret)
    """
    print(f"\n=== example 2: survivorship-correct S&P 500 daily, {start}..{end} ===")
    df = db.raw_sql(
        """
        with sp500 as (
            -- NOTE: crsp.dsp500list columns are `start` / `ending` (alias them)
            select permno, start as mbrstartdt, ending as mbrenddt from crsp.dsp500list
        )
        select a.date, a.permno,
               case
                 when d.dlret is not null and a.ret is not null then (1+a.ret)*(1+d.dlret)-1
                 when d.dlret is not null then d.dlret
                 else a.ret
               end as ret
        from crsp.dsf a
        join sp500 s
          on a.permno = s.permno and a.date between s.mbrstartdt and s.mbrenddt
        left join crsp.dsedelist d
          on a.permno = d.permno and a.date = d.dlstdt
        where a.date between %(start)s and %(end)s
          and (a.ret is not null or d.dlret is not null)
        """,
        params={"start": start, "end": end},
        date_cols=["date"],
    )
    print(f"  got {len(df):,} rows, {df.permno.nunique()} distinct permnos")
    return df


def example_gics(db):
    """GICS sectors per permno, via the Compustat<->CRSP link table."""
    print("\n=== example 3: GICS sector per permno ===")
    df = db.raw_sql(
        """
        select distinct l.lpermno as permno, c.gsector
        from comp.company c
        join crsp.ccmxpf_linktable l
          on c.gvkey = l.gvkey
         and l.linktype in ('LU','LC') and l.linkprim in ('P','C')
        where c.gsector is not null
        """
    )
    print(f"  {len(df):,} permno->gsector rows")
    return df


def example_taq_intraday(db, day: str = "2020-01-02"):
    """TAQ: 30-min last-price bars for a couple of symbols on one day.

    Monthly TAQ is HUGE (taqm_2020.ctm_2020 ~ 15 BILLION rows), so the golden rule
    is: query ONE daily table (ctm_YYYYMMDD), filter by sym_root, and aggregate to
    bars **inside SQL** so only a tiny result comes back. Time bucket = 30 min =
    floor(seconds-since-midnight / 1800) * 1800.
    """
    y, m, d = day.split("-")
    print(f"\n=== example 4: TAQ 30-min bars, {day} ===")
    df = db.raw_sql(
        f"""
        select sym_root,
               floor(extract(epoch from time_m)/1800)*1800 as bucket_sec,
               (array_agg(price order by time_m desc))[1] as last_price,
               sum(size) as volume
        from taqm_{y}.ctm_{y}{m}{d}
        where sym_root in ('AAPL','MSFT')
          and time_m between '09:30:00' and '16:00:00' and price > 0
        group by sym_root, bucket_sec
        order by sym_root, bucket_sec
        """
    )
    print(df.head(8).to_string())
    print(f"  {len(df)} bars (server-side aggregated from millions of trades)")
    return df


def main() -> int:
    p = argparse.ArgumentParser(description="Pull data from WRDS (teaching script).")
    p.add_argument("--username", required=True, help="your WRDS username")
    p.add_argument("--start", default="2000-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--explore", action="store_true", help="just explore libraries/tables")
    p.add_argument("--save", default=None, help="parquet path prefix to save the S&P500 pull")
    args = p.parse_args()

    db = connect(args.username)
    try:
        if args.explore:
            explore(db)
            example_single_stocks(db)
            return 0

        example_single_stocks(db)
        rets = example_sp500_universe(db, args.start, args.end)
        gics = example_gics(db)
        try:
            example_taq_intraday(db)
        except Exception as e:
            print(f"  (TAQ example skipped: {e})")

        if args.save:
            wide = rets.pivot_table(index="date", columns="permno", values="ret").sort_index()
            wide.columns = wide.columns.astype(str)
            wide.to_parquet(f"{args.save}_returns.parquet")
            gics.assign(permno=gics.permno.astype(str)).to_parquet(f"{args.save}_gics.parquet")
            print(f"\n[save] wrote {args.save}_returns.parquet ({wide.shape}) and _gics.parquet")
    finally:
        db.close()
        print("[connect] closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
