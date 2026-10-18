"""HTTP client."""

import logging
import socket
from time import sleep
from typing import Any, Final, Optional, Union

import primp

from .exceptions import RatelimitException, SearchException, TimeoutException

logger = logging.getLogger(__name__)


class Response:
    """HTTP response."""

    __slots__ = ("content", "headers", "status_code", "text")

    def __init__(
        self,
        status_code: int,
        content: bytes,
        text: str,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.content = content
        self.text = text
        self.headers = headers or {}


class Client:
    """HTTP client."""

    _max_attempts: Final = 3
    _retry_delay: Final = 0.5

    def __init__(self, proxy: Optional[str] = None, timeout: Optional[int] = 10, *, verify: Union[bool, str] = True) -> None:
        """Initialize the Client object.

        Args:
            proxy (str, optional): proxy for the HTTP client, supports http/https/socks5 protocols.
                example: "http://user:pass@example.com:3128". Defaults to None.
            timeout (int, optional): Timeout value for the HTTP client. Defaults to 10.
            verify: (Union[bool, str]):  True to verify, False to skip, or a str path to a PEM file. Defaults to True.

        """
        self.client = primp.Client(
            proxy=proxy,
            timeout=timeout,
            impersonate="random",
            impersonate_os="random",
            verify=verify if isinstance(verify, bool) else True,
            ca_cert_file=verify if isinstance(verify, str) else None,
        )

    def request(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a request, retrying transient connection failures up to three times."""
        for attempt in range(1, self._max_attempts + 1):
            try:
                resp = self.client.request(*args, **kwargs)
                headers = {str(key): str(value) for key, value in resp.headers.items()}
                if resp.status_code == 429:
                    raise RatelimitException.from_response("HTTP provider", headers)
                return Response(
                    status_code=resp.status_code,
                    content=resp.content,
                    text=resp.text,
                    headers=headers,
                )
            except RatelimitException:
                raise
            except Exception as ex:
                message = str(ex).lower()
                exception_name = type(ex).__name__.lower()
                is_timeout = isinstance(ex, (TimeoutError, socket.timeout)) or (
                    "timeout" in exception_name or "timed out" in message
                )
                is_connection_error = isinstance(ex, (ConnectionError, socket.gaierror)) or any(
                    marker in message
                    for marker in (
                        "connection",
                        "connect",
                        "dns error",
                        "network is unreachable",
                        "temporary failure in name resolution",
                        "name or service not known",
                    )
                )

                if attempt < self._max_attempts and (is_timeout or is_connection_error):
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    logger.info(
                        "Transient request failure (%s); retrying in %.1f seconds (%d/%d)",
                        type(ex).__name__,
                        delay,
                        attempt,
                        self._max_attempts - 1,
                    )
                    sleep(delay)
                    continue

                if is_timeout:
                    msg = f"Request timed out after {attempt} attempt(s): {ex!r}"
                    raise TimeoutException(msg) from ex
                msg = f"{type(ex).__name__}: {ex!r}"
                raise SearchException(msg) from ex

        raise AssertionError("Request retry loop exited unexpectedly")

    def get(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a GET request to the HTTP client."""
        return self.request(*args, method="GET", **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:  # noqa: ANN401
        """Make a POST request to the HTTP client."""
        return self.request(*args, method="POST", **kwargs)
