"""Hand NAV examples exercise full-capital dates and sample-volatility policy."""
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('v4_result_audit',
    Path(__file__).resolve().parents[1] / 'scripts/audit_v4_structural_cycle_results.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def metrics(navs, **changes):
    counts = {'trade_count': 2, 'exit_batches': 1, 'flat_share_exits': 1}
    return audit.nav_metrics('100', navs, **{**counts, **changes})


def test_cash_day_then_ten_percent_gain_and_loss_uses_sample_std():
    # Daily returns are 0, +10%, -10%; arithmetic mean 0, sample std 10%.
    result = metrics(['100', '110', '99'])
    assert result['daily_return_count'] == 3
    assert float(result['daily_return_mean']) == 0
    assert float(result['daily_return_sample_std']) == pytest.approx(0.1)
    assert float(result['net_return']) == pytest.approx(-0.01)
    assert float(result['maximum_drawdown']) == pytest.approx(0.1)
    assert float(result['sharpe_rf0']) == 0
    assert -0.0126 < float(result['sharpe_rf2']) < -0.0124
    assert result['passes_numeric_thresholds'] is False


def test_first_day_loss_retains_full_initial_capital_and_peak():
    # First day's -10% is indispensable. A later +10% returns NAV only to 99.
    result = metrics(['90', '99'])
    assert float(result['daily_return_mean']) == 0
    assert float(result['daily_return_sample_std']) == pytest.approx(0.1414213562373095)
    assert float(result['maximum_drawdown']) == pytest.approx(0.1)
    assert result['daily_return_count'] == 2


def test_252_idle_cash_days_are_undefined_and_cannot_pass():
    result = metrics(['100'] * 252, trade_count=0, exit_batches=0, flat_share_exits=0)
    assert result['saved_days'] == 252
    assert result['sharpe_rf2'] is None and result['sharpe_rf0'] is None
    assert result['numeric_thresholds']['has_funded_trades'] is False
    assert result['passes_numeric_thresholds'] is False and result['formal_target_success'] is False


@pytest.mark.parametrize('navs', [[], ['NaN'], ['0', '1'], ['-1']])
def test_missing_or_invalid_nav_is_never_dropped(navs):
    with pytest.raises(ValueError):
        metrics(navs)
