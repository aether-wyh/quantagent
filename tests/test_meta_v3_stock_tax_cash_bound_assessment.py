"""Recorded assessments cannot silently exceed a cash-protection envelope."""
import pytest

from quanta_agents.meta_v3.stock_distribution import AdapterError
from test_meta_v3_stock_tax_cash_bound import prepared, bound, tax
from test_meta_v3_stock_distribution import apply, event, DAYS


@pytest.mark.parametrize('final', [False, True])
@pytest.mark.parametrize('paid', ['0.00', '10.00'])
def test_recorded_assessment_above_envelope_refuses_spendable_cash(tmp_path, final, paid):
    adapter, ledger, _ = prepared(tmp_path)
    tax(ledger, '61.00', final=final)
    if paid != '0.00':
        apply(ledger, event('partial-payment', 'tax_paid', DAYS[6],
            {'action_id': 'generated-mixed', 'amount': paid}, '15:05:00'))
    before = ledger.snapshot()
    assert before['actions']['generated-mixed']['tax_due'] == '61.00'
    with pytest.raises(AdapterError, match='assessment contradicts'):
        bound(ledger, [adapter])
    assert ledger.snapshot() == before


@pytest.mark.parametrize('assessed,paid,final,reserve,unpaid', [
    ('60.00', '0.00', False, '60.00', '60.00'),
    ('60.00', '10.00', True, '50.00', '50.00'),
    ('59.00', '10.00', False, '50.00', '49.00'),
])
def test_compatible_assessment_is_visible_without_releasing_reserve(
        tmp_path, assessed, paid, final, reserve, unpaid):
    adapter, ledger, _ = prepared(tmp_path)
    tax(ledger, assessed, final=final)
    if paid != '0.00':
        apply(ledger, event('partial-payment', 'tax_paid', DAYS[6],
            {'action_id': 'generated-mixed', 'amount': paid}, '15:05:00'))
    before = ledger.snapshot()
    result = bound(ledger, [adapter])
    assert result['total_stock_tax_cash_reserve'] == reserve
    assert result['spendable_cash_after_all_tax_reserves'] == '1040.00'
    assert result['actions'][0]['recorded_total_tax_assessed'] == assessed
    assert result['actions'][0]['recorded_tax_unpaid'] == unpaid
    assert result['actual_tax_assessed_by_this_function'] is False
    assert result['research_execution_ready'] is False
    assert result['net_asset_value'] is None
    assert ledger.snapshot() == before
