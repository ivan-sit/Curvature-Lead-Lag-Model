r"""Factor/sector residualization — INSTRUCTOR REQUIREMENT (CLAUDE.md §4.5).

Build the lead-lag graph on **residual returns**, not raw returns. On raw equity
returns the market and sector factors dominate both the graph and the curvature,
and the degree-preserving null does *not* remove them — so a "topological signal"
on raw returns can be dismissed as merely rediscovering GICS sectors. Removing the
market (and sector / supplied factors) first means any surviving lead-lag is
*idiosyncratic* directional information.

Methods
-------
``market``         : time-series regress each asset on the equal-weight market.
``market_sector``  : market + leave-one-out own-sector factor (default).
``pca``            : remove the top-k statistical (principal-component) factors.
``factors``        : regress on a user-supplied factor panel (e.g. MKT/SMB/HML/MOM).

All methods regress in the time domain and return the residual series, preserving
the (T, N) shape and column order.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["residualize", "market_factor", "sector_factors"]


def _ols_residual(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Residual of y on [1, X] via least squares. X is (T, k)."""
    T = y.shape[0]
    design = np.column_stack([np.ones(T), X]) if X.ndim == 2 else np.column_stack([np.ones(T), X[:, None]])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ beta


def market_factor(returns: pd.DataFrame) -> np.ndarray:
    """Equal-weight market factor (cross-sectional mean per period)."""
    return returns.to_numpy(dtype=float).mean(axis=1)


def sector_factors(returns: pd.DataFrame, sectors: pd.Series) -> dict[object, np.ndarray]:
    """Equal-weight per-sector factor series (including all members)."""
    out: dict[object, np.ndarray] = {}
    for sec, cols in sectors.groupby(sectors).groups.items():
        out[sec] = returns[list(cols)].to_numpy(dtype=float).mean(axis=1)
    return out


def residualize(
    returns: pd.DataFrame,
    sectors: pd.Series | None = None,
    method: str = "market_sector",
    factors: pd.DataFrame | None = None,
    n_pca: int = 3,
) -> pd.DataFrame:
    """Return residual returns after removing the chosen common factors.

    Parameters
    ----------
    returns : (T, N) returns panel.
    sectors : ticker -> sector id (required for ``market_sector``).
    method  : one of ``market`` | ``market_sector`` | ``pca`` | ``factors``.
    factors : (T, k) panel of factor returns (required for ``factors``).
    n_pca   : number of principal components to remove for ``pca``.
    """
    R = returns.to_numpy(dtype=float)
    T, N = R.shape
    resid = np.empty_like(R)

    if method == "market":
        mkt = market_factor(returns)
        for a in range(N):
            resid[:, a] = _ols_residual(R[:, a], mkt)

    elif method == "market_sector":
        if sectors is None:
            raise ValueError("market_sector requires `sectors`")
        sectors = sectors.reindex(returns.columns)
        mkt = market_factor(returns)
        # precompute per-sector sums and counts for leave-one-out factor
        sec_ids = sectors.to_numpy()
        for a in range(N):
            sec = sec_ids[a]
            members = np.where(sec_ids == sec)[0]
            if len(members) > 1:
                others = members[members != a]
                sec_factor = R[:, others].mean(axis=1)  # leave-one-out
                X = np.column_stack([mkt, sec_factor])
            else:
                X = mkt[:, None]
            resid[:, a] = _ols_residual(R[:, a], X)

    elif method == "pca":
        Rc = R - R.mean(axis=0, keepdims=True)
        # top-k PCs from the cross-sectional covariance via SVD
        U, S, Vt = np.linalg.svd(Rc, full_matrices=False)
        k = min(n_pca, len(S))
        common = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
        resid = Rc - common

    elif method == "factors":
        if factors is None:
            raise ValueError("factors method requires a `factors` panel")
        F = factors.reindex(returns.index).to_numpy(dtype=float)
        for a in range(N):
            resid[:, a] = _ols_residual(R[:, a], F)

    else:
        raise ValueError(f"unknown residualization method: {method!r}")

    return pd.DataFrame(resid, index=returns.index, columns=returns.columns)
