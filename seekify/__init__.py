"""Seekify - A metasearch library for simple and distributed search.

A metasearch library that aggregates results from diverse web search services.
"""

import importlib
import logging
import threading
from typing import TYPE_CHECKING, Any, cast, Optional, Type

__version__ = "1.0.1"
__all__ = ("Search",)


if TYPE_CHECKING:
    from .search import Search

# A do-nothing logging handler
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger("ddgs").addHandler(logging.NullHandler())


class _ProxyMeta(type):
    _lock: threading.Lock = threading.Lock()
    _real_cls: Optional[Type["Search"]] = None

    @classmethod
    def _load_real(cls) -> Type["Search"]:
        if cls._real_cls is None:
            with cls._lock:
                if cls._real_cls is None:
                    cls._real_cls = importlib.import_module(".search", package=__name__).Search
                    globals()["Search"] = cls._real_cls
        return cls._real_cls

    def __call__(cls, *args: Any, **kwargs: Any) -> "Search":  
        real = type(cls)._load_real()
        return real(*args, **kwargs)

    def __getattr__(cls, name: str) -> Any:  
        return getattr(type(cls)._load_real(), name)

    def __dir__(cls) -> list[str]:
        base = set(super().__dir__())
        loaded_names = set(dir(type(cls)._load_real()))
        return sorted(base | (loaded_names - base))


class _SearchProxy(metaclass=_ProxyMeta):
    """Proxy class for lazy-loading the real Search implementation."""


Search: type[Search] = cast("type[Search]", _SearchProxy)  # type: ignore[no-redef]
