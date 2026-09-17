"""Prevent a real long-event page from losing its middle in model context."""
from copy import deepcopy
import json

from quanta_agents.meta_v3.context import bounded
from quanta_agents.meta_v3.evidence_views import compact_events, page_for_context
from quanta_agents.meta_v3.ledger import digest, serial
from quanta_agents.meta_v3.research_tools import ResearchTools
from test_meta_v3_real_entry import case


def events():
    return [{"event_id":digest({"generated":i}), "symbol":"sh600004", "signal_date":"2019-06-13",
        "feature":-0.000123456789, "included_common_sample":i%2==0, "entry_date":"2019-06-14",
        "entry_open":12.34, "exclusion_reasons":[] if i%2==0 else ["missing future endpoint"],
        "outcomes":{str(h):{"horizon_sessions":h, "exit_date":"2019-06-24" if i%2==0 else None,
            "exit_open":12.11 if i%2==0 else None, "gross_return":-0.018638573743922 if i%2==0 else None,
            "individually_available":i%2==0, "exclusion_reasons":[] if i%2==0 else ["missing future endpoint"]}
            for h in (1,5,10)}} for i in range(42)]


def wrap(page, view):
    return {"evidence_id":"generated_page_001", "action":"read_evidence", "artifact_hash":digest(page),
            "public":view, "execution_valid":False, "formal_target_success":False}


def test_all_events_losses_and_missing_values_survive_contiguous_paging():
    rows=events(); before=deepcopy(rows); offset=0; delivered=[]; pages=0
    original=ResearchTools._page(rows,{"offset":0,"limit":32})
    assert len(serial(wrap(original,compact_events(original))).encode()) > 8000
    while offset is not None:
        requested=ResearchTools._page(rows,{"offset":offset,"limit":32})
        artifact,view=page_for_context(requested,compact_events,wrap,32)
        result=wrap(artifact,view)
        assert bounded(result)==result and len(serial(result).encode())<=8000
        assert view["returned_rows"]==len(artifact["rows"])>0
        assert view["source_page_sha256"]==digest(artifact)
        delivered.extend(view["rows"]); pages+=1
        new_offset=view["next_offset"]
        assert new_offset is None or new_offset==offset+view["returned_rows"]
        offset=new_offset
    whole={"rows":rows,"offset":0,"next_offset":None,"total_rows":42}
    assert delivered==compact_events(whole)["rows"] and rows==before and pages>1


def test_single_oversized_row_is_explicitly_blocked_without_skipping():
    original={"rows":[{"raw":"缺失不能推断为零"*10000}],"offset":7,"next_offset":8,"total_rows":9}
    before=deepcopy(original)
    artifact,view=page_for_context(original,lambda x:x,wrap,1)
    assert artifact==original==before and view["delivery_blocked"]
    assert view["returned_rows"]==0 and view["next_offset"]==7
    assert view["oversized_row_sha256"]==digest(original["rows"][0])
    assert bounded(wrap(artifact,view))==wrap(artifact,view)


def test_tool_entry_saves_exact_page_and_returns_matching_cursor(tmp_path):
    prior={"tables":{"events":events()}}
    history=[{"id":"prior","response":{"action":"diagnose_horizons"},"result":{"artifact_hash":digest(prior)}}]
    tools=ResearchTools(tmp_path/"stage","unit",case(tmp_path),history)
    folder=tools.folder/"prior";folder.mkdir();(folder/"artifact.json").write_text(serial(prior),encoding="utf-8")
    result=tools.execute("page","read_evidence",{"evidence_id":"prior","table":"events_compact","offset":10,"limit":32})
    saved=json.loads((tools.folder/"page/artifact.json").read_text(encoding="utf-8"))
    assert digest(saved)==result["artifact_hash"]==result["public"]["source_page_sha256"]
    assert 0<len(saved["rows"])<32 and saved["rows"]==prior["tables"]["events"][10:10+len(saved["rows"])]
    assert bounded(result)==result and result["public"]["next_offset"]==10+len(saved["rows"])
    assert json.loads((folder/"artifact.json").read_text(encoding="utf-8"))==prior
