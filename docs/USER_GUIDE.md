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

Seekify supports proxies to prevent rate limiting.

```python
# SOCKS5 proxy (e.g., Tor)
s = Search(proxy="socks5h://127.0.0.1:9050")

# HTTP proxy
s = Search(proxy="http://user:pass@proxy_ip:port")
```
