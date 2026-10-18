<div align="center">
  <h1>Seekify</h1>
  <p><strong>Web search and page context for LLM applications</strong></p>
  <p>Search the web, collect useful page text, and pass structured results to your own LLM workflow.</p>
  <p>
    <a href="https://pypi.org/project/seekify/"><img src="https://img.shields.io/pypi/v/seekify.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="https://github.com/Parveshiiii/seekify/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Parveshiiii/seekify/ci.yml?branch=main&style=flat-square&logo=github&label=Tests" alt="Tests"></a>
    <a href="https://pypi.org/project/seekify/"><img src="https://img.shields.io/pypi/pyversions/seekify?style=flat-square&logo=python" alt="Python Version"></a>
    <a href="https://github.com/Parveshiiii/seekify/blob/main/LICENSE.md"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
  </p>
  <img src="assets/banner.webp" alt="Seekify — web search and page context for LLM applications" width="100%">
</div>

## Why Seekify?

Seekify is a Python metasearch library for applications that need current web
results without integrating a paid search API. It searches supported public
search-engine pages and returns consistent Python data structures. No search
API key is required.

Use its optional LLM mode to retrieve ranked results and extract readable text
from up to five result pages in one call. Seekify prepares the search context;
it does not call an LLM or provide a model API.

> Search engines may rate-limit requests, change their pages, or restrict
> automated access. Availability and terms depend on each provider. Seekify
> cannot guarantee uninterrupted access.

## Features

- Search across multiple text-search backends through one API.
- Return structured results with titles, URLs, snippets, source engines, and
  extracted page text for LLM workflows.
- Search images, videos, news, and books through dedicated methods.
- Use a proxy when needed.
- Work with Python dictionaries that are easy to serialize or load into tools
  such as Pandas.

## Installation

```bash
pip install -U seekify
```

Or install with [uv](https://docs.astral.sh/uv/):

```bash
uv add seekify
```

## Quick start

### Search results

```python
from seekify import Search

with Search() as search:
    results = search.text("python programming", max_results=5)

for result in results:
    print(result["title"], result["href"])
```

By default, text search returns a list of dictionaries. Select a backend with
`backend="google"` or provide a comma-separated list such as
`backend="google,bing"`. The default, `backend="auto"`, selects available
backends automatically.

### Search with page content for LLMs

Set `llm=True` to get a structured payload with page text for up to five ranked
results by default. Set `llm_max_pages` to fetch more or fewer pages:

```python
from seekify import Search

with Search() as search:
    payload = search.text(
        "How do solar panels work?",
        max_results=10,
        llm=True,
        llm_max_pages=8,
    )

for result in payload["results"]:
    print(f"[{result['rank']}] {result['title']} — {result['url']}")
    print(result["content"])
```

The payload is JSON-serializable and follows this shape:

```json
{
  "schema_version": "1.0",
  "query": "How do solar panels work?",
  "results": [
    {
      "rank": 1,
      "title": "Solar panels explained",
      "url": "https://example.com/solar-panels",
      "snippet": "A short summary from the search engine...",
      "content": "Readable text extracted from the page...",
      "content_status": "ok",
      "sources": ["google", "bing"],
      "metadata": {}
    }
  ]
}
```

Page text is capped at 5,000 characters per page. `llm_max_pages` defaults to
`5`; set it to `0` to skip page fetching or to a higher non-negative integer to
fetch more ranked results (up to the number returned by the search). Results
past that limit have `content_status` set to `"not_fetched_limit"`. If a page
cannot be retrieved, its result reports `"error"` and may include
`content_error`; one failed page does not fail the search. Page fetching uses
HTTPX for HTTP requests and lxml to extract readable text from HTML. Only
public HTTP(S) destinations are fetched, redirects are checked, response data
is capped, and page downloads run with at most five concurrent workers.

The returned payload can be passed to your own model, retrieval, or
citation-generation code. Seekify does not summarize the pages or generate
LLM responses. Without `llm=True`, the existing list-of-dictionaries response
is unchanged. See the [user guide](docs/USER_GUIDE.md#llm-ready-results) for
the complete field descriptions.

## Other search types

```python
with Search() as search:
    images = search.images("mountain landscape", max_results=10)
    videos = search.videos("python tutorial", max_results=10)
    news = search.news("renewable energy", max_results=10)
    books = search.books("machine learning", max_results=10)
```

## Supported backends

| Search type | Backends |
|---|---|
| Text | Bing, Brave, DuckDuckGo, Google, Grokipedia, Mojeek, Yahoo, Yandex, Wikipedia |
| Images | DuckDuckGo |
| Videos | DuckDuckGo |
| News | Bing, DuckDuckGo, Yahoo |
| Books | Anna's Archive |

The engines available to you may vary as providers update their sites.

## Proxy support

Pass a proxy URL when creating `Search`:

```python
from seekify import Search

with Search(proxy="socks5h://127.0.0.1:9050") as search:
    results = search.text("privacy tools")
```

HTTP and SOCKS5 proxies are supported. See the
[user guide](docs/USER_GUIDE.md) for more configuration options.
Providers may still rate-limit proxied requests. When a backend returns HTTP
429, Seekify raises `RatelimitException` and exposes any `Retry-After` delay
as `exc.retry_after`; it does not automatically retry that request.

## Command-line interface

```bash
# Search the web
seekify text -q "Python programming" -m 10

# Search news and save results as JSON
seekify news -q "renewable energy" -m 20 -o news.json

# Search images and download results
seekify images -q "mountain landscape" -m 5 --download --download-directory ./images
```

## Documentation

- [User guide](docs/USER_GUIDE.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Credits

Seekify builds on work from [deedy5/ddgs](https://github.com/deedy5/ddgs),
formerly known as Dux, and extends it with additional engines and features.
