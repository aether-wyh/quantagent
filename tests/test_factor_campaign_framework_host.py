"""Host transition tests use explicit synthetic model decisions, no paid calls."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from quanta_agents.factor_campaign import framework_host as host
from quanta_agents.research_kernel.store import write_json


class FakeCampaign:
    def __init__(self, root):
        self.root, self._context = root, None
        self.root.mkdir()
        self._status = {"version":"V10A","batch":2,"phase":"version_review_complete", "primary_evaluated":300,
                        "combinations_evaluated":200,"new_evaluated":254,"framework_versions_completed":[],
                        "historical_target_met":False,"stop_requested":False,"numeric_wall_seconds":12.,"failures":1}
        self.events=[]
        self.config={"budget":{"minimum_factors":300,"minimum_combinations":200,"minimum_new_v10a":254}}
    @property
    def state(self):return deepcopy(self._status)
    @property
    def version_root(self):return self.root/"versions"/self.state["version"]
    def _state(self,**updates):self._status.update(updates);return self.state
    def status(self):return self.state
    def event(self,kind,**values):self.events.append((kind,values))


class FakeLoop:
    def __init__(self, proposal, *, approved=True, pending_audit=False):
        self.proposal=proposal
        self.approved=approved
        self.pending_audit=pending_audit
        self.calls=[]
        self.responses={}
    def request(self,action,kind,context,**kwargs):
        self.calls.append((action,kind,deepcopy(context),kwargs))
        if kind=="framework_patch": response=self.proposal
        elif self.pending_audit:return {"status":"waiting","blocker":{"reason":"synthetic timeout"},"action_id":action}
        else:response={"approved":self.approved,"reason":"Synthetic independent review", "evidence_ids":["synthetic-test-evidence"],"violations":[] if self.approved else ["synthetic rejection"]}
        self.responses[action]=response
        return {"status":"ready","response":response}
    def apply_once(self,action,handler):
        return {"status":"applied","application":handler(self.responses[action],action)}


class Ready:
    def check(self):return {"allowed":True}


def fixture(tmp_path,monkeypatch):
    campaign=FakeCampaign(tmp_path/"campaign")
    workspace=tmp_path/"source"
    target=workspace/host.BASE/"selection.py"
    target.parent.mkdir(parents=True)
    target.write_text("def choose(x):\n    return x\n",encoding="utf-8")
    frozen=workspace/host.BASE/"protocol.py"
    frozen.write_text("YEARS = tuple(range(2019,2025))\n",encoding="utf-8")
    write_json(campaign.root/"active_framework.json",{"version":"V10A","workspace":str(workspace)})
    write_json(campaign.root/"protocol.json",{})
    campaign.version_root.mkdir(parents=True)
    write_json(campaign.version_root/"catalog.json",[
        {"factor_id":"reference","origin":"reference","spec":{"expression":"close"}},
        {"factor_id":"exploration","origin":"new","spec":{"expression":"close/open"}}])
    write_json(campaign.version_root/"summaries.json",{"old":{"worst_ic":.03}})
    write_json(campaign.version_root/"combination_summaries.json",{})
    answer={"answer":"A measured mechanism failed", "evidence_ids":["old"]}
    review={k:answer for k in ("failure_analysis","framework_diagnosis","proposed_improvement","cross_version_comparison")}
    review.update(next_action="revise_framework",proposed_changes=["selection algorithm"],falsifier="No gain")
    write_json(campaign.version_root/"decisions/V10A_batch0002_review.json",review)
    monkeypatch.setattr(host,"_freeze_dependencies",lambda c,w:[frozen])
    proposal={"kind":"framework_patch","component":"scheduler","hypothesis":"Evidence-driven selection", "falsifier":"No improvement", "evidence_ids":["old"],
              "changes":[{"path":host.BASE+"selection.py","content":"def choose(x):\n    return max(x, 0)\n"}]}
    return campaign,workspace,proposal


def test_end_to_end_separate_review_activates_next_version(tmp_path,monkeypatch):
    campaign,workspace,proposal=fixture(tmp_path,monkeypatch)
    loop=FakeLoop(proposal)
    result=host.advance_campaign(campaign,model_loop=loop,test_runner=lambda p:{"passed":True,"synthetic":True},resource_guard=Ready())
    assert result["status"]=="framework_activated_restart_required" and result["version"]=="V11A"
    assert len(loop.calls)==2 and loop.calls[0][1]=="framework_patch" and loop.calls[1][1]=="review"
    assert loop.calls[1][3]["schema"]==host.AUDIT_SCHEMA
    assert campaign.state["primary_evaluated"]==0 and not campaign.state["historical_target_met"]
    assert campaign.state["framework_versions_completed"]==["V10A"]
    inherited=json.loads((campaign.version_root/"inherited_catalog.json").read_text())
    assert [r["origin"] for r in inherited]==["reference","inherited"]
    assert (workspace/host.BASE/"selection.py").read_text()=="def choose(x):\n    return x\n"
    assert host.advance_campaign(campaign,model_loop=loop)["status"]=="framework_activated_restart_required"
    assert len(loop.calls)==2


def test_failed_audit_keeps_parent_and_next_call_uses_new_attempt(tmp_path,monkeypatch):
    campaign,workspace,proposal=fixture(tmp_path,monkeypatch)
    loop=FakeLoop(proposal,approved=False)
    result=host.advance_campaign(campaign,model_loop=loop,test_runner=lambda p:{"passed":True},resource_guard=Ready())
    assert result["phase"]=="framework_patch_rejected" and result["version"]=="V10A"
    assert json.loads((campaign.root/"active_framework.json").read_text())["version"]=="V10A"
    assert len(loop.calls)==2
    loop.approved=True
    assert host.advance_campaign(campaign,model_loop=loop,test_runner=lambda p:{"passed":True},resource_guard=Ready())["version"]=="V11A"
    assert "0002" in loop.calls[-2][0]


def test_pending_independent_audit_reuses_original_context_and_tests(tmp_path,monkeypatch):
    campaign,_,proposal=fixture(tmp_path,monkeypatch)
    loop=FakeLoop(proposal,pending_audit=True)
    tests=[]
    def tester(p):tests.append(str(p));return {"passed":True,"wall_seconds":len(tests)}
    result=host.advance_campaign(campaign,model_loop=loop,test_runner=tester,resource_guard=Ready())
    assert result["phase"]=="waiting" and len(tests)==1
    original_context=loop.calls[-1][2]
    loop.pending_audit=False
    result=host.advance_campaign(campaign,model_loop=loop,test_runner=tester,resource_guard=Ready())
    assert result["version"]=="V11A" and len(tests)==1
    assert loop.calls[-1][2]==original_context


def test_literal_tuning_cannot_publish_framework_version(tmp_path,monkeypatch):
    campaign,workspace,proposal=fixture(tmp_path,monkeypatch)
    (workspace/host.BASE/"selection.py").write_text("def choose(x):\n    return x + 1\n",encoding="utf-8")
    proposal["changes"][0]["content"]="def choose(x):\n    return x + 2\n"
    loop=FakeLoop(proposal)
    result=host.advance_campaign(campaign,model_loop=loop,test_runner=lambda p:pytest.fail("No test for mere tuning"),resource_guard=Ready())
    assert result["phase"]=="framework_patch_rejected" and len(loop.calls)==1


def test_unwired_algorithm_module_cannot_publish_framework(tmp_path,monkeypatch):
    campaign,workspace,proposal=fixture(tmp_path,monkeypatch)
    proposal["changes"]=[{"path":host.BASE+"algorithms/unused.py","content":"def unused(x):\n    return x * x\n"}]
    result=host.advance_campaign(campaign,model_loop=FakeLoop(proposal),test_runner=lambda p:pytest.fail("Unwired algorithm"),resource_guard=Ready())
    assert result["phase"]=="framework_patch_rejected"
    assert "wired" in result["blocker"]["error"]


def test_incomplete_source_scale_is_preserved_and_not_counted_complete(tmp_path,monkeypatch):
    campaign,_,proposal=fixture(tmp_path,monkeypatch)
    campaign._state(primary_evaluated=29,new_evaluated=10,combinations_evaluated=0)
    result=host.advance_campaign(campaign,model_loop=FakeLoop(proposal),test_runner=lambda p:{"passed":True},resource_guard=Ready())
    assert result["version"]=="V11A" and result["framework_versions_completed"]==[]
    closed=json.loads((campaign.root/"versions/V10A/framework_close_snapshot.json").read_text())
    assert not closed["scale_completed"] and closed["state"]["primary_evaluated"]==29


def test_active_pointer_crash_before_state_transition_is_recovered(tmp_path,monkeypatch):
    campaign,_,proposal=fixture(tmp_path,monkeypatch)
    original=host._complete_transition
    monkeypatch.setattr(host,"_complete_transition",lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    loop=FakeLoop(proposal)
    with pytest.raises(KeyboardInterrupt):
        host.advance_campaign(campaign,model_loop=loop,test_runner=lambda p:{"passed":True},resource_guard=Ready())
    assert campaign.state["version"]=="V10A"
    assert json.loads((campaign.root/"active_framework.json").read_text())["version"]=="V11A"
    monkeypatch.setattr(host,"_complete_transition",original)
    result=host.advance_campaign(campaign,model_loop=loop,resource_guard=Ready())
    assert result["version"]=="V11A" and len(loop.calls)==2
