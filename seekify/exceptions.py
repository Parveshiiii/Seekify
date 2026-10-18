"""Seekify exceptions."""

from collections.abc import Mapping
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional


class SearchException(Exception):
    """Base exception class for seekify."""


class RatelimitException(SearchException):
    """Raised for rate limit exceeded errors during API requests."""

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after

    @classmethod
    def from_response(cls, provider: str, headers: Mapping[str, str]) -> "RatelimitException":
        retry_after = parse_retry_after(
            next((value for key, value in headers.items() if key.lower() == "retry-after"), None),
        )
        message = f"{provider} rate limited the request (HTTP 429)"
        if retry_after is not None:
            message += f"; retry after {retry_after:.0f} seconds"
        return cls(message, retry_after=retry_after)


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse Retry-After as delay-seconds or an HTTP date."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


class TimeoutException(SearchException):
    """Raised for timeout errors during API requests."""
