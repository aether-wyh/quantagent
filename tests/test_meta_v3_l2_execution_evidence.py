from copy import deepcopy
from datetime import datetime

from quanta_agents.meta_v3.l2_execution_evidence import finite_depth_match, assess_order


POLICY={"decision_local_time":"09:35:00","assumed_feed_delay_ms":1000,
    "max_decision_quote_source_age_ms":4000,"assumed_order_latency_ms":1000,
    "max_execution_snapshot_delay_ms":4000,"per_level_displayed_depth_fraction":"0.10",
    "buy_limit_vs_decision_ask_fraction":"0.001","sell_limit_vs_decision_bid_fraction":"0.001",
    "requested_sleeve_cash":"100000.00","unit_lot":100,"price_scale":10000,"tick_scaled":100}


def quote(clock="09:35:01",seq=2):
    ts=datetime.fromisoformat("2026-01-07T"+clock)
    row={"wind_code":"600006.SH","date":"2026-01-07","event_ts":ts,"source_row_no":seq,
         "time_raw":ts.hour*10000000+ts.minute*100000+ts.second*1000}
    for side in ("ask","bid"):
        for n in range(1,11):
            row[f"{side}_price_{n}_x1e4"]=100000+(n-1)*100 if side=="ask" and n<=2 else 99900-(n-1)*100 if side=="bid" and n<=2 else 0
            row[f"{side}_volume_{n}"]=(1700 if n==1 else 2700) if n<=2 else 0
    return row


def test_finite_depth_partial_fill_prices_and_unmatched_remainder():
    row=quote();before=deepcopy(row)
    r=finite_depth_match(row,"buy",1000,100200,POLICY)
    assert r["status"]=="partial_reference_match" and r["matched_reference_quantity_native"]==400
    assert r["unmatched_reference_quantity_native"]==600 and r["quoted_notional_excluding_fees"]=="4002.3"
    assert [x["matched_quantity_native"] for x in r["allocations"]]==[170,230]
    assert row==before and r["actual_fill_verified"] is False


def test_order_size_is_frozen_before_future_execution_price_and_depth():
    decision=quote("09:34:58",1);execute=quote();rows=[decision,execute]
    first=assess_order(rows,"600006.SH","2026-01-07","buy",POLICY)
    worse=deepcopy(execute)
    for side in ("ask","bid"):
        for n in (1,2):worse[f"{side}_price_{n}_x1e4"]+=10000
    second=assess_order([decision,worse],"600006.SH","2026-01-07","buy",POLICY)
    assert first["requested_quantity_native"]==second["requested_quantity_native"]==9900
    assert first["limit_price_scaled"]==second["limit_price_scaled"]==100100
    assert first["matched_reference_quantity_native"]==400 and second["matched_reference_quantity_native"]==0
    later=quote("09:36:00",3)
    assert assess_order(rows+[later],"600006.SH","2026-01-07","buy",POLICY)==first


def test_no_skip_of_invalid_first_execution_quote():
    decision=quote("09:34:58",1);bad=quote();bad["ask_volume_1"]=None
    later=quote("09:35:02",3)
    r=assess_order([decision,bad,later],"600006.SH","2026-01-07","buy",POLICY)
    assert r["status"]=="rejected_evidence" and r["matched_reference_quantity_native"]==0
    assert r["execution_snapshot"]["source_row_no"]==2


def test_stale_and_duplicate_quotes_remain_failures():
    stale=quote("09:34:54",1);execution=quote()
    r=assess_order([stale,execution],"600006.SH","2026-01-07","buy",POLICY)
    assert r["status"]=="rejected_evidence" and "stale" in r["reasons"][0]
    decision=quote("09:34:58",1)
    r=assess_order([decision,decision,execution],"600006.SH","2026-01-07","buy",POLICY)
    assert "duplicate" in r["reasons"][0]


def test_sell_uses_bid_depth_and_cannot_exceed_reference_quantity():
    r=finite_depth_match(quote(),"sell",300,99800,POLICY)
    assert r["matched_reference_quantity_native"]==300 and r["unmatched_reference_quantity_native"]==0
    assert r["quoted_notional_excluding_fees"]=="2995.7"
    assert all(x["price_scaled"]<=99900 for x in r["allocations"])
