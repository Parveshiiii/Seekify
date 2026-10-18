import logging
import pytest
from seekify import Search
from seekify.exceptions import SearchException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Engines to test
TEXT_ENGINES = [
    "bing", "brave", "duckduckgo", "google", 
    "grokipedia", "mojeek", "yandex", "yahoo", "wikipedia"
]
IMAGE_ENGINES = ["duckduckgo"]
VIDEO_ENGINES = ["duckduckgo"]
NEWS_ENGINES = ["bing", "duckduckgo", "yahoo"]
BOOK_ENGINES = ["annasarchive"]


def _assert_provider_results(search, query, engine, fields):
    try:
        results = search(query, backend=engine, max_results=3)
    except SearchException as ex:
        pytest.skip(f"Provider {engine} unavailable: {ex}")

    assert results is not None
    if not results:
        pytest.skip(f"Provider {engine} returned no results")

    for field in fields:
        assert field in results[0]


def test_provider_assertions_are_not_swallowed():
    with pytest.raises(AssertionError):
        _assert_provider_results(lambda *_args, **_kwargs: [{"title": "missing URL"}], "query", "stub", ("href",))


@pytest.mark.parametrize("engine", TEXT_ENGINES)
def test_text_search(engine):
    logger.info(f"Testing text search with backend: {engine}")
    with Search() as s:
        _assert_provider_results(s.text, "python programming", engine, ("title", "href"))

@pytest.mark.parametrize("engine", IMAGE_ENGINES)
def test_image_search(engine):
    logger.info(f"Testing image search with backend: {engine}")
    with Search() as s:
        _assert_provider_results(s.images, "cute cat", engine, ("image",))

@pytest.mark.parametrize("engine", VIDEO_ENGINES)
def test_video_search(engine):
    logger.info(f"Testing video search with backend: {engine}")
    with Search() as s:
        _assert_provider_results(s.videos, "python tutorial", engine, ("content",))

@pytest.mark.parametrize("engine", NEWS_ENGINES)
def test_news_search(engine):
    logger.info(f"Testing news search with backend: {engine}")
    with Search() as s:
        _assert_provider_results(s.news, "technology", engine, ("title",))

@pytest.mark.parametrize("engine", BOOK_ENGINES)
def test_book_search(engine):
    logger.info(f"Testing book search with backend: {engine}")
    with Search() as s:
        _assert_provider_results(s.books, "python", engine, ("title",))
