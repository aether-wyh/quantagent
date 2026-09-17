import copy
import json
from quanta_agents.meta_v3.context import bounded, history_context
from quanta_agents.meta_v3.ledger import digest, serial


def test_unicode_escaping_bound_and_no_source_mutation():
    value = {"rows": [{"text": '\\"\n证据' * 20000}], "cash": "9808.44"}
    before = copy.deepcopy(value)
    result = bounded(value)
    assert len(serial(result).encode()) <= 8000
    assert result["original_sha256"] == digest(value)
    assert result["original_bytes"] == len(serial(value).encode())
    assert "9808.44" in result["first_excerpt"] + result["last_excerpt"]
    assert value == before


def test_all_failed_attempt_identities_survive_large_context():
    history = [{"id": str(i), "status": "failed", "response": {"action": "develop_strategy", "arguments_json": "x"*20000},
                "result": {"error": "e"*50000}} for i in range(8)]
    projected = history_context(history)
    assert [x["id"] for x in projected] == [str(i) for i in range(8)]
    assert all(x["status"] == "failed" for x in projected)
    assert len(serial(projected).encode()) < 132000
