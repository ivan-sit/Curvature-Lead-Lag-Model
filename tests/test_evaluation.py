"""Out-of-sample directional IC metric + selectors + bootstrap CI."""

import numpy as np

from cllm.evaluation import (
    block_bootstrap_ic,
    directional_ic,
    orient_pairs,
    select_by_correlation,
    select_random,
)
from cllm.synthetic import factor_lead_lag_returns
from cllm.validation import train_val_test_split


def _split(returns):
    tr, va, te = train_val_test_split(len(returns), (0.6, 0.0, 0.4))
    return returns.iloc[tr], returns.iloc[te].reset_index(drop=True)


def test_directional_ic_positive_on_true_pairs():
    data = factor_lead_lag_returns(
        n_assets=24, n_periods=4000, n_lead_lag_pairs=6,
        lead_lag=1, lead_lag_strength=0.7, seed=3,
    )
    train, test = _split(data.returns)
    true_pairs = [(l, g, lag) for (l, g, lag) in data.lead_lag_pairs]
    res = directional_ic(train, test, true_pairs)
    # the planted leader->lagger pairs must carry positive OOS directional info
    assert res.mean_ic > 0.05
    assert res.n_pairs >= 1


def test_random_pairs_have_near_zero_ic():
    data = factor_lead_lag_returns(n_assets=30, n_periods=4000, n_lead_lag_pairs=5, seed=4)
    train, test = _split(data.returns)
    tickers = list(data.returns.columns)
    cands = [(tickers[i], tickers[j]) for i in range(len(tickers)) for j in range(i + 1, len(tickers))]
    pairs = select_random(cands, k=15, returns_train=train, seed=1)
    res = directional_ic(train, test, pairs)
    # random selection should not have a large directional IC
    assert abs(res.mean_ic) < 0.1


def test_orientation_recovers_leader():
    data = factor_lead_lag_returns(
        n_assets=12, n_periods=5000, n_lead_lag_pairs=3,
        lead_lag=1, lead_lag_strength=0.8, seed=8,
    )
    train, _ = _split(data.returns)
    leader, lagger, lag = data.lead_lag_pairs[0]
    oriented = orient_pairs(train, [(leader, lagger)], lags=(1, 2, 3))
    # leader should be identified as the leader (not flipped)
    assert oriented[0][0] == leader
    assert oriented[0][1] == lagger


def test_within_day_ic_drops_cross_day_pairs():
    # planted lead-lag at lag 1; within-day groups must (a) still recover positive
    # IC and (b) use fewer observations than the unrestricted version.
    data = factor_lead_lag_returns(
        n_assets=16, n_periods=4000, n_lead_lag_pairs=5,
        lead_lag=1, lead_lag_strength=0.7, seed=5,
    )
    train, test = _split(data.returns)
    true_pairs = [(l, g, lag) for (l, g, lag) in data.lead_lag_pairs]
    # 10-bar "days" over the test window
    groups = np.repeat(np.arange(len(test) // 10 + 1), 10)[: len(test)]
    res_all = directional_ic(train, test, true_pairs)
    res_wd = directional_ic(train, test, true_pairs, groups=groups)
    assert res_wd.n_pairs >= 1
    # within-day uses strictly fewer (forecast, realized) obs -> different pooled IC
    assert res_wd.pooled_ic != res_all.pooled_ic
    # signal survives the within-day restriction
    assert res_wd.mean_ic > 0.0
    # bootstrap carries groups without error
    ci = block_bootstrap_ic(train, test, true_pairs, n_boot=30, block=10,
                            seed=0, groups=groups)
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]


def test_correlation_selector_and_bootstrap_ci_run():
    data = factor_lead_lag_returns(n_assets=20, n_periods=3000, n_lead_lag_pairs=5, seed=6)
    train, test = _split(data.returns)
    tickers = list(data.returns.columns)
    cands = [(tickers[i], tickers[j]) for i in range(len(tickers)) for j in range(i + 1, len(tickers))]
    pairs = select_by_correlation(train, cands, k=10)
    ci = block_bootstrap_ic(train, test, pairs, n_boot=50, block=20, seed=0)
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]
    assert np.isfinite(ci["mean"])
