"""Residualization must remove common factors yet preserve idiosyncratic lead-lag."""

import numpy as np

from cllm.network import lagged_cross_correlation
from cllm.residualize import market_factor, residualize
from cllm.synthetic import factor_lead_lag_returns


def _avg_abs_offdiag_corr(df):
    C = np.corrcoef(df.to_numpy().T)
    n = C.shape[0]
    return (np.abs(C).sum() - n) / (n * (n - 1))


def test_market_residual_is_orthogonal_to_market():
    data = factor_lead_lag_returns(n_assets=30, n_periods=2000, seed=1)
    resid = residualize(data.returns, method="market")
    mkt = market_factor(data.returns)
    # each residual series should be ~uncorrelated with the market factor
    for col in resid.columns:
        rho = np.corrcoef(resid[col].values, mkt)[0, 1]
        assert abs(rho) < 1e-6


def test_market_sector_reduces_common_correlation():
    data = factor_lead_lag_returns(
        n_assets=40, n_periods=3000, n_sectors=4, n_lead_lag_pairs=6, seed=3
    )
    raw_corr = _avg_abs_offdiag_corr(data.returns)
    resid = residualize(data.returns, sectors=data.sectors, method="market_sector")
    resid_corr = _avg_abs_offdiag_corr(resid)
    # common factor structure removed -> lower average cross-sectional correlation
    assert resid_corr < raw_corr


def test_lead_lag_survives_residualization():
    data = factor_lead_lag_returns(
        n_assets=30, n_periods=6000, n_sectors=3, n_lead_lag_pairs=5,
        lead_lag=1, lead_lag_strength=0.7, seed=9,
    )
    resid = residualize(data.returns, sectors=data.sectors, method="market_sector")
    leader, lagger, lag = data.lead_lag_pairs[0]
    # the directional idiosyncratic signal should survive (and be detectable)
    x = resid[leader].values[:-lag]
    y = resid[lagger].values[lag:]
    rho = np.corrcoef(x, y)[0, 1]
    assert rho > 0.05
    # the signed lead-lag matrix should still flag this pair directionally
    C = lagged_cross_correlation(resid, lag=1)
    i = list(resid.columns).index(leader)
    j = list(resid.columns).index(lagger)
    assert C[i, j] - C[j, i] > 0  # leader -> lagger


def test_pca_and_factors_methods_run():
    data = factor_lead_lag_returns(n_assets=20, n_periods=1000, seed=4)
    r_pca = residualize(data.returns, method="pca", n_pca=2)
    assert r_pca.shape == data.returns.shape
    # supply the true market as an explicit factor
    import pandas as pd
    F = pd.DataFrame({"MKT": market_factor(data.returns)}, index=data.returns.index)
    r_fac = residualize(data.returns, method="factors", factors=F)
    assert r_fac.shape == data.returns.shape
