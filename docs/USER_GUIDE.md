# User Guide

## Core Concepts

The main entry point is the `Search` class. It manages the connection logic, proxies, and threading for various search backends.

```python
from seekify import Search
```

It is recommended to use `Search` as a context manager (`with` statement) to ensure resources are cleaned up properly.

## Text Search

Perform broad web searches.

```python
with Search() as s:
    results = s.text(
        query="python",
        region="us-en",   # "uk-en", "ru-ru", etc.
        safesearch="moderate", # "on", "off"
        max_results=20,
        backend="auto"    # "google", "bing", "duckduckgo", etc.
    )
```

**Backends**: `google`, `bing`, `duckduckgo`, `brave`, `yahoo`, `yandex`, `mojeek`, `grokipedia`, `wikipedia`.

### LLM-ready results

Pass `llm=True` to text search to get a structured payload with ranked results,
source-engine names, snippets, and cleaned page text. By default, it fetches
the first five results; use `llm_max_pages` to change this, or set it to `0` to
skip page fetching. The value must be a non-negative integer. Page text is
capped at 5,000 characters per page. Page retrieval uses HTTPX and HTML text
extraction uses lxml. Individual fetch failures are reported in that result's
`content_status` and `content_error`; they do not fail the search. Only public
HTTP(S) destinations are fetched, with at most five pages downloaded
concurrently.

```python
with Search() as s:
    payload = s.text(
        "python programming",
        max_results=10,
        llm=True,
        llm_max_pages=8,
    )

for result in payload["results"]:
    print(result["rank"], result["title"], result["url"])
    print(result["content"])
```

The payload has a `schema_version`, the original `query`, and a `results` list.
Each result includes `rank`, `title`, `url`, `snippet`, `content`,
`content_status`, `sources`, and `metadata`. Results beyond `llm_max_pages`
have `content_status="not_fetched_limit"`. Without `llm=True`, the existing
list of result dictionaries is returned unchanged.

## Image Search

Find images.

```python
with Search() as s:
    results = s.images(
        query="landscapes",
        size="Wallpaper", # "Small", "Medium", "Large"
        color="Blue",
        max_results=10
    )
```

**Backends**: `duckduckgo`.

## Video Search

Find videos.

```python
with Search() as s:
    results = s.videos(
        query="tutorials",
        duration="medium", # "short", "long"
        max_results=10
    )
```

**Backends**: `duckduckgo`.

## News Search

Find news articles.

```python
with Search() as s:
    results = s.news("market trends", region="us-en")
```

**Backends**: `bing`, `duckduckgo`, `yahoo`.

## Proxies

Seekify supports HTTP and SOCKS5 proxies for routing requests. A proxy does not
guarantee avoiding provider rate limits; follow each provider's access policies.

When a provider responds with HTTP 429, Seekify raises
`RatelimitException`. If the response includes `Retry-After`, the exception's
`retry_after` attribute contains the recommended delay in seconds. Seekify does
not automatically retry a rate-limited request.

```python
from seekify import Search
from seekify.exceptions import RatelimitException

try:
    Search().text("python")
except RatelimitException as exc:
    if exc.retry_after is not None:
        print(f"Try again in {exc.retry_after:.0f} seconds")
    raise
```

```python
# SOCKS5 proxy (e.g., Tor)
s = Search(proxy="socks5h://127.0.0.1:9050")

# HTTP proxy
s = Search(proxy="http://user:pass@proxy_ip:port")
```
