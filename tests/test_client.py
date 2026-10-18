import socket
from types import SimpleNamespace

import pytest

from seekify.client import Client
from seekify.exceptions import RatelimitException, SearchException, TimeoutException


@pytest.fixture
def client(monkeypatch):
    instance = Client.__new__(Client)
    instance.client = SimpleNamespace()
    monkeypatch.setattr("seekify.client.sleep", lambda _delay: None)
    return instance


def test_client_initializes_with_random_impersonation():
    instance = Client()

    assert instance.client is not None


def test_request_retries_timeout_then_returns_response(client, monkeypatch):
    attempts = 0

    def request(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise socket.timeout("timed out")
        return SimpleNamespace(status_code=200, content=b"ok", text="ok", headers={"x-test": "value"})

    monkeypatch.setattr(client, "client", SimpleNamespace(request=request))

    response = client.request("GET", "https://example.com")

    assert attempts == 3
    assert response.status_code == 200
    assert response.text == "ok"
    assert response.headers == {"x-test": "value"}


def test_request_retries_connection_error_then_returns_response(client, monkeypatch):
    attempts = 0

    def request(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("connection reset")
        return SimpleNamespace(status_code=200, content=b"ok", text="ok", headers={})

    monkeypatch.setattr(client, "client", SimpleNamespace(request=request))

    response = client.request("GET", "https://example.com")

    assert attempts == 2
    assert response.text == "ok"


def test_request_raises_timeout_after_retry_limit(client, monkeypatch):
    attempts = 0

    def request(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise socket.timeout("timed out")

    monkeypatch.setattr(client, "client", SimpleNamespace(request=request))

    with pytest.raises(TimeoutException, match="after 3 attempt\\(s\\)") as error:
        client.request("GET", "https://example.com")

    assert attempts == 3
    assert isinstance(error.value.__cause__, socket.timeout)


def test_request_does_not_retry_non_connection_error(client, monkeypatch):
    attempts = 0

    def request(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        raise ValueError("invalid request")

    monkeypatch.setattr(client, "client", SimpleNamespace(request=request))

    with pytest.raises(SearchException, match="ValueError"):
        client.request("GET", "https://example.com")

    assert attempts == 1


def test_request_raises_rate_limit_with_retry_after(client, monkeypatch):
    monkeypatch.setattr(
        client,
        "client",
        SimpleNamespace(
            request=lambda *_args, **_kwargs: SimpleNamespace(
                status_code=429,
                content=b"",
                text="",
                headers={"Retry-After": "25"},
            )
        ),
    )

    with pytest.raises(RatelimitException) as error:
        client.request("GET", "https://example.com")

    assert error.value.retry_after == 25
