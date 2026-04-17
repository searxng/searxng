# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring

from collections import defaultdict
from unittest.mock import Mock

from searx.engines import (
    google_api,
    google_images_api,
    google_news_api,
    google_videos_api,
)
from searx.engines.google_api_providers import get_google_api_locale
from searx.exceptions import (
    SearxEngineAPIException,
    SearxEngineTooManyRequestsException,
)


def test_google_api_locale_uses_script_and_region():
    assert get_google_api_locale("zh-HK") == ("zh-Hant", "hk")
    assert get_google_api_locale("en-GB") == ("en", "gb")


def test_google_api_request_builds_serper_search_request():
    google_api.provider = "serper"
    google_api.api_key = "test-key"
    params = defaultdict(dict)
    params["headers"] = {}
    params["pageno"] = 2
    params["searxng_locale"] = "en-GB"
    params["time_range"] = "week"
    params["safesearch"] = 2

    google_api.request("python asyncio", params)

    assert params["method"] == "POST"
    assert params["url"] == "https://google.serper.dev/search"
    assert params["headers"]["X-API-KEY"] == "test-key"
    assert params["json"] == {
        "q": "python asyncio",
        "hl": "en",
        "gl": "gb",
        "page": 2,
        "tbs": "qdr:w",
        "safe": "active",
    }


def test_google_api_response_maps_serpbase_results_and_suggestions():
    google_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {
        "status": 0,
        "organic": [
            {
                "title": "Asyncio in Python",
                "link": "https://example.com/asyncio",
                "snippet": "Structured search result.",
                "icon": "https://example.com/favicon.ico",
            }
        ],
        "related_searches": ["python async await"],
    }

    results = google_api.response(response)

    assert len(results) == 2
    assert results[0]["title"] == "Asyncio in Python"
    assert results[0]["url"] == "https://example.com/asyncio"
    assert results[0]["thumbnail"] == "https://example.com/favicon.ico"
    assert results[1]["suggestion"] == "python async await"


def test_google_api_response_raises_on_serpbase_rate_limit():
    google_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {"status": 1029, "error": "rate limited"}

    try:
        google_api.response(response)
        assert False
    except SearxEngineTooManyRequestsException as exc:
        assert "rate limited" in str(exc)


def test_google_images_api_maps_serper_image_results():
    google_images_api.provider = "serper"
    response = Mock()
    response.json.return_value = {
        "images": [
            {
                "title": "Asyncio in Python",
                "imageUrl": "https://example.com/full.png",
                "thumbnailUrl": "https://example.com/thumb.png",
                "imageWidth": 800,
                "imageHeight": 600,
                "source": "Example",
                "link": "https://example.com/page",
            }
        ]
    }

    results = google_images_api.response(response)

    assert len(results) == 1
    assert results[0]["template"] == "images.html"
    assert results[0]["img_src"] == "https://example.com/full.png"
    assert results[0]["thumbnail_src"] == "https://example.com/thumb.png"
    assert results[0]["resolution"] == "800 x 600"


def test_google_images_api_falls_back_for_sparse_serpbase_results():
    google_images_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {
        "status": 0,
        "images": [
            {
                "title": "Asyncio in Python",
                "link": "https://example.com/page",
                "domain": "example.com",
            }
        ],
    }

    results = google_images_api.response(response)

    assert len(results) == 1
    assert results[0]["title"] == "Asyncio in Python"
    assert results[0]["url"] == "https://example.com/page"
    assert "template" not in results[0]


def test_google_news_api_maps_news_metadata():
    google_news_api.provider = "serper"
    response = Mock()
    response.json.return_value = {
        "news": [
            {
                "title": "Asyncio News",
                "link": "https://example.com/news",
                "snippet": "Latest async news.",
                "source": "Example News",
                "date": "Sep 27, 2025",
                "imageUrl": "https://example.com/news.png",
            }
        ]
    }

    results = google_news_api.response(response)

    assert len(results) == 1
    assert results[0]["author"] == "Example News"
    assert results[0]["publishedDate"].year == 2025
    assert results[0]["thumbnail"] == "https://example.com/news.png"


def test_google_videos_api_maps_embed_and_metadata():
    google_videos_api.provider = "serper"
    response = Mock()
    response.json.return_value = {
        "videos": [
            {
                "title": "Asyncio Video",
                "link": "https://www.youtube.com/watch?v=oAkLSJNr5zY",
                "snippet": "Video description.",
                "imageUrl": "https://example.com/video.png",
                "duration": "1:42:41",
                "channel": "Corey Schafer",
                "date": "Aug 20, 2025",
            }
        ]
    }

    results = google_videos_api.response(response)

    assert len(results) == 1
    assert results[0]["template"] == "videos.html"
    assert results[0]["length"] == "1:42:41"
    assert results[0]["author"] == "Corey Schafer"
    assert results[0]["publishedDate"].year == 2025
    assert (
        results[0]["iframe_src"] == "https://www.youtube-nocookie.com/embed/oAkLSJNr5zY"
    )


def test_google_videos_api_parses_sparse_serpbase_metadata():
    google_videos_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {
        "status": 0,
        "videos": [
            {
                "title": "OpenAI's New Era - YouTube",
                "link": "https://www.youtube.com/watch?v=jUiZg4LQgiY",
                "source": "Duration: 12:34 Posted: Feb 9 2026",
            },
            {
                "title": "OpenAI - YouTube",
                "link": "https://www.youtube.com/OpenAI",
                "source": "OpenAI on OpenAI How OpenAI uses its own technology.",
            },
        ],
    }

    results = google_videos_api.response(response)

    assert len(results) == 2
    assert results[0]["length"] == "12:34"
    assert results[0]["publishedDate"].year == 2026
    assert results[0]["content"] == ""
    assert (
        results[0]["thumbnail"]
        == "https://img.youtube.com/vi/jUiZg4LQgiY/hqdefault.jpg"
    )
    assert results[1]["author"] == ""
    assert "OpenAI uses its own technology" in results[1]["content"]


def test_google_videos_api_parses_serpbase_time_and_thumbnail_fallback():
    google_videos_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {
        "status": 0,
        "videos": [
            {
                "title": "AsyncIO Video",
                "link": "https://www.youtube.com/watch?v=q_yk3oV14hE",
                "source": "Duration: Posted: Aug 1 2025",
                "duration": "9 Minutes",
            },
            {
                "title": "Author Only Video",
                "link": "https://youtu.be/abc123xyz00",
                "source": "Corey Schafer",
                "time": "1 week ago",
            },
        ],
    }

    results = google_videos_api.response(response)

    assert len(results) == 2
    assert results[0]["length"] == "9 Minutes"
    assert results[0]["publishedDate"].year == 2025
    assert (
        results[0]["thumbnail"]
        == "https://img.youtube.com/vi/q_yk3oV14hE/hqdefault.jpg"
    )
    assert results[1]["author"] == "Corey Schafer"
    assert (
        results[1]["iframe_src"] == "https://www.youtube-nocookie.com/embed/abc123xyz00"
    )


def test_google_news_api_parses_sparse_serpbase_metadata():
    google_news_api.provider = "serpbase"
    response = Mock()
    response.json.return_value = {
        "status": 0,
        "news": [
            {
                "title": "Asyncio News",
                "link": "https://example.com/news",
                "source": "Example News Posted: Sep 27, 2025",
            }
        ],
    }

    results = google_news_api.response(response)

    assert len(results) == 1
    assert results[0]["author"] == "Example News"
    assert results[0]["publishedDate"].year == 2025
    assert results[0]["content"] == "Example News Posted: Sep 27, 2025"


def test_google_api_init_rejects_invalid_provider():
    google_api.provider = "invalid"
    google_api.api_key = "test-key"

    try:
        google_api.init({})
        assert False
    except SearxEngineAPIException as exc:
        assert "Unsupported Google API provider" in str(exc)
