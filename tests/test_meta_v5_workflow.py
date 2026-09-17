"""Actual immutable catalog and tool-dispatch integration, without any model."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from quanta_agents.meta_v3.ledger import AdmissionBlocked, digest


SPEC = importlib.util.spec_from_file_location("v5_workflow_demo", Path(__file__).resolve().parents[1] / "scripts/demo_research_v5.py")
DEMO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEMO)


def setup(tmp_path):
    tools, catalog, identity = DEMO.create_demo_tools(tmp_path / "stage")
    profile = catalog.profiles()["synthetic_difference"]
    return tools, catalog, identity, profile


def record(tools, profile):
    return DEMO.saved_call(tools, "record_stability_reflection", {"profile_id": "synthetic_difference", "declaration": DEMO.fixture_reflection(profile)})


def test_real_catalog_pages_reflection_saved_history_and_research_state(tmp_path):
    report = DEMO.run_demo(tmp_path / "demo")
    assert report["status"] == "completed_engineering_only"
    assert report["model_calls"] == report["network_calls"] == report["market_value_reads"] == 0
    assert report["missing_read_reflection_rejected"]
    pages = report["page_deliveries"]
    delivered_cells = [cell for page in pages if page["table"] == "cells" for cell in page["delivered_ids"]]
    assert len(delivered_cells) == len(set(delivered_cells)) == report["cell_count"] == 4
    delivered_issues = [issue for page in pages if page["table"] == "issues" for issue in page["delivered_ids"]]
    assert len(delivered_issues) == len(set(delivered_issues)) == report["issue_count"] > 0
    candidate = report["research_state"]["candidates"][0]
    assert candidate["reflection_evidence_id"] == report["reflection_evidence_id"]
    assert any(a["action"] == "run_discriminating_experiment" for a in candidate["next_actions"])
    assert all(a["unresolved_issue_ids"] for a in candidate["next_actions"])
    assert not report["formal_target_success"] and not report["causal_mechanism_identified"]


@pytest.mark.parametrize("omitted", ["summary", "cells", "issues"])
def test_each_required_table_must_really_be_delivered(tmp_path, omitted):
    tools, _, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference", tables=tuple(t for t in ("summary", "cells", "issues") if t != omitted))
    with pytest.raises(AdmissionBlocked, match="read"):
        record(tools, profile)
    assert tools._reflection(profile) is None


def test_reading_first_cell_page_does_not_count_as_full_scope_read(tmp_path):
    tools, _, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference", tables=("summary", "issues"))
    first = DEMO.saved_call(tools, "inspect_stability", {"profile_id": "synthetic_difference", "table": "cells", "offset": 0, "limit": 1})
    assert first["public"]["next_offset"] == 1
    with pytest.raises(AdmissionBlocked, match="all original annual/unit cells"):
        record(tools, profile)


def test_rehashed_catalog_profile_cannot_replace_controller_pinned_identity(tmp_path):
    tools, catalog, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference")
    path = catalog.folder / "synthetic_difference.profile.json"
    forged = json.loads(path.read_text(encoding="utf-8"))
    forged["cells"][0]["candidate_metrics"]["return"] = 99.
    forged["profile_hash"] = digest({k:v for k,v in forged.items() if k != "profile_hash"})
    path.write_text(json.dumps(forged), encoding="utf-8")
    with pytest.raises(AdmissionBlocked, match="profile drift"):
        record(tools, profile)


def test_changed_source_is_rejected_even_when_saved_profile_itself_did_not_change(tmp_path):
    tools, catalog, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference")
    (tools.root / "generation.json").write_text("changed source identity", encoding="utf-8")
    with pytest.raises(AdmissionBlocked, match="source changed"):
        record(tools, profile)


def test_tampered_page_cannot_forge_read_coverage(tmp_path):
    tools, _, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference")
    page = next(r for r in tools.history if r["response"]["action"] == "inspect_stability")
    path = tools.folder / page["id"] / "artifact.json"
    artifact = json.loads(path.read_text(encoding="utf-8"))
    artifact["delivered_ids"] = ["invented"]
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(AdmissionBlocked, match="saved tool evidence changed"):
        record(tools, profile)


def test_reflection_artifact_has_top_profile_binding_and_tampering_breaks_state(tmp_path):
    tools, _, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference")
    result = record(tools, profile)
    artifact = tools._prior(result["evidence_id"], "record_stability_reflection")
    assert artifact["profile_hash"] == profile["profile_hash"]
    assert tools._reflection(profile)[0] == result["evidence_id"]
    artifact["formal_target_success"] = True
    path = tools.folder / result["evidence_id"] / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(AdmissionBlocked, match="saved tool evidence changed"):
        tools.research_state()


def test_model_cannot_submit_profile_or_nav_through_reflection_tool(tmp_path):
    tools, _, _, profile = setup(tmp_path)
    DEMO.read_pages(tools, "synthetic_difference")
    args = {"profile_id": "synthetic_difference", "declaration": DEMO.fixture_reflection(profile), "nav": [100., 200.]}
    with pytest.raises(AdmissionBlocked, match="reflection action exact fields"):
        DEMO.saved_call(tools, "record_stability_reflection", args)


def test_demo_requires_new_directory_and_never_overwrites_prior_receipts(tmp_path):
    path = tmp_path / "existing"
    path.mkdir()
    marker = path / "keep.txt"; marker.write_text("preserve")
    with pytest.raises(FileExistsError):
        DEMO.run_demo(path)
    assert marker.read_text() == "preserve"
