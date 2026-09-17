import hashlib
import json
from types import SimpleNamespace

import pytest

from quanta_agents.factor_campaign.framework_host import _freeze_dependencies


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_original_oracle_and_moved_controller_both_remain_pinned(tmp_path):
    oracle = tmp_path / "original_oracle.py"
    host = tmp_path / "maintenance_host.py"
    oracle.write_text("ORACLE = 1", encoding="utf-8")
    host.write_text("HOST = 2", encoding="utf-8")
    original = tmp_path / "framework_dependency_pins.json"
    original.write_text(json.dumps({str(oracle): _sha(oracle)}), encoding="utf-8")
    original_bytes = original.read_bytes()
    manifest = tmp_path / "maintenance_pins.json"
    manifest.write_text(json.dumps({"files": {str(host): _sha(host)}}), encoding="utf-8")
    index = tmp_path / "framework_additional_dependency_pins.json"
    index.write_text(json.dumps([{"path": str(manifest), "sha256": _sha(manifest)}]), encoding="utf-8")
    campaign = SimpleNamespace(root=tmp_path)
    assert set(_freeze_dependencies(campaign, tmp_path)) == {str(oracle), str(host)}
    assert original.read_bytes() == original_bytes
    host.write_text("HOST = 3", encoding="utf-8")
    with pytest.raises(ValueError, match="dependency changed"):
        _freeze_dependencies(campaign, tmp_path)
    host.write_text("HOST = 2", encoding="utf-8")
    oracle.write_text("ORACLE = 0", encoding="utf-8")
    with pytest.raises(ValueError, match="dependency changed"):
        _freeze_dependencies(campaign, tmp_path)


def test_maintenance_manifest_cannot_silently_repin_modified_host(tmp_path):
    host = tmp_path / "host.py"
    host.write_text("HOST = 1", encoding="utf-8")
    (tmp_path / "framework_dependency_pins.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / "pins.json"
    manifest.write_text(json.dumps({"files": {str(host): _sha(host)}}), encoding="utf-8")
    (tmp_path / "framework_additional_dependency_pins.json").write_text(
        json.dumps([{"path": str(manifest), "sha256": _sha(manifest)}]), encoding="utf-8")
    host.write_text("HOST = 2", encoding="utf-8")
    manifest.write_text(json.dumps({"files": {str(host): _sha(host)}}), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest changed"):
        _freeze_dependencies(SimpleNamespace(root=tmp_path), tmp_path)


def test_new_framework_does_not_inherit_previous_control_counts(tmp_path):
    from quanta_agents.factor_campaign.framework_host import _complete_transition
    root = tmp_path / "versions/V10A"
    root.mkdir(parents=True)
    (root / "catalog.json").write_text("[]", encoding="utf-8")
    parent = {"version": "V10A", "framework_versions_completed": [],
              "combination_controls_evaluated": 3, "combination_controls_attempted": 9}
    class Campaign:
        def __init__(self):
            self.root = tmp_path
            self.state = dict(parent)
        def _state(self, **changes):
            self.state.update(changes)
        def event(self, *args, **kwargs):
            pass
        def status(self):
            return dict(self.state)
    result = _complete_transition(Campaign(), {"parent_state": parent, "next_version": "V11A",
        "patch_id": "tested_patch", "active_workspace": str(tmp_path / "workspace"), "scale_completed": False})
    assert result["combination_controls_evaluated"] == 0
    assert result["combination_controls_attempted"] == 0
    assert parent["combination_controls_attempted"] == 9
    assert result["framework_versions_completed"] == []
