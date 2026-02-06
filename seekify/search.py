"""Search class implementation."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor, wait
from math import ceil
from random import random, shuffle
from types import TracebackType
from typing import Any, ClassVar, Optional, Union, Type

from .base import BaseSearchEngine
from .engines import ENGINES
from .exceptions import SearchException, TimeoutException
from .results import ResultsAggregator
from .similarity import SimpleFilterRanker
from .utils import _expand_proxy_tb_alias

logger = logging.getLogger(__name__)


class Search:
    """Seekify - A metasearch library for simple and distributed search.

    A metasearch library that aggregates results from diverse web search services.

    Args:
        proxy: The proxy to use for the search. Defaults to None.
        timeout: The timeout for the search. Defaults to 5.
        verify: bool (True to verify, False to skip) or str path to a PEM file. Defaults to True.

    Attributes:
        threads: The number of threads to use for the search. Defaults to None (automatic).
        _executor: The ThreadPoolExecutor instance.

    Raises:
        SearchException: If an error occurs during the search.

    Example:
        >>> from seekify import Search
        >>> results = Search().search("python")

    """

    threads: ClassVar[Optional[int]] = None
    _executor: ClassVar[Optional[ThreadPoolExecutor]] = None

    def __init__(self, proxy: Optional[str] = None, timeout: Optional[int] = 5, *, verify: Union[bool, str] = True) -> None:
        self._proxy = _expand_proxy_tb_alias(proxy) or os.environ.get("SEEKIFY_PROXY")
        self._timeout = timeout
        self._verify = verify
        self._engines_cache: dict[
            type[BaseSearchEngine[Any]], BaseSearchEngine[Any]
        ] = {}  # dict[engine_class, engine_instance]

    def __enter__(self) -> "Search":
        """Enter the context manager and return the Search instance."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> None:
        """Exit the context manager."""

    @classmethod
    def get_executor(cls) -> ThreadPoolExecutor:
        """Get a ThreadPoolExecutor instance and cache it."""
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(max_workers=cls.threads, thread_name_prefix="Seekify")
        return cls._executor

    def _get_engines(
        self,
        category: str,
        backend: str,
    ) -> list[BaseSearchEngine[Any]]:
        """Retrieve a list of search engine instances for a given category and backend.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            backend: A single or comma-delimited backends. Defaults to "auto".

        Returns:
            A list of initialized search engine instances corresponding to the specified
            category and backend. Instances are cached for reuse.

        """
        if isinstance(backend, list):  # deprecated handling
            backend = ",".join(backend)
        backend_list = [x.strip() for x in backend.split(",")]
        
        # Get all available engine keys for the category
        engine_keys = list(ENGINES[category].keys())
        shuffle(engine_keys)

        # Determine which keys to use
        if "auto" in backend_list or "all" in backend_list:
            keys = engine_keys
            # For text search, prioritize Wikipedia/Grokipedia if we are falling back to auto/all?
            # Actually the original logic seemed to force them to the front.
            if category == "text":
                priority_keys = ["wikipedia", "grokipedia"]
                other_keys = [k for k in keys if k not in priority_keys]
                keys = priority_keys + other_keys
        else:
            keys = backend_list

        try:
            # Instantiate engines or retrieve from cache
            available_engines = []
            for key in keys:
                engine_class = ENGINES[category].get(key)
                if not engine_class:
                    raise KeyError(key)

                if engine_class in self._engines_cache:
                    available_engines.append(self._engines_cache[engine_class])
                else:
                    engine_instance = engine_class(
                        proxy=self._proxy, 
                        timeout=self._timeout, 
                        verify=self._verify
                    )
                    self._engines_cache[engine_class] = engine_instance
                    available_engines.append(engine_instance)

            # Sort engines by priority (higher priority first)
            available_engines.sort(key=lambda e: (e.priority, random), reverse=True)
            return available_engines
        except KeyError as ex:
            logger.warning(
                "%r - backend is not exist or disabled. Available: %s. Using 'auto'",
                ex,
                ", ".join(sorted(engine_keys)),
            )
            return self._get_engines(category, "auto")

    def _search(  # noqa: C901
        self,
        category: str,
        query: str,
        keywords: Optional[str] = None,  # deprecated
        *,
        region: str = "us-en",
        safesearch: str = "moderate",
        timelimit: Optional[str] = None,
        max_results: Optional[int] = 10,
        page: int = 1,
        backend: str = "auto",
        **kwargs: str,
    ) -> list[dict[str, Any]]:
        """Perform a search across engines in the given category.

        Args:
            category: The category of search engines (e.g., 'text', 'images', etc.).
            query: The search query.
            keywords: Deprecated alias for `query`.
            region: The region to use for the search (e.g., us-en, uk-en, ru-ru, etc.).
            safesearch: The safesearch setting (e.g., on, moderate, off).
            timelimit: The timelimit for the search (e.g., d, w, m, y) or custom date range.
            max_results: The maximum number of results to return. Defaults to 10.
            page: The page of results to return. Defaults to 1.
            backend: A single or comma-delimited backends. Defaults to "auto".
            **kwargs: Additional keyword arguments to pass to the search engines.

        Returns:
            A list of dictionaries containing the search results.

        """
        query = keywords or query
        if not query:
            msg = "query is mandatory."
            raise SearchException(msg)

        engines = self._get_engines(category, backend)
        # Unique providers to prevent duplicate queries to the same source (e.g. Bing)
        len_unique_providers = len({engine.provider for engine in engines})
        seen_providers: set[str] = set()

        # Perform search
        # Initialize results and executor
        results_aggregator: ResultsAggregator[set[str]] = ResultsAggregator({"href", "image", "url", "embed_url"})
        
        # Determine strict number of workers to prevent over-fetching
        max_workers = min(len_unique_providers, ceil(max_results / 10) + 1) if max_results else len_unique_providers
        
        executor = self.get_executor()
        futures, err = {}, None
        for i, engine in enumerate(engines, start=1):
            if engine.provider in seen_providers:
                continue
            future = executor.submit(
                engine.search,
                query,
                region=region,
                safesearch=safesearch,
                timelimit=timelimit,
                page=page,
                **kwargs,
            )
            futures[future] = engine

            if len(futures) >= max_workers or i >= max_workers:
                done, not_done = wait(futures, timeout=self._timeout, return_when="FIRST_EXCEPTION")
                for f, f_engine in futures.items():
                    if f in done:
                        try:
                            if r := f.result():
                                results_aggregator.extend(r)
                                seen_providers.add(f_engine.provider)
                        except Exception as ex:  # noqa: BLE001
                            err = ex
                            logger.info("Error in engine %s: %r", engine.name, ex)
                futures = {f: futures[f] for f in not_done}

            # Check if we have enough results to stop
            if max_results and len(results_aggregator) >= max_results:
                break

        results = results_aggregator.extract_dicts()
        # Rank results
        ranker = SimpleFilterRanker()
        results = ranker.rank(results, query)

        if results:
            return results[:max_results] if max_results else results

        if "timed out" in f"{err}":
            raise TimeoutException(err)
        raise SearchException(err or "No results found.")

    def text(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a text search."""
        return self._search("text", query, **kwargs)

    def images(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform an image search."""
        return self._search("images", query, **kwargs)

    def news(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a news search."""
        return self._search("news", query, **kwargs)

    def videos(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a video search."""
        return self._search("videos", query, **kwargs)

    def books(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Perform a book search."""
        return self._search("books", query, **kwargs)
