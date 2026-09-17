"""Generated accounting and byte-format checks; no supplier/model calls."""
from copy import deepcopy
import hashlib
import json
import sqlite3
import zlib

import pytest

from quanta_agents.meta_v3 import archive_codec as codec, saved_execution as saved
from quanta_agents.meta_v3.ledger import digest
from test_meta_v3_streamed_execution import inputs, run

POLICY = {'version': 'zlib_records_v1'}


@pytest.mark.parametrize('raw', [b'', b'one', '原始证明\n现金1000000.00'.encode(), b'x' * 200000], ids=['empty','small','unicode','large'])
def test_byte_exact_codec_and_two_hashes(raw):
    record = codec.encode_record(raw, POLICY, decoded_limit=len(raw))
    assert codec.decode_record(record, POLICY, decoded_limit=len(raw)) == raw
    assert record['decoded_sha256'] == hashlib.sha256(raw).hexdigest()
    assert record['stored_sha256'] == hashlib.sha256(record['payload']).hexdigest()


@pytest.mark.parametrize('bad', [{}, {'version':'other'}, {'version':codec.VERSION,'level':9}, [], False])
def test_unknown_policy_cannot_select_or_extend_encoding(bad):
    with pytest.raises(ValueError, match='policy'):
        codec.validate_policy(bad)
    codec.validate_policy(None)
    with pytest.raises(ValueError, match='explicit'):
        codec.encode_record(b'a', None, decoded_limit=1)


@pytest.mark.parametrize('change', ['stored_hash','decoded_hash','stored_length','decoded_length','truncated','tail','second_stream','corrupt','oversized_blob'])
def test_corruption_lengths_trailing_and_multistream_rejected(change):
    record = codec.encode_record(b'old evidence' * 20, POLICY, decoded_limit=1000)
    if change == 'stored_hash': record['stored_sha256'] = '0' * 64
    elif change == 'decoded_hash': record['decoded_sha256'] = '0' * 64
    elif change == 'stored_length': record['stored_bytes'] += 1
    elif change == 'decoded_length': record['decoded_bytes'] -= 1
    else:
        record['payload'] = {'truncated':record['payload'][:-1], 'tail':record['payload']+b'junk',
                             'second_stream':record['payload']+zlib.compress(b'next'), 'corrupt':b'bad zlib',
                             'oversized_blob':b'X' * 4000}[change]
        record['stored_bytes'] = len(record['payload'])
        record['stored_sha256'] = hashlib.sha256(record['payload']).hexdigest()
    with pytest.raises(ValueError):
        codec.decode_record(record, POLICY, decoded_limit=1000)


def test_decompression_is_bounded_before_output_allocation(monkeypatch):
    packed = zlib.compress(b'x' * 1000000)
    record = {'codec':codec.VERSION, 'payload':packed, 'stored_bytes':len(packed),
              'stored_sha256':hashlib.sha256(packed).hexdigest(), 'decoded_bytes':100,
              'decoded_sha256':hashlib.sha256(b'x' * 100).hexdigest()}
    original = zlib.decompressobj
    calls = []
    class Bounded:
        def __init__(self): self.raw = original()
        def decompress(self, payload, maximum):
            calls.append(maximum)
            assert maximum <= 101
            return self.raw.decompress(payload, maximum)
        def __getattr__(self, name): return getattr(self.raw, name)
    monkeypatch.setattr(codec.zlib, 'decompressobj', Bounded)
    with pytest.raises(ValueError, match='length'):
        codec.decode_record(record, POLICY, decoded_limit=100)
    assert calls == [101]
    record['decoded_bytes'] = 101
    with pytest.raises(ValueError, match='exceeds limit'):
        codec.decode_record(record, POLICY, decoded_limit=100)
    assert calls == [101]
    with pytest.raises(ValueError): codec.encode_record(b'12', POLICY, decoded_limit=1)
    with pytest.raises(ValueError): codec.stored_limit(codec.MAX_DECODED_RECORD + 1)


def compressed_job(tmp_path, *, count=12):
    values = inputs(tmp_path/'inputs', count)
    plan = saved.freeze_saved_research_plan(**values, archive_storage_policy=POLICY)
    return saved.SavedRawResearch.create(tmp_path/'archive', plan), plan


def test_complete_account_and_legacy_read_format_unchanged(tmp_path, monkeypatch):
    values = inputs(tmp_path/'inputs', 12)
    legacy_job, legacy_plan, legacy = run(tmp_path/'plain', saved, values)
    job, plan, compressed = run(tmp_path/'packed', saved, {**values, 'archive_storage_policy':POLICY})
    assert compressed['status'] == legacy['status'] == 'completed_mechanical'
    assert compressed['result'] == legacy['result']
    assert plan['initial_cash'] == legacy_plan['initial_cash'] == '1000000.00'
    assert plan['resource_budget'] == legacy_plan['resource_budget']
    assert 'archive_codec.py' in plan['engine_sources'] and 'archive_codec.py' not in legacy_plan['engine_sources']
    assert 'archive_storage_policy' not in legacy_plan
    with sqlite3.connect(legacy_job.db) as db:
        assert [r[1] for r in db.execute('PRAGMA table_info(records)')] == ['seq','previous_sha256','body','sha256']
        assert all(r[0] == 'text' for r in db.execute('SELECT typeof(body) FROM records'))
        assert set(dict(db.execute('SELECT key,value FROM metadata'))) == {'plan','plan_sha256','usage'}
    with sqlite3.connect(job.db) as db:
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='records'").fetchone()
        row = db.execute('SELECT seq,previous_sha256,payload,stored_bytes,stored_sha256,decoded_bytes,decoded_sha256,sha256 FROM records_zlib ORDER BY seq LIMIT 1').fetchone()
        decoded = codec.decode_record(dict(zip(('codec','payload','stored_bytes','stored_sha256','decoded_bytes','decoded_sha256'), (codec.VERSION,*row[2:7]))), POLICY, decoded_limit=saved.MAX_RECORD)
        assert row[-1] == saved.content_hash({'seq':row[0], 'previous_sha256':row[1], 'body':json.loads(decoded)})
        stored_count = db.execute('SELECT sum(length(payload)) FROM records_zlib').fetchone()[0]
    usage = compressed['resource_usage']
    assert usage['persisted_payload_bytes'] == usage['stored_payload_bytes'] == stored_count
    assert usage['stored_payload_bytes'] < usage['decoded_payload_bytes']
    assert set(legacy['resource_usage']) == {'persisted_payload_bytes','pending_write_reserved_bytes','terminal_reserved_bytes','event_intents'}
    before = {str(j.db):j.db.read_bytes() for j in (job, legacy_job)}
    monkeypatch.setattr(saved, 'simulate_streamed_portfolio', lambda **k: pytest.fail('reexecuted'))
    monkeypatch.setattr(saved, '_load_saved', lambda *a: pytest.fail('reopened market source'))
    assert job.reconcile_saved_only(expected_plan_sha256=plan['plan_sha256']) == compressed
    assert legacy_job.reconcile_saved_only(expected_plan_sha256=legacy_plan['plan_sha256']) == legacy
    assert all(j.db.read_bytes() == before[str(j.db)] for j in (job, legacy_job))


@pytest.mark.parametrize('change', ['codec_metadata','remove_metadata','remove_plan_flag','counter','payload','chain'])
def test_store_tampering_and_policy_downgrade_rejected(tmp_path, change):
    job, plan = compressed_job(tmp_path)
    job._append('execution_intent', {'plan_sha256':plan['plan_sha256']})
    expected = plan['plan_sha256']
    with sqlite3.connect(job.db) as db:
        if change == 'codec_metadata': db.execute("UPDATE metadata SET value=? WHERE key='archive_storage_policy'", (json.dumps({'version':'unknown'}),))
        elif change == 'remove_metadata': db.execute("DELETE FROM metadata WHERE key='archive_storage_policy'")
        elif change == 'remove_plan_flag':
            frozen = json.loads(db.execute("SELECT value FROM metadata WHERE key='plan'").fetchone()[0])
            frozen.pop('archive_storage_policy'); frozen['engine_sources'].pop('archive_codec.py')
            expected = saved.content_hash(frozen)
            db.execute("UPDATE metadata SET value=? WHERE key='plan'", (saved._json(frozen),))
            db.execute("UPDATE metadata SET value=? WHERE key='plan_sha256'", (expected,))
            (job.root/'plan.json').write_text(saved._json({**frozen,'plan_sha256':expected}), encoding='utf-8')
        elif change == 'counter': db.execute("UPDATE metadata SET value=? WHERE key='usage'", (json.dumps({'bytes':0,'records':1,'event_intents':0,'stored_bytes':0}),))
        elif change == 'payload': db.execute('UPDATE records_zlib SET payload=?', (b'changed',))
        else: db.execute('UPDATE records_zlib SET sha256=?', ('0'*64,))
    with pytest.raises(ValueError): job._read(expected)


def test_decoded_and_stored_total_limits_and_atomic_append(tmp_path, monkeypatch):
    job, plan = compressed_job(tmp_path)
    original = job.db.read_bytes()
    # Trigger abort after the record insert, before usage commits. The existing
    # SQLite transaction must roll the record and counters back together.
    with sqlite3.connect(job.db) as db:
        db.execute("CREATE TRIGGER fail_usage BEFORE UPDATE ON metadata WHEN NEW.key='usage' BEGIN SELECT RAISE(ABORT,'injected usage failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match='injected'):
        job._append('execution_intent', {'plan_sha256':plan['plan_sha256']})
    with sqlite3.connect(job.db) as db:
        assert db.execute('SELECT count(*) FROM records_zlib').fetchone()[0] == 0
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='usage'").fetchone()[0]) == {'bytes':0,'records':0,'event_intents':0,'stored_bytes':0}
        db.execute('DROP TRIGGER fail_usage')
    job._append('execution_intent', {'plan_sha256':plan['plan_sha256']})
    monkeypatch.setattr(saved, 'MAX_ARCHIVE', 1)
    with pytest.raises(ValueError, match='bound exceeded'): job._read(plan['plan_sha256'])
    with pytest.raises(ValueError, match='archive bound'): job._append('terminal', {'status':'failed'})


def test_encoded_reserve_blocks_before_inserting_next_intent(tmp_path):
    job, _ = compressed_job(tmp_path)
    with sqlite3.connect(job.db) as db:
        usage = {'bytes':0,'records':0,'event_intents':0,'stored_bytes':saved.MAX_ARCHIVE-1000}
        db.execute("UPDATE metadata SET value=? WHERE key='usage'", (json.dumps(usage),))
    with pytest.raises(ValueError, match='reserved persistence'):
        job._append('execution_intent', {'proof':'kept'})
    with sqlite3.connect(job.db) as db:
        assert db.execute('SELECT count(*) FROM records_zlib').fetchone()[0] == 0
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='usage'").fetchone()[0]) == usage


def test_sql_blob_bound_checked_before_decoder_fetch(tmp_path, monkeypatch):
    job, plan = compressed_job(tmp_path)
    job._append('execution_intent', {'plan_sha256':plan['plan_sha256']})
    with sqlite3.connect(job.db) as db:
        db.execute('UPDATE records_zlib SET payload=zeroblob(4000),stored_bytes=4000,decoded_bytes=1')
    monkeypatch.setattr(codec, 'decode_record', lambda *a, **k: pytest.fail('oversized payload reached decoder'))
    with pytest.raises(ValueError, match='encoded evidence bound'):
        job._read(plan['plan_sha256'])


def test_compressed_dividend_and_tax_proofs_equal_plain_complete_account(tmp_path):
    values = inputs(tmp_path/'inputs', 12)
    days = values['calendar']
    from quanta_agents.meta_v3.kernel import module
    adapter = module('corporate_action_adapter')
    values['corporate_actions'] = [adapter.CashDividendAnnouncement(
        action_id='generated-cash',symbol=values['codes'][0],announcement_date=days[2],
        record_date=days[5],ex_date=days[6],cash_payment_date=days[6],gross_cash_per_share='0.17',
        short_holding_tax_rate='0.20',tax_rule=adapter.SUPPORTED_TAX_RULE,account_type=adapter.ACCOUNT_TYPE,
        stock_distribution_per_share='0',stock_distribution_kind='none',rights_issue=False,
        implementation_status='implementation_notice',source_url='fixture://generated-event',
        source_sha256='a'*64,source_fetched_at='2026-09-07T00:00:00+00:00',facts_verified=True)]
    _, _, plain = run(tmp_path/'plain', saved, values)
    _, _, packed = run(tmp_path/'packed', saved, {**values,'archive_storage_policy':POLICY})
    assert plain['status'] == packed['status'] == 'completed_mechanical'
    assert plain['result'] == packed['result']
    kinds = {row['event']['kind'] for row in packed['result']['journal']}
    assert {'cash_dividend_paid','activate_entitlement','tax_assessed','tax_paid'} <= kinds


@pytest.mark.parametrize('ack_lost', [False, True])
def test_compressed_interrupted_event_saved_only_recovery(tmp_path, monkeypatch, ack_lost):
    job, plan = compressed_job(tmp_path)
    append = job._append
    def fail(kind, payload):
        if kind == 'checkpoint' and payload['phase'] == 'event_applied' and payload['event']['kind'] == 'buy_fill':
            if ack_lost: append(kind, payload)
            raise OSError('injected persistence interruption')
        return append(kind, payload)
    monkeypatch.setattr(job, '_append', fail)
    result = job.execute_saved(expected_plan_sha256=plan['plan_sha256'])
    assert result['status'] == 'failed' and result['result'] is None
    assert bool(result['pending_event_intent']) is not ack_lost
    assert result['partial']['snapshot']['external_cash_flow'] == '1000000.00'
    monkeypatch.setattr(saved, 'simulate_streamed_portfolio', lambda **k: pytest.fail('retry'))
    monkeypatch.setattr(saved, '_load_saved', lambda *k: pytest.fail('source reopening'))
    assert job.reconcile_saved_only(expected_plan_sha256=plan['plan_sha256']) == result


def real_case(tmp_path):
    values = inputs(tmp_path/'inputs', 12)
    for row in values['obligations']:
        row['status'] = 'documented_scope' if row['kind'] == 'corporate_actions' else 'declared_simulation'
    cells, eligibility = [], []
    for day in values['calendar']:
        for code in values['codes']:
            meta = {'session':day,'symbol':code,'available_at':day+'T15:05:00+08:00',
                    'effective_at':day+'T15:05:00+08:00','source_evidence_id':'e'*64}
            cells.append({**meta,'field':'close','value':10.})
            eligibility.append({**meta,'eligible':True})
    return {'research_class':'real_saved_development','description':'Generated engineering case',
            'initial_cash':'1000000.00','execution_backend':'v3_streamed_001','archive_storage_policy':POLICY,
            'decision_fixture':{'kind':'exposed_real_decision_table','codes':values['codes'],'calendar':values['calendar'],
                                'fields':[{'name':'close','unit':'CNY'}],'field_rows':cells,'eligibility_rows':eligibility},
            'raw_source_bindings':{k:values[k] for k in ('source_artifacts','obligations')}}


def test_actual_frozen_case_policy_reaches_real_tool_execution(tmp_path):
    from quanta_agents.meta_v3.research_tools import ResearchTools
    from quanta_agents.meta_v3.runtime import verify_case_sources
    case = real_case(tmp_path)
    verify_case_sources({'case':case,'case_hash':digest(case)})
    tools = ResearchTools(tmp_path/'stage', 'test', case, [])
    response = tools.execute('candidate', 'develop_strategy', {'program':{
        'version':'factor_strategy_program_v1','factors':[],'target_weight_expression':'0.4',
        'hypothesis':'Generated accounting check','applicability':['Engineering only'],
        'invalidation_conditions':['Accounting mismatch']}})
    assert response['public']['raw_status'] == 'completed_mechanical'
    child = tools.folder/'candidate/workbench/raw_children/program'
    frozen = json.loads((child/'plan.json').read_text(encoding='utf-8'))
    assert frozen['archive_storage_policy'] == POLICY and frozen['identity']['data_hash'] == digest(case)
    with sqlite3.connect(child/'research.sqlite3') as db:
        assert db.execute('SELECT count(*) FROM records_zlib').fetchone()[0] > 0
        assert not db.execute("SELECT 1 FROM sqlite_master WHERE name='records'").fetchone()
    modified = deepcopy(case); modified.pop('archive_storage_policy')
    with pytest.raises(ValueError, match='case identity'):
        verify_case_sources({'case':modified,'case_hash':digest(case)})
    for invalid in (None, {'version':'wrong'}):
        modified = deepcopy(case); modified['archive_storage_policy'] = invalid
        with pytest.raises(ValueError): verify_case_sources({'case':modified,'case_hash':digest(modified)})
    for backend in (None, 'v3_structural_001', 'v3_l2_cash_001'):
        modified = deepcopy(case); modified['execution_backend'] = backend
        with pytest.raises(ValueError, match='real streamed'): verify_case_sources({'case':modified,'case_hash':digest(modified)})
