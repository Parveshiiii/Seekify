<div align="center">
  <h1>Seekify</h1>

  <p><strong>Your Complete Toolkit for Search</strong></p>

  <p>
    Access diverse search engines, retrieve rich multimedia content, and bypass rate limits – all through one unified library.
  </p>

  <!-- Badges -->
  <p>
    <a href="https://pypi.org/project/seekify/"><img src="https://img.shields.io/pypi/v/seekify.svg?style=flat-square&logo=pypi&label=PyPI" alt="PyPI Version"></a>
    <a href="https://github.com/Parveshiiii/seekify/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Parveshiiii/seekify/ci.yml?branch=main&style=flat-square&logo=github&label=Tests" alt="Tests"></a>
    <a href="https://pypi.org/project/seekify/"><img src="https://img.shields.io/pypi/pyversions/seekify?style=flat-square&logo=python" alt="Python Version"></a>
    <a href="https://github.com/Parveshiiii/seekify/blob/main/LICENSE.md"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
  </p>
</div>

<hr/>

## 📋 Table of Contents

- [🌟 Features](#-features)
- [⚙️ Installation](#️-installation)
- [🚀 Quick Start](#-quick-start)
- [🖥️ Command Line Interface](#️-command-line-interface)
- [🌐 Supported Engines](#-supported-engines)
- [🛡️ Proxy Support](#️-proxy-support)
- [📚 Documentation](#-documentation)

<hr/>

> [!NOTE]
> 1. Seekify supports over 9 major search engines including: Google, Bing, DuckDuckGo, Brave, Yahoo, Yandex, Mojeek, Grokipedia, and Wikipedia. All providers follow similar usage patterns with consistent interfaces.
> 2. Search-IT name was not avilable in pypi so we rebranded it.
<hr/>

## 🌟 Features

<details open>
<summary><b>Unified Search API</b></summary>
<p>

- **Text Search:** Aggregated results from Google, Bing, DuckDuckGo, Yahoo, Yandex, and more.
- **Rich Media:** Retrieve images, videos, news, and books through dedicated endpoints.
- **Consistent Format:** All results differ in source but share a common, easy-to-parse structure.
</p>
</details>

<details open>
<summary><b>Advanced Capabilities</b></summary>
<p>

- **Zero Config:** No API keys required. It just works.
- **Proxy Support:** Fully compatible with HTTP and SOCKS5 proxies to manage identity and avoid rate limits.
- **Data Science Ready:** Returns data structures that easily convert to Pandas DataFrames for analysis.
- **Robust CLI:** Powerful command-line tools for quick lookups, downloads, and data exports.
</p>
</details>

<hr/>

## ⚙️ Installation

Seekify supports multiple installation methods to fit your workflow:

### 📦 Standard Installation

```bash
# Install from PyPI
pip install -U seekify

# Install with valid HTTPS/HTTP2 support
pip install -U "seekify[http2]"
```

### ⚡ UV Package Manager (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager. Seekify has full UV support:

```bash
# Install UV first (if not already installed)
pip install uv

# Install Seekify with UV
uv add seekify
```

<hr/>

## 🚀 Quick Start

### Python Script

Seekify is designed to be intuitive. Here is how to perform a simple text search:

```python
from seekify import Search

with Search() as s:
    results = s.text("python programming", max_results=5)
    for r in results:
        print(f"{r['title']} - {r['href']}")
```

### Jupyter Notebook

You can easily collect data into a Pandas DataFrame for analysis:

```python
from seekify import Search
import pandas as pd

# Search and create a DataFrame
with Search() as s:
    results = s.text("artificial intelligence trends", backend="duckduckgo", max_results=20)

df = pd.DataFrame(results)
display(df)
```

<hr/>

## 🖥️ Command Line Interface

Seekify includes a powerful CLI for quick queries and data export.

### 🚀 Direct Commands

```bash
# Text Search
seekify text -q "OpenAI" -m 10

# Image Search & Download
seekify images -q "minimalist wallpaper" -m 5 --download --download-directory ./wallpapers

# News Search (Export to JSON)
seekify news -q "tech industry" -m 20 --output news_data.json
```

### 📦 Python Module Execution

```bash
python -m seekify.cli text -q "search query"
```

<hr/>

## 🌐 Supported Engines

The library supports a wide range of backends tailored to specific search types:

<div align="center">

| Search Type | Supported Engines |
|-------------|-------------------|
| **Text**    | Bing, Brave, DuckDuckGo, Google, Grokipedia, Mojeek, Yahoo, Yandex, Wikipedia |
| **Images**  | DuckDuckGo |
| **Videos**  | DuckDuckGo |
| **News**    | Bing, DuckDuckGo, Yahoo |
| **Books**   | Anna's Archive |

</div>

<hr/>

## 🛡️ Proxy Support

Avoid rate limits and IP bans by routing traffic through a proxy.

```python
from seekify import Search

# Using a SOCKS5 proxy (e.g., Tor)
s = Search(proxy="socks5h://127.0.0.1:9050")

# Using an authenticated HTTP proxy
s = Search(proxy="http://user:password@proxy_ip:port")

# Then use normal search methods
results = s.text("privacy tools")
```

<hr/>

## 📚 Documentation

For comprehensive usage guides and advanced configuration, please refer to the [docs](./docs) directory.

## 👏 Credits

- Based on the work of [deedy5/ddgs](https://github.com/deedy5/ddgs) (formerly Dux), which is no longer maintained. We have expanded upon this foundation with new engines, features, and modernized tooling.

<div align="center">
  <p>Made with ❤️ by the Seekify team</p>
</div>
