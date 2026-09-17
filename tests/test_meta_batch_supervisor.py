import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('batch_supervisor', Path(__file__).resolve().parents[1] / 'scripts/supervise_meta_batch.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_file_error_reenters_same_dispatcher_without_replacing_work():
    calls, events = [], []
    def run_once():
        calls.append('same_frozen_batch')
        if len(calls) == 1:
            raise PermissionError('report temporarily open')
        return {'status': 'completed'}
    assert module.supervise(run_once, emit=events.append, sleep=lambda _: None) == {'status': 'completed'}
    assert calls == ['same_frozen_batch'] * 2
    assert events[0]['action'] == 'resume_existing_dispatcher_via_ledger'


@pytest.mark.parametrize('report', [
    {'status': 'attention', 'stop_reason': 'creation response unknown'},
    {'status': 'attention', 'stop_reason': 'unknown model usage'},
    {'status': 'cancelled'}, {'status': 'budget_exceeded'}, {'status': 'frozen_mismatch'},
])
def test_paid_unknown_and_explicit_stops_are_never_retried(report):
    calls = []
    def run_once():
        calls.append(1)
        return report
    assert module.supervise(run_once, emit=lambda _: None) is report
    assert calls == [1]


def test_persistent_file_denial_stops_after_bounded_attempts():
    events = []
    def denied():
        raise PermissionError('permanent denial')
    with pytest.raises(RuntimeError, match='without creating'):
        module.supervise(denied, emit=events.append, sleep=lambda _: None, monotonic=lambda: 0)
    assert len(events) == 8
    assert events[-1]['action'] == 'stop_supervisor'


def test_only_known_active_run_filesystem_attention_is_recoverable():
    transient = {'status': 'attention', 'stop_reason': 'read-only API reconciliation unavailable: PermissionError',
                 'entries': [{'run_id': 'existing', 'run_status': 'running'}]}
    responses = iter([transient, {'status': 'completed'}])
    assert module.supervise(lambda: next(responses), emit=lambda _: None, sleep=lambda _: None)['status'] == 'completed'
    transient['entries'] = [{'run_id': None, 'run_status': None}]
    assert module.supervise(lambda: transient, emit=lambda _: None) is transient
