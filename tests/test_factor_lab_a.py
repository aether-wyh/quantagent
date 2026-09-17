import numpy as np
import pandas as pd
import pytest

from quanta_agents.factor_lab_a.dsl import Compiler
from quanta_agents.factor_lab_a.evaluate import rank_ic, quantile_returns, annual_table


def _panel(n_dates=300, n_codes=60, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2016-01-01", periods=n_dates)
    cols = [f"S{i:03d}" for i in range(n_codes)]
    close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, 0.02, (n_dates, n_codes)), axis=0)), index=idx, columns=cols)
    volume = pd.DataFrame(rng.lognormal(10, 1, (n_dates, n_codes)), index=idx, columns=cols)
    fields = {"close": close, "open": close * (1 + rng.normal(0, 0.005, close.shape)), "high": close * 1.01, "low": close * 0.99,
              "volume": volume, "amount": volume * close, "turnover": volume / 1e6, "ret": close.pct_change(),
              "log_cap": np.log(volume * close * 50), "prev_close": close.shift(1), "vwap": close, "mkt_ret": close.pct_change().mean(axis=1).to_frame().reindex(columns=cols).ffill(axis=1)}
    fields["mkt_ret"] = pd.DataFrame(np.repeat(close.pct_change().mean(axis=1).values[:, None], n_codes, axis=1), index=idx, columns=cols)
    return fields


EXPRS = [
    "-(close / lag(close, 20) - 1)", "rolling_std(ret, 20)", "cs_rank(rolling_mean(turnover, 10))",
    "rolling_corr(ret, log(volume), 20)", "rolling_residual(ret, mkt_ret, 30)", "ema(close, 10) / close - 1",
    "ts_rank(close, 20) - ts_rank(volume, 20)", "cs_neutralize(cs_rank(rolling_mean(turnover, 20)), log_cap)",
    "where(high > low, (2 * close - high - low) / (high - low), 0 / 0)", "rolling_skew(ret, 20) ** 2",
    "decay_linear(ret, 5)", "ts_zscore(volume, 20)", "(rolling_mean(turnover, 5) / rolling_mean(turnover, 60) < 1) and (ret > 0)",
]


@pytest.mark.parametrize("expr", EXPRS)
def test_time_safety_appending_future_rows_does_not_change_past(expr):
    fields = _panel()
    comp = Compiler(fields)
    full = comp.evaluate(expr)
    cut = 200
    trunc = {k: v.iloc[:cut] for k, v in fields.items()}
    part = Compiler(trunc).evaluate(expr)
    a = full.iloc[:cut].to_numpy(); b = part.to_numpy()
    m = np.isfinite(a) & np.isfinite(b)
    assert (np.isfinite(a) == np.isfinite(b)).mean() > 0.999
    assert np.allclose(a[m], b[m], atol=1e-9)


def test_rejects_unsafe_syntax():
    comp = Compiler(_panel())
    for bad in ["close.shift(-1)", "__import__('os')", "lag(close, -1)", "close[0]", "foo(close)", "lag(close, 0)"]:
        with pytest.raises(Exception):
            comp.canonical(bad)


def test_canonical_identity_stable():
    comp = Compiler(_panel())
    a = comp.canonical("rolling_mean( close ,20)/close")
    b = comp.canonical("rolling_mean(close, 20) / close")
    assert a == b and comp.identity(a) == comp.identity(b)


def test_rank_ic_recovers_planted_signal():
    fields = _panel()
    rng = np.random.default_rng(3)
    label = pd.DataFrame(rng.normal(0, 0.05, fields["close"].shape), index=fields["close"].index, columns=fields["close"].columns)
    factor = label * 30 + pd.DataFrame(rng.normal(0, 1, label.shape), index=label.index, columns=label.columns)
    mask = pd.DataFrame(True, index=label.index, columns=label.columns)
    ric, n = rank_ic(factor, label, mask, min_stocks=30)
    assert ric.mean() > 0.2
    q = quantile_returns(factor, label, mask)
    assert q[10].mean() > q[1].mean()
    tab = annual_table(ric, years=(2016, 2017))
    assert tab[2016]["days"] > 100
