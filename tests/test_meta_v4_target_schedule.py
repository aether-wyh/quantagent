"""Generated-only schedule and complete-account counterexamples."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import real_program, target_schedule as schedule
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from quanta_agents.meta_v3.research_tools import ResearchTools
from quanta_agents.meta_v3.runtime import verify_case_sources
from quanta_agents.meta_v3.source_admission import preflight_case
from test_meta_v3_real_entry import case as generated_case, program


def policy(case, unavailable=()):
    days = case['decision_fixture']['calendar']
    return {'version': schedule.VERSION, 'interval_sessions': 5, 'anchor_signal_dates': days[::5],
        'anchor_inputs': [{'signal_date': day, 'status': 'unavailable' if day in unavailable else 'ready',
            'reason': 'Generated common-input failure' if day in unavailable else None,
            'input_receipt_sha256': digest({'generated_only': True, 'date': day})} for day in days[::5]],
        'off_anchor': 'hold_actual_shares', 'unavailable_action': 'zero_targets_at_original_anchor',
        'terminal': 'penultimate_signal_zero_next_session'}


def inputs(tmp_path):
    case = generated_case(tmp_path)
    case['execution_backend'] = 'v3_streamed_001'
    case[schedule.KEY] = policy(case)
    return case


def ordinary(case):
    compiled = real_program.validate_program(program(), public_field_contract=case['decision_fixture']['fields'])
    return real_program.build_targets(compiled, decision_fixture=case['decision_fixture'], frozen_policy=real_program.POLICY)


def execute(case, path):
    tools = ResearchTools(path, 'engineering', case, [])
    public = tools.execute('candidate', 'develop_strategy', {'program': program()})
    artifact = json.loads((tools.folder / 'candidate/artifact.json').read_text(encoding='utf-8'))
    target = json.loads((tools.folder / 'candidate/workbench/targets.json').read_text(encoding='utf-8'))
    return tools, public, artifact, target


def test_without_policy_returns_original_artifact_and_contract(tmp_path):
    case = generated_case(tmp_path); target = ordinary(case)
    assert schedule.apply_schedule(target, case=case) is target
    assert schedule.validate_case_policy(case) is None
    assert 'target_schedule' not in ResearchTools(tmp_path/'stage', 'engineering', case, []).contract()


def test_complete_grid_fixed_anchors_unavailable_and_terminal_precedence(tmp_path):
    case = inputs(tmp_path); days = case['decision_fixture']['calendar']
    case[schedule.KEY] = policy(case, [days[5], days[10]])
    before = ordinary(case); before_hash = digest(before)
    result = schedule.apply_schedule(before, case=case)
    assert {r['signal_date'] for r in result['targets']} == {days[0], days[5], days[10]}
    assert all(r['target_weight'] == '0' for r in result['targets'] if r['signal_date'] in (days[5], days[10]))
    assert all('mandatory_terminal_liquidation' in r['reasons'] for r in result['decisions'] if r['signal_date'] == days[-2])
    assert len(result['targets']) + len(result['omitted_target_rows']) == len(before['targets'])
    assert digest(before) == before_hash and result['untraded_terminal_signals'] == before['untraded_terminal_signals']
    assert result['target_schedule']['input_receipt_authentication'] is False
    assert result['target_schedule']['formal_target_success'] is False


def test_last_calendar_anchor_is_retained_but_never_dispatched_without_next_session(tmp_path):
    case = inputs(tmp_path); table = case['decision_fixture']
    table['calendar'] = table['calendar'][:-1]
    table['field_rows'] = [row for row in table['field_rows'] if row['session'] in table['calendar']]
    table['eligibility_rows'] = [row for row in table['eligibility_rows'] if row['session'] in table['calendar']]
    case[schedule.KEY] = policy(case)
    result = schedule.apply_schedule(ordinary(case), case=case); days = table['calendar']
    assert days[-1] in result['target_schedule']['policy']['anchor_signal_dates']
    assert {row['signal_date'] for row in result['targets']} == {days[0], days[5], days[-2]}
    assert all(row['signal_date'] == days[-1] for row in result['untraded_terminal_signals'])


@pytest.mark.parametrize('mutation', ['missing_key','extra_key','none','interval_bool','shift_anchor','drop_anchor',
    'missing_input','duplicate_input','unknown_status','missing_reason','false_ready_reason','bad_hash','wrong_hold',
    'wrong_terminal','wrong_backend','synthetic','sealed'])
def test_invalid_contracts_are_rejected_before_source_reads(tmp_path, monkeypatch, mutation):
    case = inputs(tmp_path); value = case[schedule.KEY]
    if mutation == 'missing_key': value.pop('terminal')
    if mutation == 'extra_key': value['escape'] = True
    if mutation == 'none': case[schedule.KEY] = None
    if mutation == 'interval_bool': value['interval_sessions'] = True
    if mutation == 'shift_anchor': value['anchor_signal_dates'][0] = case['decision_fixture']['calendar'][1]
    if mutation == 'drop_anchor': value['anchor_signal_dates'].pop()
    if mutation == 'missing_input': value['anchor_inputs'].pop()
    if mutation == 'duplicate_input': value['anchor_inputs'][1] = deepcopy(value['anchor_inputs'][0])
    if mutation == 'unknown_status': value['anchor_inputs'][0]['status'] = 'unknown'
    if mutation == 'missing_reason': value['anchor_inputs'][0]['status'] = 'unavailable'
    if mutation == 'false_ready_reason': value['anchor_inputs'][0]['reason'] = 'cannot know'
    if mutation == 'bad_hash': value['anchor_inputs'][0]['input_receipt_sha256'] = 'not-a-hash'
    if mutation == 'wrong_hold': value['off_anchor'] = 'daily_rebalance'
    if mutation == 'wrong_terminal': value['terminal'] = 'omit'
    if mutation == 'wrong_backend': case['execution_backend'] = None
    if mutation == 'synthetic': case['research_class'] = 'synthetic_calibration'
    if mutation == 'sealed': case['decision_fixture']['calendar'] = ['2024' + d[4:] for d in case['decision_fixture']['calendar']]
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('opened source before policy refusal'))
    with pytest.raises(ValueError): verify_case_sources({'case':case,'case_hash':digest(case)})
    with pytest.raises(ValueError): ResearchTools(tmp_path/'rejected', 'engineering', case, [])
    assert not (tmp_path/'rejected').exists()


@pytest.mark.parametrize('mutation', ['missing_target','reorder','nonzero_terminal','decision_mismatch','changed_clock','case_hash','invalid_decimal'])
def test_adapter_refuses_incomplete_or_changed_ordinary_artifact(tmp_path, mutation):
    case = inputs(tmp_path); target = ordinary(case)
    if mutation == 'missing_target': target['targets'].pop()
    if mutation == 'reorder': target['targets'].reverse()
    if mutation == 'nonzero_terminal':
        target['targets'][-1]['target_weight'] = target['decisions'][-1]['target_weight'] = '.4'
    if mutation == 'decision_mismatch': target['decisions'][0]['target_weight'] = '0'
    if mutation == 'changed_clock': target['targets'][0]['available_at'] = '2024-01-01T15:10:00+08:00'
    if mutation == 'case_hash': target['decision_table_hash'] = '0'*64
    if mutation == 'invalid_decimal': target['targets'][0]['target_weight'] = 'not-decimal'
    with pytest.raises(ValueError): schedule.apply_schedule(target, case=case)


def test_streamed_account_holds_actual_shares_between_anchors_and_keeps_every_cash_day(tmp_path):
    case = inputs(tmp_path/'source'); case['initial_cash'] = '1000000.00'
    days = case['decision_fixture']['calendar']; case[schedule.KEY] = policy(case, [days[5]])
    tools, public, artifact, target = execute(case, tmp_path/'stage')
    assert public['public']['raw_status'] == 'completed_mechanical', artifact['raw'].get('error')
    body = artifact['raw']['result']
    assert [r['date'] for r in body['daily']] == days
    assert body['initial_cash'] == body['final_snapshot']['external_cash_flow'] == '1000000.00'
    expected_order_days = {days[1], days[6], days[-1]}
    assert all(r['trade_date'] in expected_order_days for r in body['orders'])
    first_holding = body['daily'][1]['holdings']
    assert first_holding and all(body['daily'][i]['holdings'] == first_holding for i in range(2,6))
    assert all(body['daily'][i]['orders'] == 0 for i in (2,3,4,5,7,8,9,10))
    assert body['daily'][6]['holdings'] == body['daily'][-1]['holdings'] == {}
    assert Decimal(body['final_snapshot']['fees_paid']) > 0
    assert sum(r['event']['kind'] == 'cash_deposit' for r in body['journal']) == 1
    assert tools.contract()['target_schedule']['input_receipt_authentication'] is False
    assert artifact['workbench']['formal_target_success'] is False


def test_scheduled_cash_intent_cannot_release_halted_holdings_or_fake_final_liquidation(tmp_path):
    from test_meta_v3_structural_execution import example, public_case, save_rows
    values = example(tmp_path); days, codes = values['calendar'], values['codes']
    episode = values['market_schedule']['episodes'][0]
    episode.update(first_halted=days[5], first_resumed=days[7])
    review_path = Path(episode['review_path'])
    review = json.loads(review_path.read_text(encoding='utf-8'))
    review.update(first_halted=days[5], first_resumed=days[7])
    review_path.write_text(json.dumps(review), encoding='utf-8')
    episode['review_sha256'] = hashlib.sha256(review_path.read_bytes()).hexdigest()
    def quotes(rows):
        for i, row in enumerate(rows):
            if i in (5,6):
                row.update(raw_open=None, raw_close=None, raw_prev_close=None, volume=None, stock_name=None)
                row['raw_price_text'] = dict.fromkeys(('raw_open','raw_close','raw_prev_close'))
            else:
                price = 9.2 if i == 7 else 10.
                row.update(raw_open=price, raw_close=price, raw_prev_close=10., volume=1000000, stock_name='Generated engineering')
                row['raw_price_text'] = {key:str(row[key]) for key in ('raw_open','raw_close','raw_prev_close')}
    save_rows(values, codes[0], quotes)
    case = public_case(values); case[schedule.KEY] = policy(case, [days[5]])
    _, public, artifact, target = execute(case, tmp_path/'stage')
    assert public['public']['raw_status'] == 'completed_mechanical', artifact['raw'].get('error')
    body = artifact['raw']['result']; quantity = body['daily'][1]['holdings'][codes[0]]
    assert [row['date'] for row in body['daily']] == days
    assert quantity > 0 and body['daily'][6]['holdings'][codes[0]] == quantity
    assert body['daily'][6]['halted_position_estimates'][codes[0]]['tradable'] is False
    assert Decimal(body['daily'][6]['estimated_locked_share_value']) == quantity * Decimal('10')
    assert Decimal(body['daily'][6]['simulated_net_asset_value']) > Decimal(body['daily'][6]['cash_available'])
    exits = [o for o in body['orders'] if o['symbol'] == codes[0] and o['trade_date'] in days[6:]]
    assert len(exits) == 2 and all(o['status'] == 'rejected' and o['filled_quantity'] == 0 for o in exits)
    assert 'suspension' in exits[0]['reasons'][0] and 'previous-session' in exits[1]['reasons'][0]
    assert body['daily'][-1]['holdings'][codes[0]] == quantity
    assert all(row['target_weight'] == '0' for row in target['targets'] if row['signal_date'] in days[5:7])
    assert artifact['workbench']['formal_target_success'] is False
