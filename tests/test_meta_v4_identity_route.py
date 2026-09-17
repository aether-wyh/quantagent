"""Identity-route prerequisites; generated verifier metadata is not authentic proof."""
from copy import deepcopy

import pytest

from quanta_agents.meta_v3.identity_route import verify
from quanta_agents.meta_v3.ledger import AdmissionBlocked
from quanta_agents.meta_v3.runtime import action_schema
from test_meta_v3_research_entry import new
from test_meta_v4_controller import stage


@pytest.mark.parametrize('confirmed', [False, True])
def test_existing_capture_is_required_and_provider_binding_remains_separate(tmp_path, monkeypatch, confirmed):
    runtime, _ = new(tmp_path)
    intent = runtime.ledger.reserve('test', ('submit_research_report',),
        lambda menu, state, decision: ('Explicit identity-engineering fixture', action_schema(menu)))
    receipt = {'response': {}, 'usage': {'input_tokens': 1, 'output_tokens': 1},
        'request_identity': {'intent_id': intent['intent_id']}, 'artifact_sha256': {},
        'model_verified': confirmed, 'engineering_fixture': True,
        'identity_verification': {'provider_request_binding_verified': False}}
    runtime.ledger.receive_saved(intent['intent_id'], lambda *args, **kwargs: receipt)
    plan = deepcopy(runtime.plan)
    plan['provenance']['runtime_identity_route'] = {'root': str(runtime.root), 'call_id': intent['intent_id']}
    monkeypatch.setattr(runtime.gateway_module, 'verify_saved_completion', lambda *args, **kwargs: receipt)
    if confirmed:
        result = verify(plan, runtime.gateway_module)
        assert result['status'] == 'available' and result['provider_binding_verified'] is False
    else:
        with pytest.raises(AdmissionBlocked, match='request configuration is insufficient'):
            verify(plan, runtime.gateway_module)


def test_status_reports_scoped_sources_and_identity_without_call_or_saved_status(tmp_path, monkeypatch):
    runtime = stage(tmp_path)
    monkeypatch.setattr(runtime.gateway_module.CodexGateway, 'run',
        lambda *a, **kw: pytest.fail('read-only status dispatched a model'))
    state = runtime.inspect_work()
    assert state['work_schedule']['tasks']['unavailable']['status'] == 'blocked_task_source'
    assert state['work_schedule']['tasks']['independent']['status'] == 'blocked_runtime_identity'
    assert not (runtime.root / 'status.json').exists()
    assert not state['tasks']['independent']['calls']
