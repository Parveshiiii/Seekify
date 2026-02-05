"""Searchit exceptions."""


class SearchException(Exception):
    """Base exception class for searchit."""


class RatelimitException(SearchException):
    """Raised for rate limit exceeded errors during API requests."""


class TimeoutException(SearchException):
    """Raised for timeout errors during API requests."""
