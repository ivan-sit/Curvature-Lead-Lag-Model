r"""Uniform data loaders.

``DataBundle`` = (returns: DataFrame[T x N], sectors: Series[ticker -> sector]).

- ``load_synthetic`` — factor + lead-lag generator (development / kill-switches).
- ``load_csv`` — a wide returns CSV (e.g. the professor-provided file) + optional
  sector map. Auto-detects wide (date index, ticker columns) vs long (tidy) format.
- ``load_wrds_crsp`` — pulls CRSP daily returns for point-in-time S&P 500 members,
  delisting-adjusted, joined to Compustat GICS via CCM. Requires the ``wrds``
  package + institutional login; raises a clear message otherwise. The exact SQL
  is included so it is ready the moment access is granted.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..synthetic import factor_lead_lag_returns

__all__ = ["DataBundle", "load_synthetic", "load_csv", "load_wrds_crsp", "assemble_wrds_csvs"]


@dataclass
class DataBundle:
    returns: pd.DataFrame          # (T, N), columns = tickers
    sectors: pd.Series | None      # ticker -> sector id (GICS), may be None

    def __post_init__(self):
        if self.sectors is not None:
            self.sectors = self.sectors.reindex(self.returns.columns)

    @property
    def shape(self):
        return self.returns.shape


def load_synthetic(seed: int = 0, **kwargs) -> DataBundle:
    data = factor_lead_lag_returns(seed=seed, **kwargs)
    return DataBundle(returns=data.returns, sectors=data.sectors)


def load_csv(returns_path: str | Path, sectors_path: str | Path | None = None) -> DataBundle:
    """Load a returns CSV. Wide format: first column = date, rest = tickers. Long
    format (columns include date/permno-or-ticker/ret) is pivoted automatically."""
    raw = pd.read_csv(returns_path)
    cols_lower = {c.lower(): c for c in raw.columns}
    is_long = any(k in cols_lower for k in ("ret", "return", "returns")) and any(
        k in cols_lower for k in ("permno", "ticker", "cusip", "id")
    )
    if is_long:
        date_col = next((cols_lower[k] for k in ("date", "datadate", "caldt") if k in cols_lower),
                        raw.columns[0])
        id_col = next(cols_lower[k] for k in ("ticker", "permno", "cusip", "id") if k in cols_lower)
        ret_col = next(cols_lower[k] for k in ("ret", "return", "returns") if k in cols_lower)
        returns = raw.pivot_table(index=date_col, columns=id_col, values=ret_col)
    else:
        returns = raw.set_index(raw.columns[0])
    returns = returns.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    returns.index.name = "date"

    sectors = None
    if sectors_path is not None:
        smap = pd.read_csv(sectors_path)
        scl = {c.lower(): c for c in smap.columns}
        idc = next(scl[k] for k in ("ticker", "permno", "cusip", "id") if k in scl)
        secc = next(scl[k] for k in ("sector", "gsector", "gics", "ggroup") if k in scl)
        sectors = smap.set_index(idc)[secc]
    return DataBundle(returns=returns, sectors=sectors)


# WRDS SQL — runs verbatim once access is granted. -------------------------- #
_CRSP_SP500_SQL = """
WITH sp500 AS (
    SELECT permno, start AS mbrstartdt, ending AS mbrenddt
    FROM crsp.dsp500list
)
SELECT a.date, a.permno,
       CASE
         WHEN d.dlret IS NOT NULL AND a.ret IS NOT NULL THEN (1 + a.ret) * (1 + d.dlret) - 1
         WHEN d.dlret IS NOT NULL THEN d.dlret
         ELSE a.ret
       END AS ret
FROM crsp.dsf AS a
JOIN sp500 AS s
  ON a.permno = s.permno
 AND a.date BETWEEN s.mbrstartdt AND s.mbrenddt
LEFT JOIN crsp.dsedelist AS d
  ON a.permno = d.permno AND a.date = d.dlstdt
WHERE a.date BETWEEN %(start)s AND %(end)s
  AND (a.ret IS NOT NULL OR d.dlret IS NOT NULL)
"""

_GICS_SQL = """
SELECT DISTINCT l.lpermno AS permno, c.gsector
FROM comp.company AS c
JOIN crsp.ccmxpf_linktable AS l
  ON c.gvkey = l.gvkey
 AND l.linktype IN ('LU','LC')
 AND l.linkprim IN ('P','C')
WHERE c.gsector IS NOT NULL
"""


def load_crsp_matrix(
    returns_csv: str | Path,
    sectors_csv: str | Path | None = None,
    sector_col: str = "Sector_Wikipedia",
) -> DataBundle:
    """Load the group's CRSP *matrix-format* extract (Cucuringu-group format).

    The returns file has the first column = instrument ``ticker`` and the remaining
    columns = trading days named ``X20000103`` (i.e. ``XYYYYMMDD``); values are the
    chosen return variable (``pvCLCL`` = close-to-close, ``OPCL`` = open-to-close).
    We transpose to a (T x N) panel (index = dates, columns = tickers).

    NOTE on survivorship: this "subset universe" keeps only instruments present
    *every day* over the sample, so it is survivor-only (a balanced panel), NOT
    point-in-time index membership. Fine for development and a first real result;
    for the paper's survivorship-correct results use ``load_wrds_crsp``.

    ``sectors_csv`` is the group's ``Sectors_SP500_*`` file (``Ticker`` + a sector
    column such as ``Sector_Wikipedia`` / ``Sector_Yahoo``).
    """
    raw = pd.read_csv(returns_csv)
    raw = raw.set_index(raw.columns[0])
    dates = pd.to_datetime([str(c).lstrip("X") for c in raw.columns], format="%Y%m%d")
    returns = raw.T
    returns.index = dates
    returns.index.name = "date"
    returns = returns.apply(pd.to_numeric, errors="coerce")
    returns.columns = [str(c) for c in returns.columns]
    # a handful of stray missing values exist despite the "every day" claim; a
    # missing daily return is treated as 0 (no move). NaNs left in place would
    # poison both the cross-correlation quantile and the residualization SVD.
    returns = returns.fillna(0.0)

    sectors = None
    if sectors_csv is not None:
        s = pd.read_csv(sectors_csv)
        tcol = _find_col(s.columns, "ticker")
        scol = sector_col if sector_col in s.columns else _find_col(s.columns, "sector", "gsector")
        sectors = s.drop_duplicates(tcol).set_index(tcol)[scol].reindex(returns.columns)
    return DataBundle(returns=returns, sectors=sectors)


def _find_col(cols, *candidates) -> str:
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in low:
            return low[cand]
    raise KeyError(f"none of {candidates} found in columns {list(cols)}")


def assemble_wrds_csvs(
    daily_returns_csv: str | Path,
    members_csv: str | Path | None = None,
    gics_csv: str | Path | None = None,
) -> DataBundle:
    """Assemble a survivorship-correct DataBundle from WRDS web-query CSV exports.

    Files (column names auto-detected, case-insensitive):

    1. ``daily_returns_csv`` — CRSP Daily Stock File: needs ``permno``, ``date``,
       ``ret`` (a long/tidy file).
    2. ``members_csv`` — CRSP S&P 500 constituents (``dsp500list``): ``permno``,
       ``mbrstartdt`` (start), ``mbrenddt`` (end). If given, returns are kept ONLY
       within each stock's membership window (point-in-time survivorship handling).
    3. ``gics_csv`` — GICS map: ``permno`` (or ``lpermno``) and ``gsector``.

    Returns a (T x N) wide returns panel (columns = permno strings) + sector map.
    """
    raw = pd.read_csv(daily_returns_csv)
    pcol = _find_col(raw.columns, "permno")
    dcol = _find_col(raw.columns, "date", "caldt", "datadate")
    rcol = _find_col(raw.columns, "ret", "return", "returns")
    raw = raw[[pcol, dcol, rcol]].copy()
    raw[dcol] = pd.to_datetime(raw[dcol])
    raw[rcol] = pd.to_numeric(raw[rcol], errors="coerce")
    raw[pcol] = raw[pcol].astype(int).astype(str)

    if members_csv is not None:
        mem = pd.read_csv(members_csv)
        mp = _find_col(mem.columns, "permno")
        ms = _find_col(mem.columns, "mbrstartdt", "start", "from", "linkdt")
        me = _find_col(mem.columns, "mbrenddt", "end", "thru", "linkenddt")
        mem = mem[[mp, ms, me]].copy()
        mem[mp] = mem[mp].astype(int).astype(str)
        mem[ms] = pd.to_datetime(mem[ms])
        mem[me] = pd.to_datetime(mem[me].replace({"E": None, "": None})).fillna(pd.Timestamp("2100-01-01"))
        keep = raw.merge(mem, left_on=pcol, right_on=mp, how="inner")
        keep = keep[(keep[dcol] >= keep[ms]) & (keep[dcol] <= keep[me])]
        raw = keep[[pcol, dcol, rcol]]

    returns = raw.pivot_table(index=dcol, columns=pcol, values=rcol).sort_index()
    returns.index.name = "date"

    sectors = None
    if gics_csv is not None:
        g = pd.read_csv(gics_csv)
        gp = _find_col(g.columns, "permno", "lpermno")
        gs = _find_col(g.columns, "gsector", "sector", "gics")
        g = g[[gp, gs]].dropna().drop_duplicates(gp)
        g[gp] = g[gp].astype(int).astype(str)
        sectors = g.set_index(gp)[gs].reindex(returns.columns)
    return DataBundle(returns=returns, sectors=sectors)


def load_wrds_crsp(
    start: str = "2000-01-01",
    end: str = "2024-12-31",
    wrds_username: str | None = None,
) -> DataBundle:
    """Pull survivorship-correct CRSP daily returns for S&P 500 members + GICS.

    Requires ``pip install wrds`` and a valid WRDS login (institutional). Returns
    delisting-adjusted daily returns pivoted to (T x N) by permno, with the GICS
    sector map. Raises a helpful error if the package or access is missing.
    """
    try:
        import wrds  # type: ignore
    except ImportError as e:  # pragma: no cover - depends on optional dep
        raise RuntimeError(
            "WRDS access not available. Install with `pip install wrds` and ensure "
            "you have an approved UCLA WRDS account, then call load_wrds_crsp(). "
            "Until then use load_synthetic() or load_csv()."
        ) from e

    db = wrds.Connection(wrds_username=wrds_username)  # pragma: no cover
    try:
        rets = db.raw_sql(_CRSP_SP500_SQL, params={"start": start, "end": end},
                          date_cols=["date"])
        gics = db.raw_sql(_GICS_SQL)
    finally:
        db.close()

    returns = rets.pivot_table(index="date", columns="permno", values="ret")
    # permno comes back as float (numeric) -> normalize to a clean int-string on
    # BOTH sides so the GICS reindex matches ("10107", not "10107.0").
    returns.columns = [str(int(float(c))) for c in returns.columns]
    sectors = gics.drop_duplicates("permno").set_index("permno")["gsector"]
    sectors.index = [str(int(float(c))) for c in sectors.index]
    return DataBundle(returns=returns, sectors=sectors.reindex(returns.columns))


# 30-min bar aggregation from millisecond TAQ, computed server-side per day. ---- #
# Use DISTINCT ON (the Postgres "last row per group" idiom) rather than
# array_agg(... ORDER BY ...)[1]: array_agg materializes a sorted array of EVERY
# trade in each bucket, which overflows server-side work_mem on high-volume days
# (500k-800k trades) and silently fails. DISTINCT ON streams to one row per bucket.
_TAQ_BARS_SQL = """
SELECT DISTINCT ON (sym_root, bucket_sec)
       sym_root, bucket_sec, price AS last_price
FROM (
  SELECT sym_root,
         floor(extract(epoch from time_m) / %(bar_sec)s) * %(bar_sec)s AS bucket_sec,
         price, time_m, tr_seqnum
  FROM taqm_{year}.ctm_{yyyymmdd}
  WHERE sym_root IN %(syms)s
    AND time_m BETWEEN '09:30:00' AND '16:00:00'
    AND price > 0
) t
ORDER BY sym_root, bucket_sec, time_m DESC, tr_seqnum DESC
"""


def load_wrds_taq_intraday(
    symbols: list[str],
    days: list[str],
    bar_minutes: int = 30,
    wrds_username: str | None = None,
    return_prices: bool = False,
    checkpoint_path: str | Path | None = None,
    resume: bool = True,
    statement_timeout_s: int = 300,
) -> pd.DataFrame:
    """Pull intraday 30-min bar RETURNS for ``symbols`` over a list of trading
    ``days`` (``"YYYY-MM-DD"``) from Monthly TAQ.

    Each day's millisecond trades are aggregated to last-price bars **server-side**
    (one small result per day), then stitched into an intraday returns panel
    (index = bar timestamps, columns = symbols). Overnight gaps are dropped
    (intra-day log returns only) — overnight is macro-driven, not microstructural
    (CLAUDE.md §9). This is the Phase-2 intraday input where lead-lag is strongest.

    Resilience (a full-year pull is multi-hour — never lose it to a crash/hang):

    * ``checkpoint_path`` — if given, the accumulated **prices** are written there
      every 20 days; on restart with ``resume=True`` any day already present is
      skipped, so an interrupted pull continues where it left off.
    * ``statement_timeout_s`` — a server-side ``statement_timeout`` so a single
      pathological day-query cannot hang the whole pull indefinitely; it errors,
      is caught, and that day is skipped.

    WARNING: TAQ is enormous. Always pull a bounded symbol list + day list; never
    a whole year of the universe. (taqm_YYYY.ctm_YYYY is ~15 billion rows.)
    """
    try:
        import wrds  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("pip install wrds and have WRDS access to use TAQ") from e

    bar_sec = bar_minutes * 60
    syms = tuple(symbols)
    progress = bool(globals().get("_TAQ_PROGRESS", True))

    # resume from a prior checkpoint of accumulated prices
    frames: list[pd.DataFrame] = []
    done_days: set = set()
    ckpt = Path(checkpoint_path) if checkpoint_path is not None else None
    if ckpt is not None and resume and ckpt.exists():
        prior = pd.read_parquet(ckpt)
        frames.append(prior)
        done_days = set(pd.DatetimeIndex(prior.index).normalize().strftime("%Y-%m-%d"))
        if progress:
            print(f"[taq] resume: {len(done_days)} days already in {ckpt}", flush=True)

    db = wrds.Connection(wrds_username=wrds_username)  # pragma: no cover
    try:
        # cap each query server-side so a pathological day cannot hang the pull
        try:
            db.raw_sql(f"SET statement_timeout = {int(statement_timeout_s) * 1000}")
        except Exception:
            pass
        new_since_ckpt = 0
        for i, day in enumerate(days):
            if day in done_days:
                continue
            y, m, d = day.split("-")
            sql = _TAQ_BARS_SQL.format(year=y, yyyymmdd=f"{y}{m}{d}")
            try:
                raw = db.raw_sql(sql, params={"bar_sec": bar_sec, "syms": syms})
            except Exception as e:
                if progress:
                    print(f"[taq] SKIP {day}: {repr(e)[:80]}", flush=True)
                continue  # holiday / missing table / timeout -> skip
            if raw.empty:
                continue
            raw["ts"] = pd.to_datetime(day) + pd.to_timedelta(raw["bucket_sec"], unit="s")
            wide = raw.pivot_table(index="ts", columns="sym_root", values="last_price")
            frames.append(wide)
            new_since_ckpt += 1
            if progress and (i % 20 == 0 or i == len(days) - 1):
                print(f"[taq] {i + 1}/{len(days)} days ({day})", flush=True)
            # periodic checkpoint of accumulated prices
            if ckpt is not None and new_since_ckpt >= 20:
                pd.concat(frames).sort_index().to_parquet(ckpt)
                new_since_ckpt = 0
                if progress:
                    print(f"[taq] checkpoint -> {ckpt}", flush=True)
    finally:
        db.close()

    if not frames:
        return pd.DataFrame()
    prices = pd.concat(frames).sort_index()
    prices = prices[~prices.index.duplicated(keep="last")]
    if ckpt is not None:
        prices.to_parquet(ckpt)
    if return_prices:
        return prices
    # intraday returns within each day (drop the first bar of each day = overnight)
    rets = prices.groupby(prices.index.normalize()).apply(lambda x: x.pct_change()).droplevel(0)
    return rets.dropna(how="all")
