"""Safe extraction of readable text from web pages."""

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx
from lxml import etree, html

_REDIRECT_STATUSES = {301, 302, 303, 307, 308}
_MAX_REDIRECTS = 3
_MAX_PAGE_BYTES = 1_000_000
_MAX_CONTENT_CHARS = 5_000
_REMOVED_ELEMENTS = "//script|//style|//noscript|//svg|//nav|//footer|//header|//aside|//form"


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only public HTTP(S) page URLs can be fetched")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise ValueError("Page URL resolves to a non-public address")


def fetch_page_text(client: httpx.Client, url: str) -> tuple[str, bool]:
    """Fetch a public HTML page and return cleaned text and whether it was truncated."""
    for redirect_count in range(_MAX_REDIRECTS + 1):
        _validate_public_url(url)
        with client.stream("GET", url, follow_redirects=False) as response:
            if response.status_code in _REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location or redirect_count == _MAX_REDIRECTS:
                    response.raise_for_status()
                    raise ValueError("Page redirected too many times")
                url = urljoin(url, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise ValueError("Page response is not HTML")

            page_bytes = bytearray()
            truncated = False
            for chunk in response.iter_bytes():
                remaining = _MAX_PAGE_BYTES - len(page_bytes)
                if len(chunk) > remaining:
                    page_bytes.extend(chunk[:remaining])
                    truncated = True
                    break
                page_bytes.extend(chunk)

            page = html.fromstring(bytes(page_bytes), parser=html.HTMLParser(recover=True))
            for element in page.xpath(_REMOVED_ELEMENTS):
                parent = element.getparent()
                if parent is not None:
                    parent.remove(element)
            text = " ".join(" ".join(page.itertext()).split())
            if len(text) > _MAX_CONTENT_CHARS:
                text = text[:_MAX_CONTENT_CHARS]
                truncated = True
            return text, truncated

    raise ValueError("Page redirected too many times")
