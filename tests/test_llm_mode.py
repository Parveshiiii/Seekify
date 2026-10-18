import socket
from types import SimpleNamespace

import httpx
import pytest

from seekify import page_content
from seekify.exceptions import RatelimitException
from seekify.search import Search


def test_fetch_page_text_extracts_readable_html(monkeypatch):
    monkeypatch.setattr(
        page_content.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))],
    )
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><head><title>Page</title><script>hidden()</script></head>"
            "<body><nav>Navigation</nav><main>Useful article text</main></body></html>",
        )
    )

    with httpx.Client(transport=transport) as client:
        text, truncated = page_content.fetch_page_text(client, "http://example.com/article")

    assert text == "Page Useful article text"
    assert not truncated


def test_fetch_page_text_blocks_redirect_to_private_address(monkeypatch):
    requested_urls = []

    def resolve(host, port, **_kwargs):
        if host == "example.com":
            address = "93.184.216.34"
        else:
            address = "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

    def respond(request):
        requested_urls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})

    monkeypatch.setattr(page_content.socket, "getaddrinfo", resolve)
    with httpx.Client(transport=httpx.MockTransport(respond), follow_redirects=False) as client:
        with pytest.raises(ValueError, match="non-public"):
            page_content.fetch_page_text(client, "https://example.com/article")

    assert requested_urls == ["https://example.com/article"]


def test_fetch_page_text_caps_content_length(monkeypatch):
    monkeypatch.setattr(
        page_content.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))],
    )
    monkeypatch.setattr(page_content, "_MAX_CONTENT_CHARS", 12)
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text=f"<main>{'x' * 20}</main>",
        )
    )

    with httpx.Client(transport=transport) as client:
        text, truncated = page_content.fetch_page_text(client, "http://example.com/article")

    assert text == "x" * 12
    assert truncated


def test_llm_payload_includes_sources_and_page_content(monkeypatch):
    class FakeHttpClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    monkeypatch.setattr("seekify.search.httpx.Client", FakeHttpClient)
    monkeypatch.setattr(
        "seekify.search.fetch_page_text",
        lambda _client, url: (f"Extracted from {url}", False),
    )

    search = Search.__new__(Search)
    search._proxy = None
    search._timeout = 5
    search._verify = True
    payload = search._format_llm_results(
        "seekify",
        [
            {"title": "Seekify", "href": "https://example.com", "body": "Search snippet"},
            {"title": "Guide", "href": "https://docs.example.com", "body": "Guide snippet"},
        ],
        {"https://example.com": {"google", "bing"}},
    )

    assert payload["schema_version"] == "1.0"
    assert payload["query"] == "seekify"
    assert payload["results"][0] == {
        "rank": 1,
        "title": "Seekify",
        "url": "https://example.com",
        "snippet": "Search snippet",
        "content": "Extracted from https://example.com",
        "content_status": "ok",
        "sources": ["bing", "google"],
        "metadata": {},
    }
    assert payload["results"][1]["content"] == "Extracted from https://docs.example.com"


def test_llm_payload_fetches_only_top_five(monkeypatch):
    class FakeHttpClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    fetched = []

    def fetch(_client, url):
        fetched.append(url)
        return "page content", False

    monkeypatch.setattr("seekify.search.httpx.Client", FakeHttpClient)
    monkeypatch.setattr("seekify.search.fetch_page_text", fetch)
    search = Search.__new__(Search)
    search._proxy = None
    search._timeout = 5
    search._verify = True
    payload = search._format_llm_results(
        "query",
        [{"title": str(i), "href": f"https://example.com/{i}"} for i in range(7)],
        {},
    )

    assert len(fetched) == 5
    assert payload["results"][4]["content_status"] == "ok"
    assert payload["results"][5]["content_status"] == "not_fetched_limit"
    assert payload["results"][6]["content"] == ""


def test_llm_payload_can_fetch_more_than_five_pages(monkeypatch):
    class FakeHttpClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    fetched = []

    def fetch(_client, url):
        fetched.append(url)
        return "page content", False

    monkeypatch.setattr("seekify.search.httpx.Client", FakeHttpClient)
    monkeypatch.setattr("seekify.search.fetch_page_text", fetch)
    search = Search.__new__(Search)
    search._proxy = None
    search._timeout = 5
    search._verify = True
    payload = search._format_llm_results(
        "query",
        [{"title": str(i), "href": f"https://example.com/{i}"} for i in range(7)],
        {},
        max_pages=7,
    )

    assert len(fetched) == 7
    assert payload["results"][6]["content_status"] == "ok"


def test_llm_payload_can_skip_page_fetches(monkeypatch):
    search = Search.__new__(Search)
    payload = search._format_llm_results(
        "query",
        [{"title": "Result", "href": "https://example.com"}],
        {},
        max_pages=0,
    )

    assert payload["results"][0]["content"] == ""
    assert payload["results"][0]["content_status"] == "not_fetched_limit"


def test_llm_page_limit_must_be_non_negative_integer():
    search = Search.__new__(Search)

    with pytest.raises(ValueError, match="non-negative integer"):
        search._format_llm_results("query", [], {}, max_pages=-1)


def test_text_llm_mode_returns_structured_payload(monkeypatch):
    search = Search.__new__(Search)
    monkeypatch.setattr(
        search,
        "_search",
        lambda category, query, **_kwargs: [{"title": query, "href": "https://example.com"}]
        if category == "text"
        else [],
    )
    monkeypatch.setattr(
        search,
        "_format_llm_results",
        lambda query, results, sources, max_pages: {
            "query": query,
            "results": results,
            "sources": sources,
            "max_pages": max_pages,
        },
    )

    payload = search.text("seekify", llm=True, llm_max_pages=8)

    assert payload["query"] == "seekify"
    assert payload["results"][0]["title"] == "seekify"
    assert payload["max_pages"] == 8


def test_search_propagates_rate_limit_when_no_backend_succeeds(monkeypatch):
    class RateLimitedEngine:
        name = "rate-limited"
        provider = "rate-limited"

        def search(self, *_args, **_kwargs):
            raise RatelimitException.from_response("rate-limited", {"Retry-After": "30"})

    class InlineExecutor:
        def submit(self, function, *args, **kwargs):
            from concurrent.futures import Future

            future = Future()
            try:
                future.set_result(function(*args, **kwargs))
            except Exception as ex:
                future.set_exception(ex)
            return future

    search = Search.__new__(Search)
    search._timeout = 1
    monkeypatch.setattr(search, "_get_engines", lambda *_args: [RateLimitedEngine()])
    monkeypatch.setattr(search, "get_executor", lambda: InlineExecutor())

    with pytest.raises(RatelimitException, match="rate limited the request") as error:
        search._search("text", "query", max_results=1)

    assert error.value.retry_after == 30
