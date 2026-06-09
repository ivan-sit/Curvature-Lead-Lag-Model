r"""Evaluation — PRIMARY metric: out-of-sample directional IC (CLAUDE.md §7.2).

The headline claim is *predictive*: curvature-selected leader->lagger pairs carry
out-of-sample directional information. We measure the **directional information
coefficient (IC)** — the rank correlation between the leader-based forecast of the
lagger's future return and its realized future return, on a held-out window — and
compare curvature selection against baselines on identical settings:

    correlation-distance, correlation-matrix clustering, cointegration, random,
    undirected Forman (symmetrized graph), Ollivier-Ricci.

Curvature is a *selection* signal; the directional sign is inherited from the
lead-lag estimate (fit on train), never from the curvature. Differences in IC
across methods get block-bootstrap confidence intervals. A mean-reversion PnL
hook is provided but is an optional secondary deliverable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

__all__ = [
    "orient_pairs",
    "directional_ic",
    "select_top_edges",
    "select_random",
    "select_by_correlation",
    "select_by_cointegration",
    "block_bootstrap_ic",
    "evaluate_methods",
]

Pair = tuple  # (leader, lagger, lag)


# --------------------------------------------------------------------------- #
# Orientation + the IC metric
# --------------------------------------------------------------------------- #
def _best_direction(rtr: pd.DataFrame, a: str, b: str, lags) -> Pair:
    """Pick (leader, lagger, lag) maximizing |lagged corr| on the train window."""
    best = (a, b, lags[0], -1.0)
    for lag in lags:
        ca = np.corrcoef(rtr[a].values[:-lag], rtr[b].values[lag:])[0, 1]  # a leads b
        cb = np.corrcoef(rtr[b].values[:-lag], rtr[a].values[lag:])[0, 1]  # b leads a
        if abs(ca) > best[3]:
            best = (a, b, lag, abs(ca))
        if abs(cb) > best[3]:
            best = (b, a, lag, abs(cb))
    return (best[0], best[1], best[2])


def orient_pairs(returns_train: pd.DataFrame, unordered_pairs, lags=(1, 2, 3, 5)) -> list[Pair]:
    """Assign a leader/lagger/lag to each unordered pair using the train window."""
    return [_best_direction(returns_train, a, b, lags) for a, b in unordered_pairs]


@dataclass
class ICResult:
    mean_ic: float
    pooled_ic: float
    per_pair: dict
    n_pairs: int


def directional_ic(
    returns_train: pd.DataFrame,
    returns_test: pd.DataFrame,
    pairs: list[Pair],
    groups: np.ndarray | None = None,
) -> ICResult:
    """Out-of-sample directional IC for a set of (leader, lagger, lag) pairs.

    For each pair: the predictive sign ``s`` is fit on train
    (``sign corr(leader[:-lag], lagger[lag:])``); the OOS forecast of the lagger's
    return at ``t+lag`` is ``s * leader[t]`` and the IC is its Spearman rank
    correlation with the realized lagger return on the test window. We report the
    mean per-pair IC and a pooled IC over all (forecast, realized) observations.

    ``groups`` (optional) is a per-test-row label (trading day for intraday data).
    When given, the ``(t, t+lag)`` forecast/realized pairing is restricted to the
    **same day** — a within-day-only prediction horizon that never bets a late-day
    leader on the next morning's lagger across the overnight gap.
    """
    per_pair: dict = {}
    all_fore, all_real = [], []
    g = np.asarray(groups) if groups is not None else None
    for leader, lagger, lag in pairs:
        if leader not in returns_train or lagger not in returns_train:
            continue
        s = np.sign(np.corrcoef(
            returns_train[leader].values[:-lag], returns_train[lagger].values[lag:]
        )[0, 1])
        s = s if s != 0 else 1.0
        fore = s * returns_test[leader].values[:-lag]
        real = returns_test[lagger].values[lag:]
        if g is not None and g.shape[0] == returns_test.shape[0]:
            m = g[:-lag] == g[lag:]
            fore, real = fore[m], real[m]
        if len(fore) < 5:
            continue
        ic, _ = spearmanr(fore, real)
        if np.isfinite(ic):
            per_pair[(leader, lagger, lag)] = float(ic)
            all_fore.append(fore)
            all_real.append(real)

    mean_ic = float(np.mean(list(per_pair.values()))) if per_pair else float("nan")
    if all_fore:
        pf = np.concatenate(all_fore)
        pr = np.concatenate(all_real)
        pooled, _ = spearmanr(pf, pr)
        pooled_ic = float(pooled) if np.isfinite(pooled) else float("nan")
    else:
        pooled_ic = float("nan")
    return ICResult(mean_ic=mean_ic, pooled_ic=pooled_ic, per_pair=per_pair, n_pairs=len(per_pair))


# --------------------------------------------------------------------------- #
# Pair selectors (each returns a list of oriented pairs)
# --------------------------------------------------------------------------- #
def select_top_edges(curv_df: pd.DataFrame, column: str, k: int, ascending: bool = True) -> list[Pair]:
    """Select k edges by a curvature column (ascending => most negative = most
    isolated). Uses the (source, target) index and the per-edge ``lag`` if present."""
    df = curv_df.sort_values(column, ascending=ascending).head(k)
    lags = df["lag"] if "lag" in df.columns else None
    out = []
    for i, (src, dst) in enumerate(df.index):
        lag = int(lags.iloc[i]) if lags is not None else 1
        out.append((src, dst, lag))
    return out


def select_random(unordered_pairs, k: int, returns_train: pd.DataFrame,
                  lags=(1, 2, 3, 5), seed: int | None = 0) -> list[Pair]:
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(unordered_pairs), size=min(k, len(unordered_pairs)), replace=False)
    chosen = [unordered_pairs[i] for i in idx]
    return orient_pairs(returns_train, chosen, lags)


def select_by_correlation(returns_train: pd.DataFrame, candidates, k: int,
                          lags=(1, 2, 3, 5)) -> list[Pair]:
    """Top-k pairs by contemporaneous |correlation| (the distance/correlation
    baseline; Gower-Mantegna distance is monotone in |rho|)."""
    C = returns_train.corr().abs()
    scored = sorted(candidates, key=lambda p: C.loc[p[0], p[1]], reverse=True)
    return orient_pairs(returns_train, scored[:k], lags)


def select_by_cointegration(returns_train: pd.DataFrame, candidates, k: int,
                            lags=(1, 2, 3, 5)) -> list[Pair]:
    """Top-k most-cointegrated pairs (lowest Engle-Granger p-value on cumulative
    log-price proxies = cumulative returns)."""
    from statsmodels.tsa.stattools import coint

    prices = returns_train.cumsum()
    scored = []
    for a, b in candidates:
        try:
            _, pval, _ = coint(prices[a].values, prices[b].values)
        except Exception:
            pval = 1.0
        scored.append(((a, b), pval))
    scored.sort(key=lambda kv: kv[1])
    chosen = [p for p, _ in scored[:k]]
    return orient_pairs(returns_train, chosen, lags)


# --------------------------------------------------------------------------- #
# Block-bootstrap CIs
# --------------------------------------------------------------------------- #
def block_bootstrap_ic(
    returns_train: pd.DataFrame,
    returns_test: pd.DataFrame,
    pairs: list[Pair],
    n_boot: int = 200,
    block: int = 20,
    seed: int | None = 0,
    groups: np.ndarray | None = None,
) -> dict:
    """Block-bootstrap the TEST window; return mean-IC distribution + 95% CI.

    ``groups`` (per-test-row day label) is resampled alongside the rows so the
    within-day IC pairing is preserved under the bootstrap.
    """
    rng = np.random.default_rng(seed)
    T = len(returns_test)
    n_blocks = int(np.ceil(T / block))
    g = np.asarray(groups) if groups is not None else None
    vals = []
    for _ in range(n_boot):
        starts = rng.integers(0, max(1, T - block), size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block, T)) for s in starts])[:T]
        boot = returns_test.iloc[idx].reset_index(drop=True)
        boot_groups = g[idx] if g is not None else None
        vals.append(directional_ic(returns_train, boot, pairs, groups=boot_groups).mean_ic)
    arr = np.asarray([v for v in vals if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return {"mean": float("nan"), "ci_low": float("nan"), "ci_high": float("nan")}
    return {
        "mean": float(arr.mean()),
        "ci_low": float(np.percentile(arr, 2.5)),
        "ci_high": float(np.percentile(arr, 97.5)),
    }


# --------------------------------------------------------------------------- #
# Mean-reversion PnL (OPTIONAL secondary — CLAUDE.md §8). Not a core deliverable.
# --------------------------------------------------------------------------- #
def mean_reversion_pnl(
    returns_test: pd.DataFrame, pairs: list[Pair], z_entry: float = 2.0, lookback: int = 30
) -> dict:
    """Simple market-neutral mean-reversion PnL on the spread of each pair.

    Spread s_t = leader - lagger; trade against |z(s_t)| > z_entry. Returned as
    annualized Sharpe of the equally-weighted pair book (a sanity number only — the
    standardized harness is AlphaMark, used only if the optional PnL path is taken).
    """
    pnls = []
    for leader, lagger, _ in pairs:
        if leader not in returns_test or lagger not in returns_test:
            continue
        spread = returns_test[leader].cumsum() - returns_test[lagger].cumsum()
        mu = spread.rolling(lookback).mean()
        sd = spread.rolling(lookback).std()
        z = (spread - mu) / sd
        pos = (-np.sign(z)).where(z.abs() > z_entry, 0.0).shift(1).fillna(0.0)
        pair_ret = pos * (returns_test[leader] - returns_test[lagger])
        pnls.append(pair_ret)
    if not pnls:
        return {"sharpe": float("nan"), "mean_daily": float("nan")}
    book = pd.concat(pnls, axis=1).mean(axis=1)
    sharpe = float(np.sqrt(252) * book.mean() / book.std()) if book.std() > 0 else float("nan")
    return {"sharpe": sharpe, "mean_daily": float(book.mean())}
