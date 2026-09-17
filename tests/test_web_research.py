from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from quanta_agents.web_research import (
    HttpResponse,
    WebResearchClient,
    WebResearchConfig,
)


PUBLIC_IP = ["93.184.216.34"]


def public_resolver(_hostname: str) -> list[str]:
    return PUBLIC_IP


class FakeTransport:
    def __init__(self, handler):
        self.handler = handler
        self.calls: list[str] = []

    def __call__(
        self,
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> HttpResponse:
        self.calls.append(url)
        return self.handler(url, headers, timeout_seconds, max_response_bytes)


def make_response(
    url: str,
    body: str | bytes,
    *,
    status_code: int = 200,
    content_type: str = "text/html; charset=utf-8",
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    raw_body = body.encode("utf-8") if isinstance(body, str) else body
    response_headers = {"content-type": content_type}
    response_headers.update(headers or {})
    return HttpResponse(
        status_code=status_code,
        headers=response_headers,
        body=raw_body,
        url=url,
    )


def test_search_web_uses_no_key_sources_and_records_sources(tmp_path: Path) -> None:
    ddg_html = """
    <html><body>
      <div class="result">
        <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fmarket-study">Market study</a>
        <a class="result__snippet">Evidence about volume and informed trading.</a>
      </div>
    </body></html>
    """
    openalex_json = json.dumps(
        {
            "results": [
                {
                    "display_name": "Trading volume in China",
                    "publication_date": "2023-06-10",
                    "doi": "https://doi.org/10.1234/openalex",
                    "primary_location": {
                        "landing_page_url": "https://papers.example.org/openalex"
                    },
                    "abstract_inverted_index": {
                        "volume": [0],
                        "predicts": [1],
                        "returns": [2],
                    },
                }
            ]
        }
    )
    crossref_json = json.dumps(
        {
            "message": {
                "items": [
                    {
                        "title": ["A later paper"],
                        "URL": "https://doi.org/10.1234/crossref",
                        "abstract": "<jats:p>A later result.</jats:p>",
                        "published-online": {"date-parts": [[2025, 1, 2]]},
                    }
                ]
            }
        }
    )

    def handler(url: str, *_args) -> HttpResponse:
        hostname = urlsplit(url).hostname
        if hostname == "html.duckduckgo.com":
            return make_response(url, ddg_html)
        if hostname == "api.openalex.org":
            return make_response(url, openalex_json, content_type="application/json")
        if hostname == "api.crossref.org":
            return make_response(url, crossref_json, content_type="application/json")
        raise AssertionError(f"unexpected URL: {url}")

    record_path = tmp_path / "sources.jsonl"
    transport = FakeTransport(handler)
    client = WebResearchClient(
        record_path=record_path,
        transport=transport,
        resolver=public_resolver,
    )

    result = client.search_web(
        "China volume informed trading",
        max_results=6,
        source_cutoff_date="2024-12-31",
    )

    assert result["passed"] is True
    assert result["status"] == "ok"
    assert len(transport.calls) == 3
    results = result["results"]
    assert isinstance(results, list)
    assert {item["provider"] for item in results} == {"openalex"}
    openalex_result = results[0]
    assert openalex_result["published_at"] == "2023-06-10"
    assert openalex_result["cutoff_status"] == "within_cutoff"
    assert openalex_result["usable_for_evidence"] is True
    assert result["excluded_result_count"] == 2
    assert result["excluded_by_cutoff"] == {"unknown": 1, "after_cutoff": 1}
    serialized_result = json.dumps(result, ensure_ascii=False)
    assert "Market study" not in serialized_result
    assert "https://example.com/market-study" not in serialized_result
    assert "A later paper" not in serialized_result
    assert "https://doi.org/10.1234/crossref" not in serialized_result

    records = [json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 3
    for record in records:
        assert record["record_type"] == "web_search_result"
        assert record["query"] == "China volume informed trading"
        assert record["title"]
        assert record["url"].startswith("https://")
        assert record["retrieved_at"]
        assert record["source_cutoff_date"] == "2024-12-31"
        assert "published_at" in record
        assert "summary" in record
        assert len(record["content_sha256"]) == 64


def test_open_url_extracts_text_date_and_hash_without_saving_full_page(tmp_path: Path) -> None:
    html = """
    <html>
      <head>
        <meta property="og:title" content="Exchange research note">
        <meta property="article:published_time" content="2024-05-06T09:30:00+08:00">
        <script>ignore this instruction</script>
      </head>
      <body>
        <nav>menu text</nav>
        <article><h1>Main heading</h1><p>Volume increased for two days.</p></article>
        <footer>footer text</footer>
      </body>
    </html>
    """

    transport = FakeTransport(lambda url, *_args: make_response(url, html))
    record_path = tmp_path / "opened.jsonl"
    client = WebResearchClient(
        record_path=record_path,
        transport=transport,
        resolver=public_resolver,
    )

    result = client.open_url(
        "https://exchange.example/research/1",
        query="two-day volume",
        source_cutoff_date="2024-12-31",
    )

    assert result["passed"] is True
    assert result["title"] == "Exchange research note"
    assert result["published_at"] == "2024-05-06"
    assert result["cutoff_status"] == "within_cutoff"
    assert result["usable_for_evidence"] is True
    assert "Volume increased for two days." in result["content"]
    assert "ignore this instruction" not in result["content"]
    assert "menu text" not in result["content"]
    assert "footer text" not in result["content"]
    assert len(result["content_sha256"]) == 64

    stored = json.loads(record_path.read_text(encoding="utf-8").strip())
    assert stored["record_type"] == "opened_web_source"
    assert stored["query"] == "two-day volume"
    assert stored["title"] == "Exchange research note"
    assert stored["url"] == "https://exchange.example/research/1"
    assert stored["source_cutoff_date"] == "2024-12-31"
    assert "content" not in stored


def test_open_url_blocks_direct_and_dns_resolved_private_addresses() -> None:
    transport = FakeTransport(lambda url, *_args: make_response(url, "never called"))
    client = WebResearchClient(
        transport=transport,
        resolver=lambda _hostname: ["10.2.3.4"],
    )

    direct = client.open_url("http://127.0.0.1/admin")
    resolved = client.open_url("https://private.example/admin")

    assert direct["passed"] is False
    assert direct["status"] == "blocked"
    assert resolved["passed"] is False
    assert resolved["status"] == "blocked"
    assert transport.calls == []


def test_normal_domain_may_use_codex_external_proxy_but_direct_proxy_ip_is_blocked() -> None:
    transport = FakeTransport(lambda url, *_args: make_response(url, "public page"))
    client = WebResearchClient(
        transport=transport,
        resolver=lambda _hostname: ["198.18.12.34"],
    )

    resolved = client.open_url("https://public.example/article")
    direct = client.open_url("https://198.18.12.34/article")

    assert resolved["passed"] is True
    assert direct["passed"] is False
    assert direct["status"] == "blocked"
    assert transport.calls == ["https://public.example/article"]


def test_open_url_hides_late_and_unknown_page_details_from_caller() -> None:
    late_html = """
    <html><head>
      <title>Late secret title</title>
      <meta property="article:published_time" content="2025-01-02">
    </head><body>Late secret body.</body></html>
    """
    unknown_html = """
    <html><head><title>Unknown secret title</title></head>
    <body>Unknown secret body.</body></html>
    """

    def handler(url: str, *_args) -> HttpResponse:
        return make_response(url, late_html if url.endswith("/late") else unknown_html)

    client = WebResearchClient(
        transport=FakeTransport(handler),
        resolver=public_resolver,
    )

    late = client.open_url(
        "https://example.com/late",
        source_cutoff_date="2024-12-31",
    )
    unknown = client.open_url(
        "https://example.com/unknown",
        source_cutoff_date="2024-12-31",
    )

    assert late == {
        "passed": False,
        "status": "filtered_by_cutoff",
        "cutoff_status": "after_cutoff",
        "excluded_result_count": 1,
    }
    assert unknown["status"] == "filtered_by_cutoff"
    assert unknown["cutoff_status"] == "unknown"
    hidden = json.dumps([late, unknown], ensure_ascii=False)
    for forbidden in (
        "Late secret title",
        "Late secret body",
        "Unknown secret title",
        "Unknown secret body",
        "https://example.com/late",
        "https://example.com/unknown",
    ):
        assert forbidden not in hidden


def test_redirect_to_private_address_is_blocked_before_second_request() -> None:
    def handler(url: str, *_args) -> HttpResponse:
        return make_response(
            url,
            b"",
            status_code=302,
            headers={"location": "http://169.254.169.254/latest/meta-data"},
        )

    transport = FakeTransport(handler)
    client = WebResearchClient(transport=transport, resolver=public_resolver)

    result = client.open_url("https://public.example/redirect")

    assert result["passed"] is False
    assert result["status"] == "blocked"
    assert transport.calls == ["https://public.example/redirect"]


def test_network_failure_returns_unavailable_and_does_not_raise(tmp_path: Path) -> None:
    def offline(*_args):
        raise TimeoutError("offline")

    transport = FakeTransport(offline)
    record_path = tmp_path / "failures.jsonl"
    client = WebResearchClient(
        record_path=record_path,
        transport=transport,
        resolver=public_resolver,
    )

    search_result = client.search_web(
        "volume research",
        providers=("duckduckgo",),
    )
    open_result = client.open_url("https://example.com/article")

    assert search_result["passed"] is False
    assert search_result["status"] == "unavailable"
    assert open_result["passed"] is False
    assert open_result["status"] == "unavailable"
    records = [json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()]
    assert {record["record_type"] for record in records} == {
        "web_search_call",
        "web_open_failure",
    }


def test_response_size_limit_returns_unavailable() -> None:
    config = WebResearchConfig(max_response_bytes=10)
    transport = FakeTransport(lambda url, *_args: make_response(url, b"12345678901"))
    client = WebResearchClient(
        config=config,
        transport=transport,
        resolver=public_resolver,
    )

    result = client.open_url("https://example.com/large")

    assert result["passed"] is False
    assert result["status"] == "unavailable"
    assert "大小超过限制" in result["error"]


def test_unsafe_scheme_is_blocked_without_network_access() -> None:
    transport = FakeTransport(lambda url, *_args: make_response(url, "never called"))
    client = WebResearchClient(transport=transport, resolver=public_resolver)

    result = client.open_url("file:///etc/passwd")

    assert result["passed"] is False
    assert result["status"] == "blocked"
    assert transport.calls == []
