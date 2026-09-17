from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from quanta_agents.meta_v6.data import MarketPanel
from quanta_agents.meta_v6.factors import FactorEngine, FactorSpec
from quanta_agents.meta_v6.library import FactorLibrary
from quanta_agents.research_kernel.assets import AssetRegistry
from quanta_agents.research_kernel import assets as module


def panel():
    index = pd.bdate_range("2018-01-01", periods=12, name="date")
    columns = pd.Index(["A", "B", "C"], name="stock")
    opening = pd.DataFrame(np.arange(36, dtype=float).reshape(12, 3) + 20,
                           index=index, columns=columns)
    eligible = opening.notna()
    eligible.iloc[3, 1] = False
    close = opening * 1.01
    close.iloc[6, 0] = np.nan
    return MarketPanel({"open": opening, "close": close, "volume": opening * 1000},
                       eligible, {"scope": "generated_test", "vintage": "one"})


def definition(identity="ma", expression="rolling_mean(close, 3)", **changes):
    return {"id": identity, "name": identity, "expression": expression,
            "roles": ["return"], "source": {"kind": "test"},
            "metadata": {"original_direction": -1}, **changes}


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return file_sha(path)


def test_persistent_cache_alias_dedup_and_no_direction_or_mutation(tmp_path, monkeypatch):
    p = panel()
    registry = AssetRegistry(tmp_path)
    registry.register(definition())
    registry.register(definition("alias", "rolling_mean((close),3)"))
    scores, metrics = registry.resolve(["ma", "alias", "ma"], p)
    expected = FactorEngine(p).compute(FactorSpec("expected", "rolling_mean(close, 3)"))
    assert_frame_equal(scores["ma"], expected)
    assert_frame_equal(scores["ma"], scores["alias"])
    assert metrics["computed"] == 1 and metrics["alias_reuses"] == 1
    assert metrics["requested"] == 3 and metrics["unique_ids"] == 2
    assert metrics["direction_applied"] is False
    scores["ma"].iloc[-1, 0] = -999
    assert_frame_equal(scores["alias"], expected)
    fresh = AssetRegistry(tmp_path)
    monkeypatch.setattr(FactorEngine, "compute", lambda *a: pytest.fail("cache hit recomputed"))
    restored, second = fresh.resolve(["ma", "alias"], p)
    assert_frame_equal(restored["ma"], expected)
    assert second["computed"] == 0 and second["cache_hits"] == 1
    assert second["engine_cache"]["node_evaluations"] == 0
    assert len(list(tmp_path.glob("score_cache/*/manifest.json"))) == 1


def test_shared_dag_subexpression_is_reused(tmp_path):
    r = AssetRegistry(tmp_path)
    r.register(definition("parent", "rolling_mean(close,3)+rolling_mean(close,3)"))
    r.register(definition("child", "rolling_mean(close,3)"))
    _, metrics = r.resolve(["parent", "child"], panel())
    assert metrics["computed"] == 2
    assert metrics["engine_cache"]["node_evaluations"] == 3  # close, mean, sum


@pytest.mark.parametrize("change", ["price", "eligible", "provenance", "axes"])
def test_changed_panel_values_membership_provenance_or_axes_invalidate(tmp_path, change):
    r, p = AssetRegistry(tmp_path), panel()
    r.register(definition())
    _, first = r.resolve(["ma"], p)
    if change == "price":
        p.fields["close"].iloc[-1, 0] += 10
    elif change == "eligible":
        p.eligible.iloc[-1, 0] = False
    elif change == "provenance":
        p.provenance["vintage"] = "two"
    else:
        for frame in [*p.fields.values(), p.eligible]:
            frame.columns = pd.Index(["X", "Y", "Z"], name="stock")
    _, second = r.resolve(["ma"], p)
    assert first["panel_fingerprint"] != second["panel_fingerprint"]
    assert second["computed"] == 1 and second["cache_hits"] == 0


def test_calculator_version_invalidates_cache(tmp_path, monkeypatch):
    r, p = AssetRegistry(tmp_path), panel()
    r.register(definition())
    r.resolve(["ma"], p)
    original = module._calculator_identity
    monkeypatch.setattr(module, "_calculator_identity", lambda: {**original(), "test_version": 2})
    _, result = r.resolve(["ma"], p)
    assert result["computed"] == 1


def test_deep_study_cache_longer_than_windows_max_path_roundtrips(tmp_path, monkeypatch):
    # Exercise the actual long output path, rather than shortening pytest's root.
    # The registry/SQLite root remains below MAX_PATH; full digest paths exceed it.
    base = tmp_path / "deep_study"
    root = base / ("s" * max(1, 175 - len(str(base))))
    registry, p = AssetRegistry(root), panel()
    registry.register(definition())
    first, metrics = registry.resolve(["ma"], p)
    key = metrics["assets"]["ma"]["cache_key"]
    manifest_path = root / "score_cache" / key / "manifest.json"
    # Extended-path spelling in this assertion is independent of the helper.
    native = lambda value: Path("\\\\?\\" + str(value.resolve())) if module.os.name == "nt" else value
    manifest = json.loads(native(manifest_path).read_text(encoding="utf-8"))
    payload = manifest_path.parent / f"scores.{manifest['payload_sha256']}.parquet"
    assert len(str(payload)) > 260
    assert len(payload.parent.name) == 64 and len(manifest["payload_sha256"]) == 64
    assert hashlib.sha256(native(payload).read_bytes()).hexdigest() == manifest["payload_sha256"]
    monkeypatch.setattr(FactorEngine, "compute", lambda *args: pytest.fail("long-path cache was recomputed"))
    second, hit = AssetRegistry(root).resolve(["ma"], p)
    assert_frame_equal(first["ma"], second["ma"])
    assert hit["cache_hits"] == 1 and hit["computed"] == 0 and not hit["corruptions"]


@pytest.mark.parametrize("kind", ["payload", "manifest", "axis_with_valid_hash", "path_injection"])
def test_corrupt_cache_is_repaired_without_trusting_paths(tmp_path, kind):
    r, p = AssetRegistry(tmp_path), panel()
    r.register(definition())
    expected, _ = r.resolve(["ma"], p)
    manifest_path = next(tmp_path.glob("score_cache/*/manifest.json"))
    manifest = json.loads(manifest_path.read_text())
    payload = manifest_path.parent / f"scores.{manifest['payload_sha256']}.parquet"
    outside = tmp_path / "outside.parquet"
    outside.write_bytes(b"do not touch")
    if kind == "payload":
        payload.write_bytes(b"broken parquet")
    elif kind == "manifest":
        manifest["identity"]["expression"] = "close"
        write_json(manifest_path, manifest)
    elif kind == "path_injection":
        manifest["path"] = str(outside)
        write_json(manifest_path, manifest)
    else:
        wrong = expected["ma"].iloc[:-1]
        temporary = manifest_path.parent / "wrong.parquet"
        wrong.to_parquet(temporary)
        digest = file_sha(temporary)
        temporary.rename(manifest_path.parent / f"scores.{digest}.parquet")
        manifest["payload_sha256"] = digest
        write_json(manifest_path, manifest)
    result, metrics = r.resolve(["ma"], p)
    assert len(metrics["corruptions"]) == 1 and metrics["computed"] == 1
    assert_frame_equal(result["ma"], expected["ma"])
    assert outside.read_bytes() == b"do not touch"
    _, final = AssetRegistry(tmp_path).resolve(["ma"], p)
    assert final["cache_hits"] == 1 and not final["corruptions"]


def test_partial_interrupted_write_cannot_be_cache_hit(tmp_path, monkeypatch):
    r = AssetRegistry(tmp_path)
    r.register(definition())
    original = module._atomic_json
    monkeypatch.setattr(module, "_atomic_json", lambda *a: (_ for _ in ()).throw(OSError("interrupted")))
    with pytest.raises(OSError, match="interrupted"):
        r.resolve(["ma"], panel())
    assert not list(tmp_path.glob("score_cache/*/manifest.json"))
    monkeypatch.setattr(module, "_atomic_json", original)
    _, result = r.resolve(["ma"], panel())
    assert result["computed"] == 1 and result["cache_hits"] == 0


def test_missing_and_execution_role_fields_are_local_explicit_failures(tmp_path):
    r, p = AssetRegistry(tmp_path), panel()
    r.register(definition())
    r.register(definition("missing", "fundamental_quality"))
    r.register(definition("noncausal", "quality"))
    p.fields["quality"] = p.fields["open"].copy()
    p.provenance["field_roles"] = {"quality": "label"}
    scores, result = r.resolve(["ma", "missing", "noncausal", "unknown"], p)
    assert set(scores) == {"ma"}
    assert result["complete"] is False
    assert result["unavailable"]["missing"]["missing_fields"] == ["fundamental_quality"]
    assert result["unavailable"]["noncausal"]["missing_fields"] == ["quality"]
    assert result["unavailable"]["unknown"]["reason"] == "unknown_asset"


def test_id_conflict_persistence_search_pagination_and_no_ic_gate(tmp_path):
    r = AssetRegistry(tmp_path)
    record = r.register(definition(metadata={"mechanism": "weak conditional", "prior_ic": 0}))
    assert record["status"] == "executable" and record["profitability_claim"] is False
    assert r.register(definition(expression="rolling_mean((close),3)")) == record
    with pytest.raises(ValueError, match="conflict"):
        r.register(definition(expression="rolling_mean(close,5)"))
    r.register(definition("second", "volume", roles=["condition", "interaction"]))
    assert [x["id"] for x in r.list("weak")] == ["ma"]
    assert len(r.list(limit=1, offset=1)) == 1
    record["metadata"]["mechanism"] = "changed"
    assert AssetRegistry(tmp_path).get("ma")["metadata"]["mechanism"] == "weak conditional"


@pytest.mark.parametrize("change", [{"id": "../escape"}, {"roles": ["alpha"]},
    {"expression": "raw_open"}, {"expression": "lag(close,-1)"},
    {"expression": "__import__('os')"}, {"cache_path": "elsewhere"}])
def test_definition_validation(tmp_path, change):
    with pytest.raises(ValueError):
        AssetRegistry(tmp_path).register(definition(**change))


def test_catalogue_metadata_is_never_executable_even_if_formula_looks_valid(tmp_path, monkeypatch):
    source = tmp_path / "mapping.csv"
    source.write_text("record_id,year,name,formula_key,formula_text,implementation_kind,ic_2025,return_2025\n"
                      "one,2026,Moving average,ma5,rolling_mean(close;5),existing,999,888\n"
                      "two,2024,Close,close,close,completed,777,666\n", encoding="utf-8")
    called = []
    original = pd.read_csv
    def read(*args, **kwargs):
        called.append(kwargs["usecols"])
        return original(*args, **kwargs)
    monkeypatch.setattr(pd, "read_csv", read)
    r = AssetRegistry(tmp_path / "registry")
    report = r.import_metadata(source, "calendar")
    assert report["catalogued"] == 2 and report["executable"] == 0
    assert "ic_2025" not in called[0] and "return_2025" not in called[0]
    assert all(x["expression"] is None and not x["executable"] for x in r.list())
    assert all("ic_2025" not in x["metadata"] and "return_2025" not in x["metadata"] for x in r.list())
    assert all("999" not in x["metadata"].values() and "888" not in x["metadata"].values() for x in r.list())
    frames, metrics = r.resolve(report["ids"], panel())
    assert not frames and len(metrics["unavailable"]) == 2
    assert r.import_metadata(source, "calendar")["ids"] == report["ids"]


def v6_fixture(root, last_role="return_prediction"):
    """Metadata-only V6 manifests and actual immutable registry, no price results."""
    library_path = root / "factor_library.sqlite"
    folders = [root / "study", root / "study/cycles/03_factor_information_expansion"]
    with FactorLibrary(library_path) as library:
        for phase, folder in enumerate(folders):
            count = 9 if phase == 0 else 3
            entries, declarations = [], []
            for number in range(count):
                key = f"A{number}" if phase == 0 else ["HF0280", "F7", "F8"][number]
                expression = f"rolling_mean(close,{number + 2})" if phase == 0 else (
                    "hf0280_triple_ols20_v1" if number == 0 else f"rolling_std(close,{number + 2})")
                direction = -1 if key == "F7" else 1
                role = "risk_information" if key == "F7" else (last_role if key == "F8" else "return_prediction")
                spec = FactorSpec(key, expression, metadata={"role": role})
                original = {"name": key, "expression": expression, "direction": direction}
                library.register_factor(spec)
                spec_path = folder / "factors" / key / "spec.json"
                spec_hash = write_json(spec_path, {"factor_key": key, "original": original, "spec": spec.to_dict()})
                entries.append({"factor_key": key, "name": key, "factor_id": spec.factor_id,
                    "direction": direction, "role": role, "status": "evaluated", "primary_horizon": 5,
                    "artifacts": [{"path": str(spec_path), "sha256": spec_hash}]})
                declarations.append({"factor_key": key, "original": original} if phase == 0 else original)
            declaration = {"declarations": declarations} if phase == 0 else {
                "fixed_seeds": declarations[:1], "model_factors": declarations[1:]}
            decl_hash = write_json(folder / "factor_declaration.json", declaration)
            snapshot = library.create_snapshot(scope={"dates": "synthetic metadata"})
            write_json(folder / "factor_index.json", {"status": "completed", "factor_count": count,
                "factor_declaration_sha256": decl_hash, "factors": entries,
                "library_path": str(library_path), "library_snapshot_id": snapshot})
    return folders[0]


def test_v6_import_checks_metadata_registry_and_preserves_operator_gap(tmp_path, monkeypatch):
    study = v6_fixture(tmp_path / "old")
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **kw: pytest.fail("metadata import read scores"))
    r = AssetRegistry(tmp_path / "new")
    result = r.import_v6(study)
    assert result["imported"] == 12 and result["executable"] == 11
    assert set(result["unavailable"]) == {"HF0280"}
    assert r.get("F7")["roles"] == ["risk"]
    assert r.get("F7")["metadata"]["original_direction"] == -1
    assert r.get("HF0280")["expression"] == "hf0280_triple_ols20_v1"
    assert not r.get("HF0280")["executable"]
    assert r.import_v6(study)["ids"] == result["ids"]
    # Even a user-supplied virtual field cannot silently enable the missing operator.
    p = panel()
    p.fields["hf0280_triple_ols20_v1"] = p.fields["close"].copy()
    frames, metrics = r.resolve(["HF0280"], p)
    assert not frames and "no_approximation" in metrics["unavailable"]["HF0280"]["reason"]


def test_v6_conditional_gate_role_is_preserved(tmp_path):
    study = v6_fixture(tmp_path / "old", last_role="conditional_gate")
    registry = AssetRegistry(tmp_path / "new")
    registry.import_v6(study)
    assert registry.get("F8")["roles"] == ["condition"]
    assert registry.get("F8")["metadata"]["original_role"] == "conditional_gate"


@pytest.mark.parametrize("kind", ["spec", "declaration", "registry", "incomplete"])
def test_v6_import_refuses_bad_identity_without_partial_registration(tmp_path, kind):
    study = v6_fixture(tmp_path / "old")
    if kind == "spec":
        p = study / "factors/A0/spec.json"
        p.write_text(p.read_text() + " ")
    elif kind == "declaration":
        p = study / "factor_declaration.json"
        p.write_text(p.read_text() + " ")
    elif kind == "registry":
        p = tmp_path / "old/factor_library.sqlite"
        with sqlite3.connect(p) as db:
            db.execute("DROP TRIGGER factor_library_no_update")
            db.execute("UPDATE factor_library_events SET event_hash='bad' WHERE kind='factor'")
    else:
        p = study / "factor_index.json"
        value = json.loads(p.read_text())
        value["status"] = "running"
        write_json(p, value)
    registry = AssetRegistry(tmp_path / "new")
    with pytest.raises(ValueError):
        registry.import_v6(study)
    assert registry.list() == []
