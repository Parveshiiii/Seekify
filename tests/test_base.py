from types import SimpleNamespace

import pytest

from seekify.base import BaseSearchEngine
from seekify.exceptions import RatelimitException, parse_retry_after


class StubSearchEngine(BaseSearchEngine):
    name = "stub"
    category = "text"
    provider = "stub"
    search_url = "https://example.com"
    search_method = "GET"
    items_xpath = "//div"
    elements_xpath = {}
    elements_replace = {}

    def build_payload(self, *args, **kwargs):
        return {}


def test_engine_request_raises_rate_limit_with_retry_after():
    engine = StubSearchEngine.__new__(StubSearchEngine)
    engine.client = SimpleNamespace(
        request=lambda *_args, **_kwargs: SimpleNamespace(
            status_code=429,
            headers={"Retry-After": "12"},
            text="",
        )
    )

    with pytest.raises(RatelimitException, match="HTTP 429") as error:
        engine.request("GET", "https://example.com")

    assert error.value.retry_after == 12


def test_parse_retry_after_accepts_http_date():
    retry_at = "Wed, 21 Oct 2037 07:28:00 GMT"

    delay = parse_retry_after(retry_at)

    assert delay is not None
    assert delay > 0


def test_parse_retry_after_invalid_value_returns_none():
    assert parse_retry_after("later") is None


def test_rate_limit_exception_keeps_message_constructor_compatibility():
    error = RatelimitException("custom rate limit")

    assert str(error) == "custom rate limit"
    assert error.retry_after is None
