"""Generated prices exercise the real adapter; never market or model evidence."""
from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal
import gzip
import hashlib
import json
import math
from pathlib import Path

import pytest

from quanta_agents.meta_v3 import architecture_contract as ac, generator_controls as gc
from quanta_agents.meta_v3 import registered_producer as rp, study_registry as sr
from quanta_agents.meta_v3 import process_envelope as pe, study_allocation as sa
from quanta_agents.meta_v3.closing import ClosingPolicy
from quanta_agents.meta_v3.ledger import digest
from quanta_agents.meta_v3.runtime import source_pins
from test_meta_v3_real_entry import case as real_adapter_case, program
from test_meta_v3_generator_controls import SEED


def inputs(tmp_path, values):
    case = real_adapter_case(tmp_path)
    case['initial_cash'] = '1000000.00'
    case['execution_backend'] = 'v3_streamed_001'
    # Deliberate monotone engineering prices, specified before any execution.
    prices = {}
    for artifact in case['raw_source_bindings']['source_artifacts']:
        path = Path(artifact['root']) / artifact['rows_file']
        rows = json.loads(gzip.decompress(path.read_bytes()))
        for i, row in enumerate(rows):
            price, previous = Decimal(10) + Decimal(i) / 5, Decimal(10) + Decimal(max(i-1, 0)) / 5
            text = {'raw_open': str(price), 'raw_close': str(price), 'raw_prev_close': str(previous)}
            row.update(**text, raw_price_text=text, stock_name='Generated engineering rising stock')
            prices[row['date'], row['code']] = float(price)
        payload = gzip.compress(json.dumps(rows).encode(), mtime=0)
        path.write_bytes(payload); artifact['rows_sha256'] = hashlib.sha256(payload).hexdigest()
    for row in case['decision_fixture']['field_rows']:
        if row['field'] == 'close':
            row['value'] = prices[row['session'], row['symbol']]
    case['batch_policy'] = {'version': 'bounded_batch_v1', 'max_candidates_total': len(values),
        'max_scan_cells_total': 4096, 'max_wall_seconds': 120, 'output_stop_threshold_bytes': 268435456,
        'field_semantics': {f['name']: {'unit': f['unit'], 'raw_precision': 'generated engineering decimal',
            'digit_derivation': None} for f in case['decision_fixture']['fields']}}
    template = program(); template['target_weight_expression'] = '{{weight}}'
    return case, {'program_template': template, 'parameters': {'weight': list(values)}, 'axis_order': ['weight']}


def stage(tmp_path, monkeypatch, values=(.2, .2)):
    monkeypatch.setattr(sr, 'REGISTRY', tmp_path / 'canonical.sqlite3')
    case, space = inputs(tmp_path / 'generated', values)
    contract = rp.make_real_contract(space, count=len(values), seed=SEED)
    tasks = {'producer': {'case': case, 'case_hash': digest(case),
        'idea': 'Generated prices test real-adapter mechanics only', 'documents': []}}
    architecture = ac.make('fixed_template_search')
    policy = ClosingPolicy(task_calls=3, stage_calls=3)
    root = tmp_path / 'fixed'
    entry = Path(__file__).parent / 'helpers/meta_v3_producer_fixture.py'
    budget = {'launches': 2, 'cpu_ms': 60000, 'io_transfer_bytes': 1073741824,
        'closing_cpu_ms': 1000, 'closing_io_transfer_bytes': 1048576}
    tool = {'actions': 1, 'candidates': len(values), 'scan_cells': 4096, 'comparisons': 0,
        'wall_ms': 120000, 'controller_cpu_ms': 60000, 'retained_output_bytes': 268435456}
    trial = {'id': 'fixed', 'root': str(root.resolve()), 'case_hash': digest(case),
        'architecture_contract': architecture, 'architecture_hash': digest(architecture), 'repeat': 1,
        'tasks_hash': digest(tasks), 'source_pins_hash': digest(source_pins()), 'policy': asdict(policy),
        'duration_seconds': 7200, 'tool_budget': tool, 'producer_contract': contract,
        'process_envelope': {'version': pe.VERSION, 'entrypoint': str(entry.resolve()),
            'entrypoint_sha256': hashlib.sha256(entry.read_bytes()).hexdigest(),
            'arguments': ['--root', str(root), '--registry', str(sr.REGISTRY), '--mode', 'full'], 'budget': budget}}
    sr.freeze({'study_id': 'generated_real_fixed', 'trials': [trial], 'allocation': {
        'version': sa.VERSION, 'model_tokens': policy.stage_tokens, 'model_calls': policy.stage_calls,
        'tool_resources': tool, 'process_resources': {k: budget[k] for k in pe.LIMITS}}})
    ledger = sr.create_stage(root, 'generated_real_fixed', 'fixed', policy=policy, tasks=tasks,
        duration_seconds=7200, provenance={'source_pins': source_pins(), 'fixture_only': True,
                                          'architecture_contract': architecture})
    return ledger, case, contract


@pytest.mark.parametrize('values,outcome,statuses', [
    ((.2, .2), 'development_candidate', ['completed', 'reused']),
    ((0, 0), 'abstain', ['completed', 'reused']),
    ((2, 2), 'abstain', ['failed', 'reused'])])
def test_native_registered_real_adapter_keeps_every_slot_and_selects_or_abstains(tmp_path, monkeypatch, values, outcome, statuses):
    ledger, case, contract = stage(tmp_path, monkeypatch, values)
    run = rp.dispatch(ledger.root)
    assert run['exit_code'] == 0, (ledger.root / 'process_runs/1/worker.log').read_text(encoding='utf-8', errors='replace')
    assert run['metrics']['cpu_ms'] > 0 and run['metrics']['total_processes'] >= 3
    state = rp.status(ledger.root); result = state['record']['receipt']['result']
    assert [r['status'] for r in result['candidates']] == statuses
    selection = result['development_selection']
    assert selection['outcome'] == outcome and selection['all_candidates_settled']
    assert len(selection['candidate_reviews']) == len(values)
    if outcome == 'development_candidate':
        assert selection['selected_candidate_id'] == 'c001'
        assert selection['selected_metrics']['initial_cash'] == case['initial_cash']
        assert selection['selected_metrics']['daily_return_count'] == 12
        assert Decimal(selection['selected_metrics']['sharpe_rf2']) > 0
        assert all(r['proof']['saved_raw_ledger_reconciled'] for r in selection['candidate_reviews'])
        from quanta_agents.meta_v3 import saved_execution
        monkeypatch.setattr(saved_execution, 'simulate_streamed_portfolio', lambda **_: pytest.fail('selection reran strategy'))
        folder = ledger.root / 'control/arms/fixed/batches/frozen'
        registration = json.loads((folder / 'registration.json').read_text(encoding='utf-8'))
        assert gc.select_development(folder, registration, case, result, contract['selection']) == selection
        original_reconcile = saved_execution.SavedRawResearch.reconcile_saved_only
        def changed_reconcile(self, **kwargs):
            changed = deepcopy(original_reconcile(self, **kwargs))
            changed['result']['initial_cash'] = '1.00'
            return changed
        monkeypatch.setattr(saved_execution.SavedRawResearch, 'reconcile_saved_only', changed_reconcile)
        with pytest.raises(ValueError, match='differs from its saved raw ledger'):
            gc.select_development(folder, registration, case, result, contract['selection'])
    else:
        assert selection['selected_candidate_id'] is None
    shared = sr.snapshot('generated_real_fixed')
    assert shared['known_tokens'] == 0 and not shared['calls']
    assert shared['study_allocation']['grants'][0]['tool_used']['candidates'] == len(values)
    assert state['record']['receipt']['model_final'] is False and not selection['formal_target_success']
    original = {p: p.read_bytes() for p in ledger.root.rglob('worker_result.json')}
    with pytest.raises(ValueError, match='already started'):
        rp.dispatch(ledger.root)
    assert original == {p: p.read_bytes() for p in original}


def test_metric_uses_cash_days_first_day_full_capital_and_sample_deviation():
    case = {'initial_cash': '100', 'decision_fixture': {'calendar': ['d1', 'd2', 'd3']}}
    body = {'initial_cash': '100', 'final_snapshot': {'external_cash_flow': '100'},
        'daily': [{'date': d, 'simulated_net_asset_value': value}
                  for d, value in zip(case['decision_fixture']['calendar'], ['100', '110', '99'])],
        'trades': [{'quantity': 1, 'side': 'buy'}, {'quantity': 1, 'side': 'sell'}]}
    result = gc.development_metrics(body, case)
    # Returns are exactly 0,+.1,-.1: mean=0, sample sd=.1, DD=.1.
    assert result['daily_return_count'] == 3 and Decimal(result['sharpe_rf0']) == 0
    expected = -(1.02 ** (1 / 252) - 1) * math.sqrt(252) / .1
    assert math.isclose(float(result['sharpe_rf2']), expected, rel_tol=1e-9)
    assert Decimal(result['maximum_drawdown']) == Decimal('.1')
    assert Decimal(result['sharpe_rf2']) < 0 and result['filled_trade_count'] == 2
    body['daily'].pop(0)
    with pytest.raises(ValueError, match='incomplete daily calendar'):
        gc.development_metrics(body, case)


@pytest.mark.parametrize('change', ['selection', 'random', 'class', 'sealed'])
def test_real_opt_in_cannot_change_rule_arm_or_source_scope(tmp_path, change):
    case, space = inputs(tmp_path, (.2,))
    contract = {'kind': rp.REAL_VERSION, 'arm': 'fixed', 'space': space,
        'count': 1, 'seed': SEED, 'selection': gc.selection_policy()}
    if change == 'selection':
        contract['selection']['annual_risk_free'] = '0'
    elif change == 'random':
        contract['arm'] = 'random'
    elif change == 'class':
        case['research_class'] = 'sealed_holdout'
    else:
        case['decision_fixture']['calendar'][0] = '2024-01-01'
    with pytest.raises(ValueError):
        rp.validate_contract(contract)
        gc.validate_development_case(case)


def test_unstarted_slot_forces_abstention_without_reading_results(tmp_path):
    case, _ = inputs(tmp_path, (.2,))
    registration = {'candidates': [{'candidate_id': 'c001', 'program_hash': 'f'*64}]}
    result = {'registration_hash': digest(registration),
        'candidates': [{'candidate_id': 'c001', 'status': 'not_started'}]}
    selected = gc.select_development(tmp_path, registration, case, result, gc.selection_policy())
    assert selected['outcome'] == 'abstain' and not selected['all_candidates_settled']
    assert selected['reason'] == 'unsettled_or_unstarted_frozen_candidate'
