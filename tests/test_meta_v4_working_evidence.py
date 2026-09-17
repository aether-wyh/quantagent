import copy
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v3.context import bounded, history_context, working_evidence_index
from quanta_agents.meta_v3.ledger import digest, serial


def row(call_id='a', status='applied'):
    return {'id': call_id, 'status': status, 'response': {
        'action': 'register_experiment', 'arguments_json': json.dumps({
            'mechanism_hypotheses': ['Cost reduction explains the difference.',
                                     'Entry timing explains the difference.'],
            'failure_rule': 'Reject if the matched control does as well.',
            'baseline_evidence_id': 'baseline'}),
        'public_summary': 'Registered; execution has not occurred.',
        'self_review': {'assessment': 'Neither explanation is established.',
            'uncertainty': 'Matched control remains unread.',
            'next_step': 'Read saved accounts.', 'falsifier': 'Control is not worse.'}},
        'result': {'execution_valid': False, 'formal_target_success': False}}


def test_opt_in_preserves_old_projection_and_unreconciled_public_statements():
    history = [row(), row('b', 'failed')]
    history[1]['response']['self_review']['assessment'] = 'The prior prediction failed.'
    before = copy.deepcopy(history)
    legacy = history_context(history)
    index = working_evidence_index(history, projection='full')
    assert history == before
    assert history_context(history) == legacy
    assert [(r['id'], r['status']) for r in index['rows']] == [('a', 'applied'), ('b', 'failed')]
    for source, indexed in zip(history, index['rows']):
        statements = {x['source_path']: x for x in indexed['statements']}
        for field, value in source['response']['self_review'].items():
            item = statements['/response/self_review/' + field]
            assert item == {'source_path': item['source_path'], 'sha256': digest(value),
                            'complete': True, 'value': value}
    assert index['history_sha256'] == digest(history)


def test_declared_hypotheses_falsifiers_and_source_references_are_exact():
    source = row()
    indexed = working_evidence_index([source], projection='full')['rows'][0]
    statements = {x['source_path']: x['value'] for x in indexed['statements']}
    args = json.loads(source['response']['arguments_json'])
    assert statements['/response/arguments_json#/mechanism_hypotheses'] == args['mechanism_hypotheses']
    assert statements['/response/arguments_json#/failure_rule'] == args['failure_rule']
    assert indexed['evidence_references'] == [{
        'source_path': '/response/arguments_json#/baseline_evidence_id', 'value': 'baseline'}]


def test_batch_family_mechanism_status_is_copied_not_promoted_to_fact():
    source = row()
    source['response']['action'] = 'register_batch'
    source['response']['arguments_json'] = json.dumps({'families': [{
        'id': 'position', 'mechanism_status': 'hypothesis',
        'mechanism': 'Short-term reversal is unproven.'}],
        'selection_rule': 'Retain only if matched controls are exceeded.',
        'comparisons': [{'kind': 'alternative_explanation', 'prediction': 'Exposure may explain returns.'}]})
    statements = {x['source_path']: x['value'] for x in
                  working_evidence_index([source], projection='full')['rows'][0]['statements']}
    assert statements['/response/arguments_json#/families/0/mechanism_status'] == 'hypothesis'
    assert statements['/response/arguments_json#/families/0/mechanism'] == 'Short-term reversal is unproven.'
    assert statements['/response/arguments_json#/comparisons'][0]['prediction'] == 'Exposure may explain returns.'


def test_recovered_failure_is_not_relabelled_or_erased():
    source = row(status='failed')
    source['original_application_result'] = {'error': 'Application failed after producer finished.'}
    source['saved_result_recovery'] = {'original_call_id': 'a', 'verified': True}
    indexed = working_evidence_index([source], projection='full')['rows'][0]
    assert indexed['status'] == 'failed'
    assert indexed['original_application_result_sha256'] == digest(source['original_application_result'])
    assert any(x['source_path'] == '/original_application_result' and
               x['value'] == source['original_application_result'] for x in indexed['statements'])


def test_long_public_text_is_explicit_excerpt_not_a_fabricated_summary():
    source = row()
    source['response']['self_review']['uncertainty'] = '中段反证未核实。' * 2000
    indexed = working_evidence_index([source], statement_bytes=1800, projection='full')['rows'][0]
    item = next(x for x in indexed['statements'] if x['source_path'].endswith('/uncertainty'))
    assert item['complete'] is False
    assert item['value']['original_sha256'] == item['sha256']
    assert len(serial(item['value']).encode()) <= 1800


def test_null_response_and_invalid_arguments_keep_failure_identity():
    invalid = row('bad', 'failed')
    invalid['response']['arguments_json'] = '{invalid'
    missing = {'id': 'missing', 'status': 'failed', 'response': None, 'result': {'error': 'No response'}}
    indexed = working_evidence_index([invalid, missing], projection='full')['rows']
    assert indexed[0]['arguments_index_status'].startswith('unparsed')
    assert indexed[1]['status'] == 'failed'
    assert indexed[1]['statements'][0]['value'] == 'No response'


def test_saved_prompt_omission_is_indexed_without_inventing_permissions():
    root = Path(__file__).resolve().parents[1]
    scope = root / 'experiment_traces/meta_framework_v3/batch_recovery_001'
    call_id = 'batch_tool_calibration_001_003_17eab9c0b631'
    result_path = scope / 'tools/batch_tool_calibration_001' / call_id / 'result.json'
    prompt_path = scope / 'calls/batch_tool_calibration_001_004_027c66bbd8ed/prompt.txt'
    response_path = scope / 'calls' / call_id / 'response.json'
    if not all(p.exists() for p in (result_path, prompt_path, response_path)):
        pytest.skip('Archived saved calibration trace is not installed')
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    result = read(result_path)
    saved = next(r for r in read(prompt_path)['own_complete_action_history'] if r['id'] == call_id)
    assert saved['result'] == bounded(result)
    baseline = result['public']['accounts'][3]
    assert baseline['mean_marked_share_fraction_of_gross_assets'] == '0.6559747980959308040221368916'
    assert baseline['mean_marked_share_fraction_of_gross_assets'] not in serial(saved['result'])
    source = {**saved, 'response': read(response_path), 'result': result}
    queries = working_evidence_index([source], allowed_actions=[], projection='full')['rows'][0]['page_queries']
    assert len(queries) == len(result['public']['accounts']) == 4
    assert queries[3]['account_evidence_id'] == baseline['evidence_id']
    assert queries[3]['source_sha256'] == digest(baseline)
    assert queries[3]['arguments'] == {'evidence_id': call_id, 'table': 'attribution_accounts', 'offset': 3, 'limit': 1}
    assert queries[3]['currently_allowed'] is False
    assert working_evidence_index([source], allowed_actions=['read_evidence'], projection='full')['rows'][0]['page_queries'][3]['currently_allowed'] is True
    minimal = working_evidence_index([source], allowed_actions=['read_evidence'])['rows'][0]
    assert [q['arguments']['offset'] for q in minimal['page_queries']] == [2, 3]
    assert not minimal.get('statements')  # All self-review and declaration objects survived.
    assert minimal['page_queries'][-1]['arguments'] == queries[3]['arguments']
    # Exercise the existing pure page delivery path against the saved artifact;
    # do not open a runtime, lease, call ledger or closed research scope.
    from quanta_agents.meta_v3.evidence_views import page_for_context
    from quanta_agents.meta_v3.research_iteration import public_diagnosis
    from quanta_agents.meta_v3.research_tools import ResearchTools
    artifact = read(result_path.with_name('artifact.json'))
    assert digest(artifact) == result['artifact_hash']
    accounts = public_diagnosis(artifact)['accounts']
    for query in minimal['page_queries']:
        page = ResearchTools._page(accounts, query['arguments'])
        wrap = lambda p, view: {'evidence_id': 'offline_query', 'action': 'read_evidence',
            'artifact_hash': digest(p), 'public': view,
            'execution_valid': False, 'formal_target_success': False}
        actual, public = page_for_context(page, lambda p: p, wrap, 1)
        assert public['returned_rows'] == 1
        assert digest(actual['rows'][0]) == query['source_sha256']
        assert len(serial(wrap(actual, public)).encode()) <= 8000
    assert actual['rows'][0]['mean_marked_share_fraction_of_gross_assets'] == baseline['mean_marked_share_fraction_of_gross_assets']


def test_omitted_default_does_not_repeat_any_complete_small_source():
    source = row(status='failed')
    source['saved_result_recovery'] = {'verified': True}
    source['original_application_result'] = {'error': 'Preserved application failure'}
    before = copy.deepcopy(source)
    assert working_evidence_index([source])['rows'] == []
    assert source == before
    assert history_context([source])[0]['status'] == 'failed'


def test_omitted_only_uses_object_position_not_repeated_words():
    source = row()
    repeated = 'Same words in a visible summary and a missing assessment.'
    source['response']['public_summary'] = repeated
    source['response']['arguments_json'] = '{}'
    source['response']['self_review'] = {
        'a_padding': 'x' * 5500, 'assessment': repeated,
        'uncertainty': 'y' * 5500, 'next_step': 'Inspect missing evidence.'}
    excerpt = bounded(source['response'])
    assert repeated in excerpt['first_excerpt']
    indexed = working_evidence_index([source])['rows'][0]
    paths = {item['source_path'] for item in indexed['statements']}
    assert '/response/public_summary' not in paths
    assert '/response/self_review/assessment' in paths
    assert '/response/self_review/uncertainty' in paths


def test_omitted_only_maps_escaped_and_spaced_argument_fields_exactly():
    source = row()
    args = {'mechanism_hypotheses': ['A visible hypothesis.'],
            'padding': '\\"中\n' * 5000,
            'failure_rule': 'A missing rejection condition.',
            'padding_after': 'z' * 6000,
            'success_rule': 'Visible tail declaration.'}
    source['response']['arguments_json'] = json.dumps(args, ensure_ascii=False, indent=2)
    indexed = working_evidence_index([source])['rows'][0]
    paths = {item['source_path'] for item in indexed['statements']}
    assert '/response/arguments_json#/failure_rule' in paths
    assert '/response/arguments_json#/mechanism_hypotheses' not in paths
    assert '/response/arguments_json#/success_rule' not in paths
    assert not any('/self_review/' in path for path in paths)


def test_omitted_recovered_failure_remains_explicit_and_incomplete():
    source = row(status='failed')
    source['saved_result_recovery'] = {'verified': True}
    source['original_application_result'] = {'error': 'failed ' * 2500}
    indexed = working_evidence_index([source])['rows'][0]
    assert indexed['status'] == 'failed'
    assert indexed['truncated_sources'][0]['source_path'] == '/original_application_result'
    assert indexed['statements'][0]['complete'] is False
    assert indexed['original_application_result_sha256'] == digest(source['original_application_result'])


@pytest.mark.parametrize('value', [0, 1200, 1599, 8001, True])
def test_statement_budget_rejects_unsafe_tiny_or_unbounded_projection(value):
    with pytest.raises(ValueError):
        working_evidence_index([], statement_bytes=value)


@pytest.mark.parametrize('arguments', [
    '{"failure_rule":"first","padding":"' + 'x' * 9000 + '","failure_rule":"last"}',
    '{"comparisons":[NaN],"padding":"' + 'x' * 9000 + '"}',
])
def test_failed_ambiguous_arguments_cannot_gain_a_false_source_span(arguments):
    source = row(status='failed')
    source['response']['arguments_json'] = arguments
    indexed = working_evidence_index([source])['rows'][0]
    assert indexed['arguments_index_status'].startswith('unparsed')
    assert not any('/arguments_json#/' in item['source_path'] for item in indexed.get('statements', []))
    assert indexed['status'] == 'failed'
