"""Hand-created account events: never run a strategy or portfolio simulator."""
from copy import deepcopy
from dataclasses import asdict
import importlib.util
from pathlib import Path

import pytest

from quanta_agents.meta_v3.frozen_account_terms import recompute_terms, source_pins, BACKEND
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import digest

DAYS = ['2019-01-02', '2019-01-03', '2019-01-04', '2019-01-07', '2019-01-08', '2019-01-09']
SOURCE = {'ref': 'generated-fixture://terms', 'sha256': 'a' * 64, 'verified': True,
          'evidence_type': 'simulated', 'assumption_ref': 'generated-fixture', 'assumption_sha256': 'b' * 64}


def at(day, clock='15:05:00'):
    return day + 'T' + clock + '+08:00'


def generated_account():
    ca, portfolio, lm = (module(name) for name in ('corporate_action_adapter', 'raw_portfolio_backtest', 'raw_share_ledger'))
    notice = ca.CashDividendAnnouncement(action_id='generated-cash', symbol='sh600004',
        announcement_date='2019-01-01', record_date=DAYS[1], ex_date=DAYS[2], cash_payment_date=DAYS[2],
        gross_cash_per_share='0.17', short_holding_tax_rate='0.20', tax_rule=ca.SUPPORTED_TAX_RULE,
        account_type=ca.ACCOUNT_TYPE, stock_distribution_per_share='0', stock_distribution_kind='none',
        rights_issue=False, implementation_status='implementation_notice', source_url='fixture://generated-notice',
        source_sha256='a' * 64, source_fetched_at='2026-09-08T00:00:00+00:00', facts_verified=True)
    adapter = ca.CashDividendAdapter(notice, DAYS, rounding_policy='aggregate_half_up_simulated')
    ledger = lm.RawShareLedger(DAYS, calendar_source=SOURCE, calendar_available_at=at(DAYS[0], '00:00:00'))
    def apply(event):
        assert ledger.apply(event, as_of=event['available_at'])['status'] == 'applied'
    def event(eid, kind, day, data, clock='09:30:00'):
        return dict(event_id=eid, kind=kind, effective_at=at(day, clock), available_at=at(day, clock), source=SOURCE, data=data)
    # These fee amounts are hand-calculated, not obtained from the function under test.
    trade_specs = [(DAYS[0], 'buy', 100, '10.00', '5.02'), (DAYS[4], 'sell', 40, '11.00', '5.45')]
    trades, daily = [], []
    for day in DAYS:
        if day == DAYS[0]:
            apply(event('initial', 'cash_deposit', day, {'amount': '10000.00'}, '07:00:00'))
        if day == DAYS[2]:
            apply(adapter.activation_event(ledger))
        if day == DAYS[3]:
            for item in adapter.settlement_events(ledger):
                apply(item)
        for trade_day, side, quantity, price, total in trade_specs:
            if day != trade_day:
                continue
            data = {'symbol': 'sh600004', 'quantity': quantity, 'raw_price': price, 'fees': total}
            if side == 'sell':
                data['lot_allocations'] = {'buy': quantity}
            apply(event(side, side + '_fill', day, data))
            fees = {'gross_amount': '1000.00' if side == 'buy' else '440.00', 'commission': '5.00',
                'transfer_fee': '0.02' if side == 'buy' else '0.01', 'stamp_duty': '0.00' if side == 'buy' else '0.44',
                'total': total, 'transfer_rate': '0.00002', 'stamp_rate': '0' if side == 'buy' else '0.001',
                'commission_rate': '0.0003', 'commission_minimum': '5.00', 'rounding': 'component_half_up_simulated'}
            trades.append(dict(event_id=side, date=day, side=side, symbol='sh600004', quantity=quantity, raw_price=price, fees=fees))
        if day == DAYS[1]:
            apply(adapter.record_event(ledger))
        if day >= DAYS[2]:
            apply(adapter.tax_assessment_event(ledger, as_of=at(day)))
            if day == DAYS[4]:
                apply(adapter.tax_payment_event(ledger, as_of=at(day)))
        marks = {'sh600004': dict(raw_price='10.00' if day < DAYS[4] else '11.00', effective_at=at(day), available_at=at(day), source=SOURCE)}
        valuation = ca.portfolio_tax_valuation(ledger, [adapter], marks, as_of=at(day))
        row = {key: valuation[key] for key in ('simulated_net_asset_value', 'simulated_net_pnl', 'gross_asset_value',
            'cash_available', 'realized_tax_unpaid', 'remaining_tax_reserve', 'conservative_cash_after_tax_reserve')}
        daily.append(dict(row, date=day, valuation=valuation, fees_paid_cumulative=ledger.snapshot()['fees_paid'],
            cash_receivable_gross=valuation['raw_ledger_valuation']['cash_receivable_gross']))
    terms = {'initial_cash': '10000.00', 'participation_rate': '0.05', 'slippage_fraction': '0.001',
             'corporate_action_rounding_policy': 'aggregate_half_up_simulated'}
    body = {'version': portfolio.VERSION, 'initial_cash': '10000.00', 'calendar': DAYS[:], 'replay_dates': DAYS[:],
        'genesis': ledger.genesis, 'journal': ledger.journal, 'daily': daily, 'trades': trades, 'final_snapshot': ledger.snapshot(),
        'manifest': {'policy': terms, 'policy_sha256': digest(terms), 'corporate_actions': [adapter.manifest()]}}
    plan = {'version': BACKEND, 'calendar': DAYS[:], 'codes': ['sh600004'], 'initial_cash': '10000.00',
        'corporate_actions': [asdict(notice)], 'engine_sources': source_pins(),
        'policy': {'rounding_policy': 'aggregate_half_up_simulated', 'participation_rate': '0.05', 'slippage_fraction': '0.001'}}
    return plan, body


def review(plan, body):
    unsigned = {key: value for key, value in plan.items() if key != 'plan_sha256'}
    sha = digest(unsigned)
    return recompute_terms(dict(unsigned, plan_sha256=sha), body, expected_plan_sha256=sha,
                           expected_result_sha256=digest(body), input_kind='generated_fixture')


def test_hand_cash_dividend_partial_sale_tax_and_fee_arithmetic_without_simulator(monkeypatch):
    portfolio = module('raw_portfolio_backtest')
    monkeypatch.setattr(portfolio, 'simulate_raw_portfolio', lambda **_: pytest.fail('simulation forbidden'))
    plan, body = generated_account(); before = deepcopy((plan, body))
    result = review(plan, body)
    assert result['days_checked'] == 6 and result['fills_checked'] == 2 and result['fees_paid'] == '10.47'
    assert result['daily_rows'][2]['remaining_tax_reserve'] == '3.40'
    assert result['daily_rows'][-1]['remaining_tax_reserve'] == '2.04'
    assert result['daily_rows'][-1]['realized_tax_unpaid'] == '0.00'
    assert result['daily_rows'][-1]['simulated_net_asset_value'] == '10103.13'
    assert (plan, body) == before
    assert result['algorithmically_independent'] is result['execution_valid'] is result['formal_target_success'] is False
    assert result['sources_authenticated'] is result['custody_verified_by_this_function'] is False


@pytest.mark.parametrize('fault', ['fee_total', 'fee_component', 'fee_rate', 'fee_bool', 'fee_omitted', 'trade_missing',
    'trade_duplicate', 'tax_reserve', 'tax_report', 'projected_tax', 'cash', 'daily_missing', 'daily_duplicate',
    'calendar', 'capital', 'action_missing', 'rounding', 'source_pin', 'wrong_backend', 'archive_policy', 'journal_missing'])
def test_inconsistent_saved_terms_rejected_even_with_rehashed_result(fault):
    plan, body = generated_account()
    if fault.startswith('fee_'):
        fees = body['trades'][0]['fees']
        if fault == 'fee_omitted':
            fees.pop('transfer_fee')
        else:
            field, value = {'fee_total': ('total', '5.03'), 'fee_component': ('commission', '5.02'),
                'fee_rate': ('commission_rate', '0'), 'fee_bool': ('transfer_fee', True)}[fault]
            fees[field] = value
    elif fault == 'trade_missing': body['trades'].pop()
    elif fault == 'trade_duplicate': body['trades'].append(deepcopy(body['trades'][0]))
    elif fault == 'tax_reserve':
        body['daily'][-1]['valuation']['remaining_tax_reserve'] = '0.00'
        body['daily'][-1]['valuation']['estimated_total_tax_unpaid'] = '0.00'
    elif fault == 'tax_report': body['daily'][-1]['valuation']['reserve_reports'][0]['tax_paid'] = '0.00'
    elif fault == 'projected_tax': body['daily'][-1]['remaining_tax_reserve'] = '0.00'
    elif fault == 'cash': body['daily'][-1]['cash_available'] = '999999.00'
    elif fault == 'daily_missing': body['daily'].pop()
    elif fault == 'daily_duplicate': body['daily'][-1] = deepcopy(body['daily'][-2])
    elif fault == 'calendar': plan['calendar'].pop()
    elif fault == 'capital': plan['initial_cash'] = '1000.00'
    elif fault == 'action_missing':
        plan['corporate_actions'] = []; body['manifest']['corporate_actions'] = []
    elif fault == 'rounding': plan['policy']['rounding_policy'] = 'exact_only'
    elif fault == 'source_pin': plan['engine_sources']['raw_share_ledger.py'] = 'a' * 64
    elif fault == 'wrong_backend': plan['version'] = 'meta-v3-structural-execution-v1'
    elif fault == 'archive_policy': plan['archive_storage_policy'] = {'version': 'zlib_records_v1'}
    elif fault == 'journal_missing': body['journal'].pop()
    with pytest.raises(ValueError):
        review(plan, body)


def test_expected_result_hash_cannot_be_replaced_by_verified_flag():
    plan, body = generated_account(); sha = digest(plan)
    with pytest.raises(ValueError, match='result hash mismatch'):
        recompute_terms(dict(plan, plan_sha256=sha), body, expected_plan_sha256=sha,
                        expected_result_sha256='0' * 64, input_kind='caller_bound_saved_records')
    with pytest.raises(ValueError, match='explicit input kind'):
        recompute_terms(dict(plan, plan_sha256=sha), body, expected_plan_sha256=sha,
                        expected_result_sha256=digest(body), input_kind={'verified': True})


def test_cli_rejects_relabelled_spec_before_opening_raw_store(monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts/audit_frozen_account_terms.py'
    spec = importlib.util.spec_from_file_location('generated_terms_cli', path)
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    frozen = {'version': 'generated-only-fixture', 'original_final_outcome': 'abstain'}
    monkeypatch.setattr(cli, 'build_spec', lambda: deepcopy(frozen))
    from quanta_agents.meta_v3 import saved_execution
    monkeypatch.setattr(saved_execution.SavedRawResearch, '__init__', lambda *_: pytest.fail('raw store must remain unopened'))
    with pytest.raises(ValueError, match='specification drift'):
        cli.audit_saved_candidate(dict(frozen, original_final_outcome='strategy_for_development'))


def test_cli_build_spec_is_not_the_account_recomputation(monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'scripts/audit_frozen_account_terms.py'
    spec = importlib.util.spec_from_file_location('generated_terms_cli_build', path)
    cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
    monkeypatch.setattr(cli, 'recompute_terms', lambda *_a, **_k: pytest.fail('spec build cannot audit account'))
    monkeypatch.setattr(cli, '_prior_binding', lambda: (_ for _ in ()).throw(ValueError('generated stop before actual files')))
    with pytest.raises(ValueError, match='generated stop'):
        cli.build_spec()
