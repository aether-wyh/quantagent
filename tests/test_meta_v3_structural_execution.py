"""Generated economic counterexamples; no real strategy or source certification."""
from copy import deepcopy
from decimal import Decimal as D
import gzip
import hashlib
import json

import pandas as pd
import pytest

from quanta_agents.meta_v3 import structural_execution as engine
from quanta_agents.meta_v3 import saved_execution as old
from quanta_agents.meta_v3.suspension_market import POLICY, SuspensionMarket
from test_meta_v3_streamed_execution import inputs, run


def save_rows(values, code, edit):
    artifact = next(x for x in values['source_artifacts'] if x['code'] == code)
    from pathlib import Path
    path = Path(artifact['root']) / artifact['rows_file']
    rows = json.loads(gzip.decompress(path.read_bytes()))
    edit(rows)
    raw = gzip.compress(json.dumps(rows).encode(), mtime=0)
    path.write_bytes(raw)
    artifact['rows_sha256'] = hashlib.sha256(raw).hexdigest()


def example(tmp_path):
    values = inputs(tmp_path / 'inputs', 8)
    days = values['calendar']
    doc = tmp_path / 'generated.pdf'
    doc.write_bytes(b'%PDF-generated engineering input; no historical notice claim')
    facts = {'symbol': values['codes'][0], 'first_halted': days[3], 'first_resumed': days[5],
             'source_document_date': '2020-01-01', 'document_sha256': hashlib.sha256(doc.read_bytes()).hexdigest()}
    review = tmp_path / 'generated_review.json'
    review.write_text(json.dumps({**facts, 'kind': 'suspension_event_source_review',
                                  'facts_verified': True, 'reviewed_pages': [1],
                                  'fixture_only': True}), encoding='utf-8')
    episode = {**facts, 'document_path': str(doc), 'review_path': str(review),
               'review_sha256': hashlib.sha256(review.read_bytes()).hexdigest()}
    values['market_schedule'] = {'policy': deepcopy(POLICY), 'episodes': [episode]}
    def prices(rows):
        for i, row in enumerate(rows):
            if i in (3, 4):
                row.update(raw_open=None, raw_close=None, raw_prev_close=None, volume=None, stock_name=None)
                row['raw_price_text'] = {k: None for k in ('raw_open', 'raw_close', 'raw_prev_close')}
            elif i >= 5:
                row.update(raw_open=9.2, raw_close=9.2, raw_prev_close=10. if i == 5 else 9.2)
                row['raw_price_text'] = {k: str(row[k]) for k in ('raw_open', 'raw_close', 'raw_prev_close')}
    save_rows(values, values['codes'][0], prices)
    values['targets'] = []
    for i, code, weight in [(1, values['codes'][0], '0.4'), (3, values['codes'][0], '0'),
                            (4, values['codes'][0], '0.5'), (5, values['codes'][0], '0'),
                            (6, values['codes'][0], '0'), (3, values['codes'][1], '0.8'),
                            (7, values['codes'][1], '0')]:
        values['targets'].append({'symbol': code, 'signal_date': days[i-1], 'trade_date': days[i],
                                  'available_at': days[i-1]+'T15:10:00+08:00', 'target_weight': weight})
    return values


def test_halt_keeps_capital_no_fills_then_recognizes_resumption_loss(tmp_path, monkeypatch):
    values = example(tmp_path)
    job, plan, saved = run(tmp_path/'account', engine, values)
    assert saved['status'] == 'completed_mechanical', saved.get('error')
    result = saved['result']; days = values['calendar']; code = values['codes'][0]
    quantity = result['daily'][2]['holdings'][code]
    assert len(result['daily']) == 8 and result['manifest']['input_stock_days'] == 16
    assert all(row['stock_day_denominator'] == 2 for row in result['daily'])
    for i in (3, 4):
        row = result['daily'][i]
        assert row['holdings'][code] == quantity
        mark = row['halted_position_estimates'][code]
        assert mark['last_observed_quote_date'] == days[2]
        assert mark['stale_calendar_sessions'] == i-2
        assert mark['tradable'] is False and mark['observed_current_price'] is False
        assert D(row['estimated_locked_share_value']) == quantity * D('10')
    blocked = [o for o in result['orders'] if o['symbol'] == code and o['trade_date'] in days[3:6]]
    assert len(blocked) == 3 and all(o['filled_quantity'] == 0 and o['status'] == 'rejected' for o in blocked)
    assert all('suspension' in o['reasons'][0] for o in blocked[:2])
    assert 'previous-session' in blocked[2]['reasons'][0]
    assert not [t for t in result['trades'] if t['symbol'] == code and t['date'] in days[3:6]]
    # A second stock competes for actual free cash; locked value is not buying power.
    second_buy = next(t for t in result['trades'] if t['symbol'] != code and t['side'] == 'buy')
    assert D(second_buy['raw_price'])*second_buy['quantity'] + D(second_buy['fees']['total']) <= D(result['daily'][2]['cash_available'])
    assert D(result['daily'][5]['gross_asset_value']) - D(result['daily'][4]['gross_asset_value']) == -quantity*D('.8')
    assert result['daily'][5]['halted_position_estimates'] == {}
    # Independently reconcile all cash and full initial capital including fees.
    cash = D('1000000')
    for trade in result['trades']:
        cash += (1 if trade['side']=='sell' else -1)*D(trade['raw_price'])*trade['quantity'] - D(trade['fees']['total'])
    assert cash == D(result['final_snapshot']['cash']) < D('1000000')
    assert result['daily'][-1]['holdings'] == {}
    assert sum(x['event']['kind']=='cash_deposit' for x in result['journal']) == 1
    monkeypatch.setattr(engine, 'simulate_streamed_portfolio', lambda **kw: pytest.fail('reexecuted'))
    monkeypatch.setattr(SuspensionMarket, 'verify_sources', lambda *a: pytest.fail('reopened source'))
    monkeypatch.setattr(engine, '_load_saved', lambda *a: pytest.fail('reopened quotes'))
    assert job.reconcile_saved_only(expected_plan_sha256=plan['plan_sha256']) == saved


def test_no_halt_economics_preserve_cash_kernel(tmp_path):
    values = inputs(tmp_path/'inputs', 8)
    _, _, base = run(tmp_path/'base', old, values)
    _, _, new = run(tmp_path/'new', engine, values)
    assert base['status'] == new['status'] == 'completed_mechanical'
    for a, b in zip(base['result']['daily'], new['result']['daily']):
        for field in ('simulated_net_asset_value','cash_available','fees_paid_cumulative','holdings'):
            assert a[field] == b[field]
    for a, b in zip(base['result']['trades'], new['result']['trades']):
        for field in ('date','side','symbol','quantity','raw_price','fees'):
            assert a[field] == b[field]


@pytest.mark.parametrize('change', ['quote','volume','anchor','missing_resume_close','source_hash'])
def test_gaps_and_contradictions_never_become_halt_fills(tmp_path, change):
    values = example(tmp_path); code = values['codes'][0]
    if change == 'source_hash':
        values['market_schedule']['episodes'][0]['review_sha256'] = '0'*64
    else:
        def alter(rows):
            if change == 'quote':
                rows[3]['raw_close'] = 10.; rows[3]['raw_price_text']['raw_close'] = '10.00'
            if change == 'volume': rows[3]['volume'] = 100
            if change == 'anchor': rows[2]['raw_close'] = None; rows[2]['raw_price_text']['raw_close'] = None
            if change == 'missing_resume_close': rows[5]['raw_close'] = None; rows[5]['raw_price_text']['raw_close'] = None
        save_rows(values, code, alter)
    _, _, result = run(tmp_path/'account', engine, values)
    assert result['status'] == 'failed' and result['result'] is None
    if change == 'missing_resume_close':
        assert result['valuation_complete_through'] == values['calendar'][4]
        assert any(x['quantity'] for x in result['partial']['snapshot']['lots'].values())
        assert result['partial']['snapshot']['external_cash_flow'] == '1000000.00'


def test_corporate_action_in_halt_requires_revaluation_and_unknown_coverage_stops(tmp_path):
    values = example(tmp_path)
    with pytest.raises(ValueError, match='revaluation'):
        SuspensionMarket(values['market_schedule'], values['codes'], values['calendar'],
                         [{'symbol': values['codes'][0], 'ex_date': values['calendar'][3]}])
    for item in values['obligations']:
        if item['date'] == values['calendar'][3] and item['kind']=='corporate_actions':
            item['status'] = 'unknown'
    _, _, result = run(tmp_path/'account', engine, values)
    assert result['status'] == 'failed'
    assert result['valuation_complete_through'] == values['calendar'][2]
    assert any(x['quantity'] for x in result['partial']['snapshot']['lots'].values())


def test_source_paths_require_admission_without_reading_bytes(tmp_path, monkeypatch):
    from quanta_agents.meta_v3.source_admission import source_paths
    values = example(tmp_path)
    case = {'execution_backend':'v3_structural_001', 'raw_source_bindings':values}
    paths = source_paths(case)
    episode = values['market_schedule']['episodes'][0]
    assert paths[episode['document_path']] == paths[episode['review_path']] == 'historical_notice'
    monkeypatch.setattr(SuspensionMarket, 'verify_sources', lambda *a: pytest.fail('metadata read bytes'))
    assert source_paths(case) == paths


@pytest.mark.parametrize('commit_ack_lost',[False, True])
def test_failure_while_halted_preserves_committed_account(tmp_path, monkeypatch, commit_ack_lost):
    values = example(tmp_path); plan = engine.freeze_saved_research_plan(**values)
    job = engine.SavedRawResearch.create(tmp_path/'account', plan)
    append = job._append
    def interrupt(kind, payload):
        if kind=='checkpoint' and payload['phase']=='day_completed' and payload['date']==values['calendar'][3]:
            if commit_ack_lost: append(kind,payload)
            raise OSError('injected halt-day checkpoint loss')
        return append(kind,payload)
    monkeypatch.setattr(job,'_append',interrupt)
    saved = job.execute_saved(expected_plan_sha256=plan['plan_sha256'])
    assert saved['status']=='failed' and saved['result'] is None
    assert saved['valuation_complete_through']==values['calendar'][3 if commit_ack_lost else 2]
    assert any(x['quantity'] for x in saved['partial']['snapshot']['lots'].values())
    assert saved['partial']['snapshot']['external_cash_flow']=='1000000.00'
    monkeypatch.setattr(engine,'simulate_streamed_portfolio',lambda **k:pytest.fail('repeated account'))
    assert job.reconcile_saved_only(expected_plan_sha256=plan['plan_sha256'])==saved


def public_case(values):
    cells, eligibility = [], []
    for day in values['calendar']:
        for code in values['codes']:
            metadata = {'session':day,'symbol':code,'available_at':day+'T15:05:00+08:00',
                        'effective_at':day+'T15:05:00+08:00','source_evidence_id':'e'*64}
            cells.append({**metadata,'field':'close','value':10.})
            eligibility.append({**metadata,'eligible':True})
    obligations = deepcopy(values['obligations'])
    for row in obligations:
        row['status'] = 'documented_scope' if row['kind']=='corporate_actions' else 'declared_simulation'
    return {'research_class':'real_saved_development','execution_backend':'v3_structural_001',
        'description':'Generated engineering stand-in for daily real entry; no market claim',
        'initial_cash':'1000000.00','decision_fixture':{'kind':'exposed_real_decision_table',
            'codes':values['codes'],'calendar':values['calendar'],'fields':[{'name':'close','unit':'CNY'}],
            'field_rows':cells,'eligibility_rows':eligibility},
        'raw_source_bindings':{'source_artifacts':values['source_artifacts'],'obligations':obligations,
                               'market_schedule':values['market_schedule']}}


def test_ordinary_and_actual_batch_worker_share_structural_accounting(tmp_path):
    from quanta_agents.meta_v3.research_tools import ResearchTools
    from test_meta_v3_batch_research import execute, read_results
    values = example(tmp_path); case = public_case(values)
    program = {'version':'factor_strategy_program_v1','factors':[],
               'target_weight_expression':'0.2','hypothesis':'Generated accounting path',
               'applicability':['Engineering only'],'invalidation_conditions':['Different account']}
    ordinary = ResearchTools(tmp_path/'ordinary','test',case,[])
    one = ordinary.execute('candidate','develop_strategy',{'program':program})
    assert one['public']['raw_status']=='completed_mechanical'
    one_artifact = json.loads((ordinary.folder/'candidate/artifact.json').read_text(encoding='utf-8'))
    case = deepcopy(case)
    case['research_policy'] = {'version':'structural_research_v1','action_limits':{
        'register_batch':1,'execute_batch':1,'inspect_batch':3}}
    case['batch_policy'] = {'version':'bounded_batch_v1','max_candidates_total':1,'max_scan_cells_total':1000,
        'max_wall_seconds':60,'output_stop_threshold_bytes':16*1024**2,
        'field_semantics':{'close':{'unit':'CNY','raw_precision':'generated fixture only','digit_derivation':None}}}
    batch = ResearchTools(tmp_path/'batch','test',case,[])
    declaration = {'families':[{'id':'engineering','priority':1,'origin':'fixed',
        'mechanism_status':'unknown_anomaly','mechanism':'Engineering no economic mechanism claim',
        'role':'original','program_template':program,'parameters':{},'digit_fields':[]}],
        'comparisons':[],'selection_rule':'Accounting parity only','stop_rule':'stop_on_first_failure'}
    execute(batch,'registration','register_batch',declaration)
    result = execute(batch,'run','execute_batch',{'registration_evidence_id':'registration'})
    assert result['public']['status_counts']=={'completed':1}, read_results(batch)
    worker = json.loads((batch.batch_folder/'registration/candidates/c001/worker_result.json').read_text(encoding='utf-8'))
    a, b = one_artifact['raw']['result'], worker['artifact']['raw']['result']
    for x, y in zip(a['daily'], b['daily']):
        for field in ('holdings','cash_available','simulated_net_asset_value','estimated_locked_share_value'):
            assert x[field]==y[field]
    assert any(x['halted_position_estimates'] for x in b['daily'])
    assert b['final_snapshot']['external_cash_flow']=='1000000.00'
    assert result['public']['new_model_calls_inside_batch']==0


def test_runtime_rejects_changed_notice_before_any_gateway_call(tmp_path):
    from quanta_agents.meta_v3.runtime import verify_case_sources
    from quanta_agents.meta_v3.ledger import digest
    from pathlib import Path
    values = example(tmp_path); case = public_case(values)
    episode = values['market_schedule']['episodes'][0]
    Path(episode['document_path']).write_bytes(b'%PDF-changed')
    with pytest.raises(ValueError,match='hash mismatch'):
        verify_case_sources({'case':case,'case_hash':digest(case)})


@pytest.mark.parametrize('invalid',['overlap','policy','missing_resumption','subcent_anchor'])
def test_schedule_cannot_relabel_unverified_prices_or_release_halt_capital(tmp_path,invalid):
    values=example(tmp_path)
    if invalid=='overlap': values['market_schedule']['episodes']*=2
    if invalid=='policy': values['market_schedule']['policy']['halt_orders']='allow_sales'
    if invalid=='missing_resumption': values['market_schedule']['episodes'][0]['first_resumed']='2020-01-01'
    if invalid=='subcent_anchor':
        def alter(rows):
            rows[2]['raw_price_text']['raw_close']='10.001';rows[2]['raw_close']=10.001
        save_rows(values,values['codes'][0],alter)
        _,_,result=run(tmp_path/'account',engine,values)
        assert result['status']=='failed' and 'cent tick' in result['error']['message']
    else:
        with pytest.raises(ValueError): engine.freeze_saved_research_plan(**values)
