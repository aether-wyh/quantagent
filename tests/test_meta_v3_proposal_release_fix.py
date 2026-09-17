"""Gate-only regression fixtures. No model, worker, or funded account execution."""
import json

import pytest

from quanta_agents.meta_v3 import generator_proposal as gp, generator_controls as gc, research_batch, runtime
from quanta_agents.meta_v3.kernel import module
from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest
from test_meta_v3_generator_proposal import setup, generated_call, generated_final, mock_verifier
from test_meta_v3_generator_controls import freeze


def write(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


class DownstreamReached(Exception):
    pass


@pytest.fixture(autouse=True)
def no_execution(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('No subprocess, model, batch, or account may run in this gate-only scope')
    monkeypatch.setattr(research_batch.subprocess, 'Popen', forbidden)
    monkeypatch.setattr(research_batch, 'run', forbidden)
    monkeypatch.setattr(module('meta.codex_gateway').CodexGateway, 'run', forbidden)


def sealed(tmp_path, monkeypatch, confirmed=False):
    root, rt = setup(tmp_path); receipts = {}
    one = generated_call(rt, 'inspect_inputs', {'table':'fields','offset':0,'limit':32}, receipts, confirmed=confirmed)
    generated_final(rt, receipts, one['intent_id'], confirmed=confirmed)
    mock_verifier(monkeypatch, receipts)
    gp.seal(root)
    return root


def test_release_bit_cannot_override_unconfirmed_saved_calls(tmp_path, monkeypatch):
    root = sealed(tmp_path, monkeypatch)
    release = research_batch.read(root/'control_release.json'); release['allowed'] = True
    write(root/'control_release.json', release)
    with pytest.raises(AdmissionBlocked): gp.check_control_release(root/'controls')
    assert not (root/'controls/arms').exists()


@pytest.mark.parametrize('mutation', ['confirmed_flag','all_identity_flags','empty_call_list','slot_status'])
def test_rehashed_receipt_cannot_override_saved_evidence(tmp_path, monkeypatch, mutation):
    root = sealed(tmp_path, monkeypatch)
    receipt = research_batch.read(root/'proposal_receipt.json')
    receipt['provider_model_effort_confirmed'] = True
    if mutation == 'all_identity_flags':
        for row in receipt['verified_calls']: row['model_effort_confirmed_by_runtime_events'] = True
    elif mutation == 'empty_call_list': receipt['verified_calls'] = []
    elif mutation == 'slot_status': receipt['slots'][0]['proposal_status'] = 'inside_domain'
    write(root/'proposal_receipt.json', receipt)
    release = research_batch.read(root/'control_release.json')
    release.update(allowed=True, proposal_receipt_hash=digest(receipt))
    write(root/'control_release.json', release)
    with pytest.raises(AdmissionBlocked): gp.check_control_release(root/'controls')
    assert not (root/'controls/arms').exists()


@pytest.mark.parametrize('arm', ['fixed','random','model'])
def test_missing_proposal_binding_never_reaches_execution_preflight(tmp_path, monkeypatch, arm):
    root = sealed(tmp_path, monkeypatch)
    (root/'controls'/gp.BINDING).unlink()  # Only this generated temporary fixture.
    def downstream(*args, **kwargs): raise DownstreamReached('Reached source preflight after missing binding')
    monkeypatch.setattr(runtime, 'verify_case_sources', downstream)
    with pytest.raises(AdmissionBlocked): gc.run_control(root/'controls', arm)
    assert not (root/'controls/arms').exists()


def test_proposal_requirement_is_frozen_before_model_stage(tmp_path):
    root, _ = setup(tmp_path)
    plan = research_batch.read(root/'controls/plan.json')
    assert plan.get('requires_model_proposal') is True
    plan['requires_model_proposal'] = False
    write(root/'controls/plan.json', plan)
    with pytest.raises(AdmissionBlocked): gc.verify(root/'controls')


def test_missing_mandatory_admission_identity_is_not_legacy_fallback(tmp_path):
    root, *_ = freeze(tmp_path)
    plan = research_batch.read(root/'plan.json'); plan.pop('requires_model_proposal', None)
    write(root/'plan.json', plan)
    controls = research_batch.read(root/'controls.json'); controls['plan_hash'] = digest(plan)
    write(root/'controls.json', controls)
    with pytest.raises(AdmissionBlocked): gc.verify(root)


def test_unexpected_binding_cannot_upgrade_standalone_controls(tmp_path):
    root, *_ = freeze(tmp_path)
    write(root/gp.BINDING, {'proposal_root':str(root.parent)})
    with pytest.raises(AdmissionBlocked): gc.verify(root)


def test_confirmed_generated_evidence_replays_gate_without_any_execution(tmp_path, monkeypatch):
    root = sealed(tmp_path, monkeypatch, confirmed=True)
    before = {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert gp.check_control_release(root/'controls') is None
    assert before == {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert not (root/'controls/arms').exists()


@pytest.mark.parametrize('arm', ['fixed','random'])
def test_standalone_generated_controls_reach_only_preflight(tmp_path, monkeypatch, arm):
    root, *_ = freeze(tmp_path)
    assert research_batch.read(root/'plan.json').get('requires_model_proposal') is False
    def downstream(*args, **kwargs): raise DownstreamReached('Expected gate-only boundary')
    monkeypatch.setattr(runtime, 'verify_case_sources', downstream)
    with pytest.raises(DownstreamReached): gc.run_control(root, arm)
    assert not (root/'arms').exists()
